#!/usr/bin/env python3
"""Trace every logical block of a frozen prompt through a completed NIXL arm."""

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

from lifecycle_paired_timeline import (
    LAYOUTS,
    MODES,
    TOPOLOGIES,
    elapsed_ms,
    load_pair,
    table,
)


def prompt_text(path, manifest, manifest_hash, prompt, layout):
    conversation = manifest["conversation_id"]
    prompt_name = f"prompts/{conversation}.jsonl"
    manifest_name = f"manifests/{conversation}.json"
    with ZipFile(path) as bundle:
        checksums = {}
        for line in bundle.read("SHA256SUMS").decode().splitlines():
            digest, name = line.split("  ", 1)
            checksums[name] = digest
        if (sha256(bundle.read(manifest_name)).hexdigest() != manifest_hash
                or checksums[manifest_name] != manifest_hash):
            raise ValueError("Prompt bundle manifest does not match the trace archive")
        raw = bundle.read(prompt_name)
        if sha256(raw).hexdigest() != checksums[prompt_name]:
            raise ValueError("Prompt text file failed its SHA-256 check")
    rows = [row for row in map(json.loads, raw.splitlines())
            if row["layout"] == layout and row["turn"] == prompt["turn"]]
    if (len(rows) != 1 or rows[0]["request_key"] != prompt["request_key"]
            or rows[0]["prompt_sha256"] != prompt["prompt_sha256"]
            or rows[0]["prompt_tokens"] != len(prompt["token_ids"])
            or not isinstance(rows[0]["prompt_text"], str)):
        raise ValueError("Prompt text receipt does not match the selected turn")
    return rows[0]["prompt_text"]


def slot_label(block, valid, block_size):
    first = block["block_id"] * block_size
    return f"{block['block_id']}/{block['generation']} · `[{first}, {first + valid})`"


def lmcache_objects(arm, prompts, token_ids, block_size, chunk_size):
    requests = {}
    for turn, timing, prompt in zip(arm["turns"], arm["timeline"], prompts, strict=True):
        requests[turn["p_request_id"]] = (turn["turn"], "p0", timing["p_table"], prompt["token_ids"])
        requests[turn["d_request_id"]] = (turn["turn"], turn["decode_worker"],
                                          timing["d_table"], prompt["token_ids"])
    objects = {}
    trace = arm["trace"]
    for store in trace.select("lmcache_store_completed", success=True):
        turn, worker, slots, source_ids = requests[store["request_id"]]
        for obj in store["objects"]:
            start, end = obj["token_start"], obj["token_end"]
            if end > len(token_ids) or source_ids[:end] != token_ids[:end]:
                continue
            source_slots = slots[start // block_size:end // block_size]
            block_ids = [slot["block_id"] for slot in source_slots]
            if (start % chunk_size or end - start != chunk_size or len(source_slots) != chunk_size // block_size
                    or obj["block_ids_by_group"]["0"] != block_ids):
                raise ValueError(f"LMCache object span differs from {worker}'s turn {turn} slot table")
            key = (store["worker"], obj["object_id"])
            entry = objects.setdefault(key, {"span": (start, end), "events": []})
            if entry["span"] != (start, end):
                raise ValueError(f"LMCache object {obj['object_id']} appears at multiple prompt positions")
            block_generations = ", ".join(f"{slot['block_id']}/{slot['generation']}" for slot in source_slots)
            entry["events"].append((store["ts_ns"], worker, f"Turn {turn} GPU → LMCache · {obj['bytes']:,} B · "
                                    f"pool `{source_slots[0]['pool_id']}` · block/gen `{block_generations}`"))

    labels = {
        "lmcache_l1_resident": "CPU placement",
        "lmcache_l1_evicted": "CPU release",
        "lmcache_disk_write_completed": "Disk write complete",
        "lmcache_disk_read_completed": "Disk read complete",
    }
    for event, label in labels.items():
        for row in trace.select(event):
            key = (row["worker"], row["object_id"])
            if key in objects:
                detail = f"{label} · {row['bytes']:,} B"
                if "reason" in row:
                    detail += f" · {row['reason']}"
                objects[key]["events"].append((row["ts_ns"], row["worker"], detail))
    # Keep object labels in prompt order, then group replicas by server.
    return sorted(objects.items(), key=lambda pair: (pair[1]["span"], pair[0]))


def render(manifest, manifest_hash, arm, mode, layout, topology, turn_number, prompts_zip):
    prompts = manifest["layouts"][layout]
    matches = [(row, timing, prompt) for row, timing, prompt in zip(arm["turns"], arm["timeline"], prompts, strict=True)
               if row["turn"] == turn_number]
    if len(matches) != 1:
        raise ValueError(f"Turn {turn_number} is absent from the selected phase")
    turn, timing, prompt = matches[0]
    ids = prompt["token_ids"]
    block_size, chunk_size = manifest["block_size"], manifest["chunk_size"]
    unused = timing["blocks"] * block_size - len(ids)
    full, tail = divmod(len(ids), chunk_size)
    p_local, d_local = turn["p_gpu_prefix_tokens"], turn["d_gpu_prefix_tokens"]
    decoder = turn["decode_worker"]
    zero = timing["zero"]

    lines = [f"# Prompt timeline for turn {turn_number} · {topology}", "",
             f"MT-RAG CLAPNQ `{manifest['conversation_id']}` · {mode} · {layout} · decoder `{decoder}`.", "",
             "[Request timeline](#request-timeline) · [Block map](#token-ids-and-physical-block-movement) · "
             "[LMCache events](#lmcache-copies-and-storage-events)", "",
             "## Prompt", "", f"Request `{prompt['request_key']}` · token SHA-256 `{prompt['prompt_sha256']}`.", ""]
    if prompts_zip is not None:
        text = prompt_text(prompts_zip, manifest, manifest_hash, prompt, layout)
        fence = "`" * max(3, 1 + max(map(len, re.findall(r"`+", text)), default=0))
        lines.extend(("<details>", "<summary>Read the exact prompt text</summary>", "",
                      f"{fence}text", text, fence, "", "</details>", ""))
    else:
        lines.extend(("The trace archive contains the exact token IDs. Use the replication ZIP to display prompt text.", ""))
    lines.extend((f"**{len(ids):,} tokens** occupy **{timing['blocks']:,} logical GPU blocks** with "
                  f"{unused} unused prompt slots at the end. The prompt fits {full} complete {chunk_size}-token "
                  f"LMCache objects and a {tail}-token tail.", "",
                  f"P reused **{p_local:,}** prompt tokens on GPU and computed **{len(ids) - p_local:,}**. "
                  f"{decoder} reused **{d_local:,}** on GPU and pulled **{turn['d_prefix_loaded_tokens']:,}** "
                  f"over NIXL in **{len(turn['blocks']):,} blocks** ({turn['nixl_transferred_bytes']:,} B).", "",
                  "## Request timeline", "",
                  "Times are milliseconds from P scheduler arrival. NIXL readiness covers the request's transfer batch.", ""))
    p_write, dispatch, d_arrival, d_lookup, ready, final_write, release = timing["stamps"]
    milestones = [
        (zero, "p0", "Prompt arrived"),
        (timing["p_lookup"]["ts_ns"], "p0", f"GPU prefix lookup · {p_local:,} local tokens"),
        (p_write, "p0", "Last prompt KV write completed"),
        (dispatch, "Driver", f"Dispatched to {decoder}"),
        (d_arrival, decoder, "Prompt arrived"),
        (d_lookup, decoder, f"Prefix decision · {d_local:,} local · {turn['d_prefix_loaded_tokens']:,} NIXL tokens"),
        (ready, decoder, "NIXL batch ready on GPU"),
        (final_write, decoder, "Wrote final prompt token for logits"),
        (release, decoder, "Released request's block references"),
    ]
    for worker, request in (("p0", turn["p_request_id"]), (decoder, turn["d_request_id"])):
        for store in arm["trace"].select("lmcache_store_completed", request_id=request, success=True):
            milestones.append((store["ts_ns"], worker,
                               f"GPU → {store['worker']} · {len(store['objects'])} objects · {store['bytes']:,} B"))
    lines.extend((table(("Elapsed (ms)", "Actor", "Event"),
                        ((elapsed_ms(ns, zero), actor, label) for ns, actor, label in sorted(milestones))), "",
                  "## Token IDs and physical block movement", "",
                  "Logical blocks are zero-based and stay tied to prompt positions. Physical block IDs are local to "
                  "each worker. Each slot cell shows block ID/generation and valid GPU token slots. "
                  f"P pool `{timing['p_table'][0]['pool_id']}` · {decoder} pool `{timing['d_table'][0]['pool_id']}`. "
                  "The request timeline gives NIXL readiness for all rows marked NIXL. LMCache links identify "
                  "whole objects for the same prompt prefix. Their event lists show which worker "
                  "copied each object and any later CPU or disk activity.", ""))
    objects = lmcache_objects(arm, prompts, ids, block_size, chunk_size)
    links = defaultdict(list)
    for i, (_, obj) in enumerate(objects, 1):
        links[obj["span"][0]].append(f"[M{i:02}](#lmcache-object-m{i:02})")
    p_writes = defaultdict(list)
    for write in timing["p_writes"]:
        p_writes[write["token_start"] // block_size].append(write["ts_ns"])
    rows = []
    for logical, (p_slot, d_slot) in enumerate(zip(timing["p_table"], timing["d_table"], strict=True)):
        start = logical * block_size
        end = min(start + block_size, len(ids))
        p_source = "GPU prefix" if start < p_local else f"GPU write {elapsed_ms(max(p_writes[logical]), zero)} ms"
        d_source = "GPU prefix" if start < d_local else "NIXL"
        if end == len(ids):
            d_source += f" · final token written at {elapsed_ms(final_write, zero)} ms"
        lmcache = ", ".join(links[start // chunk_size * chunk_size]) or "—"
        rows.append((logical, f"`[{start}, {end})`", f"`{json.dumps(ids[start:end])}`",
                     slot_label(p_slot, end - start, block_size), p_source,
                     slot_label(d_slot, end - start, block_size), d_source, lmcache))
    lines.extend((table(("Logical block", "Prompt positions", "Exact token IDs", "P block/gen · slots", "P source",
                         f"{decoder} block/gen · slots", "D source", "LMCache objects"), rows), "",
                  "## LMCache copies and storage events", "",
                  "These events follow each `(server, object ID)` through the conversation. Negative times precede "
                  "the selected turn. GPU copies list the source block IDs and generations in prompt order. "
                  "A disk read records movement into CPU memory. The GPU source is shown in the block table.", ""))
    for i, ((server, object_id), obj) in enumerate(objects, 1):
        start, end = obj["span"]
        lines.extend((f"### LMCache object M{i:02}", "",
                      f"`{server}` · prompt positions `[{start}, {end})` · logical blocks "
                      f"`{start // block_size}–{end // block_size - 1}`.", "", f"`{object_id}`", "",
                      table(("Elapsed (ms)", "Actor", "Event"),
                            ((elapsed_ms(ns, zero), actor, detail) for ns, actor, detail in sorted(obj["events"]))), ""))
    return "\n".join(lines).rstrip("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", type=Path, help="extracted phase with manifest.json and both topology directories")
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--layout", choices=LAYOUTS, required=True)
    parser.add_argument("--topology", choices=TOPOLOGIES, required=True)
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--prompt-archive", type=Path, help="optional verified MT-RAG Run 3 replication ZIP")
    args = parser.parse_args()
    try:
        manifest, digest, arms, _, _ = load_pair(args.phase, mode=args.mode, layout=args.layout)
        print(render(manifest, digest, arms[args.topology], args.mode, args.layout,
                     args.topology, args.turn, args.prompt_archive))
    except (OSError, ValueError, KeyError, RuntimeError, BadZipFile) as error:
        parser.exit(1, f"Prompt timeline failed: {error}\n")


if __name__ == "__main__":
    main()
