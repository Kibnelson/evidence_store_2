#!/usr/bin/env python3
"""Freeze the paired NIXL CLAPNQ cohort for the 1, 5, and 10 conversation checkpoints."""

import argparse
import json
from pathlib import Path

from lifecycle_prepare import (
    CHUNK_SIZE,
    CONVERSATION,
    MAX_PROMPT_TOKENS,
    ROOT,
    WORKLOAD,
    load_tokenizer,
    read_selected_passages,
    read_selected_turns,
    render_fixture,
    sha256_file,
    write_fixture,
)


ADDITIONAL_WORKLOAD = ROOT / "workloads/mtrag-carried-docs-clapnq-scale-twenty.json"
CHECKPOINTS = (1, 5, 10)
PILOT_SHA256 = "7b1b9360bc5be717b50387e197c10db8d1255574aabea76380994dee7d24136f"
# This pilot's Qwen BF16 KV layout uses 36 MiB per 256-token object.
DISK_OBJECT_BYTES = 37_748_736


def campaign_selection():
    legacy = json.loads(WORKLOAD.read_text(encoding="utf-8"))
    additional = json.loads(ADDITIONAL_WORKLOAD.read_text(encoding="utf-8"))
    provenance = legacy["provenance"]
    if (additional["native_reference_run"], additional["native_reference_cohort"]) != (
        provenance["campaign"], provenance["cohort"]
    ):
        raise ValueError("The additional rankings come from a different frozen retrieval cohort")

    legacy_conversations = legacy["selection"]["conversations"]
    additions = additional["conversations"]
    extra_ranks = []
    for entry in additions:
        if entry["domain"] != "clapnq" or entry["turn_window"] != f"1:{entry['turns']}":
            raise ValueError(f"Expected a complete CLAPNQ conversation for {entry['conversation_id']}")
        extra_ranks.extend(entry["native_retrieval_reference"])

    workloads = {
        path: sha256_file(path) for path in (WORKLOAD, ADDITIONAL_WORKLOAD)
    }
    sources = {}
    for path, entries in ((WORKLOAD, legacy_conversations), (ADDITIONAL_WORKLOAD, additions)):
        for entry in entries:
            conversation = entry["conversation_id"]
            if conversation in sources:
                raise ValueError(f"Duplicate conversation in frozen rankings: {conversation}")
            sources[conversation] = path
    if sources.get(CONVERSATION) != WORKLOAD:
        raise ValueError("The reference pilot is absent from the original frozen workload")
    candidates = [CONVERSATION, *(value for value in sources if value != CONVERSATION)]
    selection = {
        "provenance": provenance,
        "selection": {
            "conversations": legacy_conversations + additions,
            "per_request": legacy["selection"]["per_request"] + extra_ranks,
        },
    }
    return candidates, selection, sources, workloads


def select_fixtures(source, tokenizer_path):
    candidates, selection, sources, workloads = campaign_selection()
    provenance = selection["provenance"]
    tokenizer, tokenizer_digest = load_tokenizer(provenance, tokenizer_path)
    turns = {conversation: read_selected_turns(source, selection, conversation) for conversation in candidates}
    all_turns = [turn for rows in turns.values() for turn in rows]
    if any(len(turn["evidence"]) != 6 for turn in all_turns):
        raise ValueError("The frozen cohort must have six ranked passages on every turn")
    passages = read_selected_passages(source, selection, all_turns)

    selected = []
    skipped = []
    for conversation in candidates:
        source_workload = sources[conversation]
        fixture = render_fixture(conversation, provenance, workloads[source_workload], turns[conversation],
                                 passages, tokenizer, tokenizer_digest, max_prompt_tokens=None)
        lengths = {layout: [len(row["token_ids"]) for row in rows] for layout, rows in fixture["layouts"].items()}
        maxima = {layout: max(sizes) for layout, sizes in lengths.items()}
        if max(maxima.values()) > MAX_PROMPT_TOKENS:
            if conversation == CONVERSATION:
                raise ValueError("The reference pilot exceeds the prompt budget")
            skipped.append({"conversation_id": conversation, "max_prompt_tokens_by_layout": maxima})
            continue
        # Each turn can write a full copy per engine role, irrespective of reuse.
        disk_bounds = {layout: 2 * DISK_OBJECT_BYTES * sum(size // CHUNK_SIZE for size in sizes)
                       for layout, sizes in lengths.items()}
        selected.append((fixture, {
            "conversation_id": conversation,
            "turns": len(turns[conversation]),
            "max_prompt_tokens": max(maxima.values()),
            "max_prompt_tokens_by_layout": maxima,
            "prompt_tokens_by_layout": {layout: sum(sizes) for layout, sizes in lengths.items()},
            "disk_bytes_upper_bound": max(disk_bounds.values()),
            "disk_bytes_upper_bound_by_layout": disk_bounds,
            "ranking_workload": source_workload.relative_to(ROOT).as_posix(),
        }))
        if len(selected) == CHECKPOINTS[-1]:
            break
    if len(selected) != CHECKPOINTS[-1]:
        raise ValueError(f"The frozen workloads provide only {len(selected)} complete conversations within budget")
    return selected, skipped, workloads


def prepare(output, source, tokenizer_path):
    selected, skipped, workloads = select_fixtures(source, tokenizer_path)
    conversations = []
    for fixture, record in selected:
        manifest = Path("manifests") / f"{record['conversation_id']}.json"
        write_fixture(output / manifest, fixture)
        digest = sha256_file(output / manifest)
        if record["conversation_id"] == CONVERSATION and digest != PILOT_SHA256:
            raise ValueError(f"The first manifest differs from the archived pilot: {digest}")
        conversations.append({**record, "manifest_path": manifest.as_posix(), "manifest_sha256": digest})

    plan = output / "campaign.json"
    write_fixture(plan, {
        "schema_version": 1,
        "dataset": "mtrag",
        "domain": "clapnq",
        "modes": ["memory", "disk"],
        "layouts": ["chat", "carry_forward"],
        "topologies": ["per_engine", "shared_engine"],
        "checkpoints": list(CHECKPOINTS),
        "max_prompt_tokens": MAX_PROMPT_TOKENS,
        "selection_order": "Reference pilot, remaining original frozen rankings, then additional frozen rankings. "
                           "Omit complete conversations that exceed the token budget in either layout.",
        "workloads": {path.relative_to(ROOT).as_posix(): digest for path, digest in workloads.items()},
        "skipped_over_budget": skipped,
        "conversations": conversations,
    })
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="directory for campaign.json and frozen manifests")
    parser.add_argument("--mt-rag", type=Path, default=ROOT / "third_party/checkouts/mt-rag")
    parser.add_argument("--tokenizer-file", type=Path, help="use a local copy of the pinned tokenizer JSON")
    args = parser.parse_args()
    try:
        plan = prepare(args.output, args.mt_rag, args.tokenizer_file)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Campaign preparation failed: {error}\n")
    print(f"Frozen 10 paired conversations to {plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
