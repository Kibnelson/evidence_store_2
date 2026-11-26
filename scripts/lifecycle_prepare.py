#!/usr/bin/env python3
"""Freeze one CLAPNQ conversation for the paired KV lifecycle smoke."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
WORKLOAD = ROOT / "workloads/mtrag-multi-turn-repeat.json"
CONVERSATION = "1534a095279f2cb888fb0bea17bd70da"
BLOCK_SIZE = 16
CHUNK_SIZE = 256
NAMESPACE = "mtrag:clapnq"
IDENTITY_FIELDS = ("doc_id", "chunk_id", "chunk_version")


def sha256_file(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_selected_turns(source, manifest, conversation):
    tasks_path = source / "mtrag-human/generation_tasks/reference.jsonl"
    if sha256_file(tasks_path) != manifest["provenance"]["source_sha256"]:
        raise ValueError("MT-RAG reference tasks differ from the frozen workload")
    selected = next(
        (entry for entry in manifest["selection"]["conversations"]
         if entry["conversation_id"] == conversation),
        None,
    )
    if selected is None:
        raise ValueError(f"{conversation} is absent from the frozen workload")

    turns = {}
    with tasks_path.open(encoding="utf-8") as stream:
        for line in stream:
            task = json.loads(line)
            if task["conversation_id"] != conversation:
                continue
            if not task["Collection"].lower().startswith("mt-rag-clapnq-"):
                raise ValueError(f"{task['task_id']} is outside CLAPNQ")
            turn = int(task["turn"])
            request_key = f"mtrag:{task['task_id']}"
            expected_key = f"mtrag:{conversation}<::>{turn}"
            if request_key != expected_key or turn in turns:
                raise ValueError(f"Unexpected or duplicate turn {request_key}")
            messages = task["input"]
            roles = [message["speaker"] for message in messages]
            if (len(roles) != 2 * turn - 1
                    or any(role != "user" for role in roles[::2])
                    or any(role not in ("agent", "assistant") for role in roles[1::2])):
                raise ValueError(f"Expected complete reference Q&A for {request_key}")
            turns[turn] = {
                "turn": turn,
                "request_key": request_key,
                "messages": [{field: message[field] for field in ("speaker", "text")}
                             for message in messages],
            }
    if sorted(turns) != list(range(1, selected["turns"] + 1)):
        raise ValueError(f"Expected the complete conversation {conversation}")

    ranks = {}
    for entry in manifest["selection"]["per_request"]:
        key = entry["request_key"]
        if not key.startswith(f"mtrag:{conversation}<::>"):
            continue
        if key in ranks:
            raise ValueError(f"Duplicate frozen ranks for {key}")
        rows = sorted(entry["evidence"], key=lambda hit: hit["rank"])
        if not rows or [hit["rank"] for hit in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"Invalid evidence ranks for {key}")
        ranks[key] = [{field: hit[field] for field in ("rank", *IDENTITY_FIELDS)} for hit in rows]
    ordered = [turns[index] for index in sorted(turns)]
    if set(ranks) != {row["request_key"] for row in ordered}:
        raise ValueError("Frozen evidence and reference turns differ")
    for row in ordered:
        row["evidence"] = ranks[row["request_key"]]
    return ordered


def read_selected_passages(source, manifest, turns):
    archive_path = source / "corpora/passage_level/clapnq.jsonl.zip"
    if sha256_file(archive_path) != manifest["provenance"]["corpus_archive_sha256"]:
        raise ValueError("CLAPNQ passage archive differs from the frozen workload")
    selected = {}
    for row in turns:
        for hit in row["evidence"]:
            identity = tuple(hit[field] for field in IDENTITY_FIELDS)
            if selected.setdefault(hit["chunk_id"], identity) != identity:
                raise ValueError(f"Conflicting frozen versions of {hit['chunk_id']}")
    passages = {}
    with ZipFile(archive_path) as archive, archive.open("clapnq.jsonl") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            passage_id = row["_id"]
            document_id = re.sub(r"_\d+-\d+-\d+-\d+$", "", passage_id)
            # Use the same ID encoding as the V1 MT-RAG corpus normalizer.
            identity_source = json.dumps([document_id, passage_id], ensure_ascii=False,
                                         separators=(",", ":")) + "\n"
            chunk_id = f"{NAMESPACE}:chunk:{sha256(identity_source.encode()).hexdigest()}"
            if chunk_id not in selected:
                continue
            text = row["text"]
            doc_id = f"{NAMESPACE}:doc:{sha256(document_id.encode()).hexdigest()}"
            version = sha256(text.encode()).hexdigest()
            if (doc_id, chunk_id, version) != selected[chunk_id]:
                raise ValueError(f"Passage content or identity differs for {chunk_id}")
            passages[chunk_id] = text
    if set(passages) != set(selected):
        raise ValueError(f"Missing frozen CLAPNQ pages: {sorted(set(selected) - set(passages))}")
    return passages


def render_turn(known_turns, passages, tokenizer, carry_forward, max_prompt_tokens):
    current = known_turns[-1]
    messages = current["messages"]
    parts = ["Answer each question using the supplied evidence.\n\n"]
    evidence = []
    cursor = len(parts[0])

    for index, item in enumerate(known_turns):
        is_current = index + 1 == len(known_turns)
        if is_current or carry_forward:
            parts.append("Evidence:\n")
            cursor += len(parts[-1])
            for hit in item["evidence"]:
                parts.append(f"[Document {hit['rank']}]\n")
                cursor += len(parts[-1])
                text = passages[hit["chunk_id"]]
                evidence.append({
                    **hit,
                    "source_turn": item["turn"],
                    "current": is_current,
                    "start_char": cursor,
                    "end_char": cursor + len(text),
                })
                parts.extend((text, "\n[/Document]\n"))
                cursor += len(text) + len(parts[-1])
        parts.append(f"Question: {messages[2 * index]['text']}\nAnswer:")
        cursor += len(parts[-1])
        if not is_current:
            parts.append(f" {messages[2 * index + 1]['text']}\n\n")
            cursor += len(parts[-1])

    prompt = "".join(parts)
    encoded = tokenizer.encode(prompt, add_special_tokens=False)
    token_ids = encoded.ids
    if not 1 < len(token_ids) <= max_prompt_tokens:
        layout = "carry_forward" if carry_forward else "chat"
        raise ValueError(f"{layout} turn {current['turn']} has {len(token_ids)} tokens "
                         f"outside the prompt budget {max_prompt_tokens}")
    # Complete chunks strictly before the final token. The D connector can
    # replay the final token for logits. All remaining tokens stay in prompt.
    measured = (len(token_ids) - 1) // CHUNK_SIZE * CHUNK_SIZE
    if measured < CHUNK_SIZE:
        raise ValueError(f"{current['request_key']} has no complete measurable LMCache chunk")
    for hit in evidence:
        indices = [
            index for index, (start, end) in enumerate(encoded.offsets)
            if end > start and start < hit["end_char"] and end > hit["start_char"]
        ]
        if not indices:
            raise ValueError(f"No prompt tokens for {hit['chunk_id']}")
        hit["start_token"], hit["end_token"] = indices[0], indices[-1] + 1

    return {
        "turn": current["turn"],
        "request_key": current["request_key"],
        "token_ids": token_ids,
        "prompt_sha256": sha256(json.dumps(token_ids, separators=(",", ":")).encode("ascii")).hexdigest(),
        "measured_prefix_tokens": measured,
        "tail_tokens": len(token_ids) - measured,
        "evidence": evidence,
    }


def freeze(source, tokenizer_path, conversation, max_prompt_tokens):
    from tokenizers import Tokenizer

    manifest = json.loads(WORKLOAD.read_text(encoding="utf-8"))
    provenance = manifest["provenance"]
    model, revision = provenance["tokenizer_model"], provenance["tokenizer_revision"]
    if tokenizer_path is None:
        from huggingface_hub import hf_hub_download

        tokenizer_path = Path(hf_hub_download(model, "tokenizer.json", revision=revision))
    tokenizer_digest = sha256_file(tokenizer_path)
    if tokenizer_digest != provenance["tokenizer_asset_sha256"]:
        raise ValueError("Tokenizer asset differs from the frozen V1 model revision")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    turns = read_selected_turns(source, manifest, conversation)
    passages = read_selected_passages(source, manifest, turns)
    layouts = {
        layout: [render_turn(turns[:index + 1], passages, tokenizer,
                             carry_forward, max_prompt_tokens) for index in range(len(turns))]
        for layout, carry_forward in (("chat", False), ("carry_forward", True))
    }
    return {
        "schema_version": 1,
        "model": model,
        "model_revision": revision,
        "tokenizer_sha256": tokenizer_digest,
        "workload_sha256": sha256_file(WORKLOAD),
        "dataset": "mtrag",
        "domain": "clapnq",
        "conversation_id": conversation,
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "layouts": layouts,
    }


def write_fixture(output, contents):
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(contents, ensure_ascii=False, separators=(",", ":")) + "\n"
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(encoded)
            stream.close()
            try:
                output.hardlink_to(temporary)
            except FileExistsError:
                if output.read_text(encoding="utf-8") != encoded:
                    raise FileExistsError(f"Fixture already exists with different prompts: {output}") from None
        finally:
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mt-rag", type=Path, default=ROOT / "third_party/checkouts/mt-rag")
    parser.add_argument("--tokenizer-file", type=Path, help="use a local copy of the pinned tokenizer JSON")
    parser.add_argument("--conversation", default=CONVERSATION)
    parser.add_argument("--max-prompt-tokens", type=int, default=8191, help="leave space for generation")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        fixture = freeze(args.mt_rag, args.tokenizer_file, args.conversation, args.max_prompt_tokens)
        write_fixture(args.output, fixture)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Workload preparation failed: {error}\n")
    count = len(fixture["layouts"]["chat"])
    print(f"Frozen {count} matched turns per layout to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
