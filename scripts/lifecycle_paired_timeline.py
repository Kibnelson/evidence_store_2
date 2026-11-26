#!/usr/bin/env python3
"""Reconstruct a paired NIXL timeline from extracted trace artifacts."""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

from lifecycle_compare import matched_outputs
from lifecycle_receipts import Trace


TOPOLOGIES = ("per_engine", "shared_engine")
LAYOUT = "carry_forward"
LAYOUTS = ("chat", LAYOUT)
MODES = ("memory", "disk")
KV_FIELDS = (
    "p_gpu_prefix_tokens", "p_lmcache_prefix_tokens", "d_gpu_prefix_tokens", "d_prefix_loaded_tokens",
    "d_tail_computed_tokens", "nixl_transferred_bytes",
)
BLOCK_FIELDS = ("pool_id", "block_id", "generation")


def one_event(trace, event, worker, request):
    events = trace.select(event, worker=worker, request_id=request)
    if len(events) != 1:
        raise ValueError(f"Expected one {event} for {request}, found {len(events)}")
    return events[0]


def block_identity(row):
    return tuple(row[key] for key in BLOCK_FIELDS)


def check_published_hash(trace, block, p_slot, d_slot, d_worker, d_request):
    fields = {"group": block["group"], "token_start": block["token_start"], "partial": False,
              "block_hash": block["p_block"]["block_hash"]}
    if (not trace.select("vllm_gpu_block_cached", worker="p0", **fields, **p_slot)
            or not trace.select("vllm_gpu_block_cached", worker=d_worker, request_id=d_request,
                                **fields, **d_slot)):
        raise ValueError(f"No matching P and D prefix hash at token {block['token_start']} for {d_request}")


def prompt_identity(prompt, index):
    token_ids = prompt["token_ids"]
    token_hash = sha256(json.dumps(token_ids, separators=(",", ":")).encode("ascii")).hexdigest()
    if token_hash != prompt["prompt_sha256"]:
        raise ValueError(f"Manifest token hash differs at turn {prompt['turn']}")
    return (prompt["turn"], prompt["request_key"], token_hash, len(token_ids), f"d{index % 3}")


def check_prompt_writes(rows, table, first, limit, block_size, request):
    positions = set()
    for row in rows:
        start, end = row["token_start"], row["token_end"]
        if start >= limit:
            continue
        logical, offset = divmod(start, block_size)
        if (start < first or row["group"] != 0 or row["block_size"] != block_size
                or row["block_id"] != table[logical]["block_id"]
                or row["slot_start"] != row["block_id"] * block_size + offset
                or row["slot_end"] - row["slot_start"] != end - start
                or offset + end - start > block_size):
            raise ValueError(f"Recorded GPU write differs from the slot table for {request}")
        positions.update(range(start, min(end, limit)))
    if positions != set(range(first, limit)):
        raise ValueError(f"GPU write coverage differs for {request}")


def turn_timeline(trace, turn, block_size):
    p_req, d_req, d_worker = turn["p_request_id"], turn["d_request_id"], turn["decode_worker"]
    total = turn["prompt_tokens"]
    blocks = (total + block_size - 1) // block_size
    p_arrival = one_event(trace, "vllm_request_arrived", "p0", p_req)
    d_arrival = one_event(trace, "vllm_request_arrived", d_worker, d_req)
    p_lookup = one_event(trace, "vllm_prefix_lookup", "p0", p_req)
    d_lookup = one_event(trace, "vllm_prefix_lookup", d_worker, d_req)
    ready = one_event(trace, "vllm_external_kv_ready", d_worker, d_req)
    release = one_event(trace, "vllm_request_blocks_release", d_worker, d_req)
    p_local, d_local = p_lookup["local_tokens"], d_lookup["local_tokens"]
    remote = d_lookup["external_tokens"]
    if (p_arrival["prompt_tokens"] != total or d_arrival["prompt_tokens"] != total
            or p_local != turn["p_gpu_prefix_tokens"] or p_lookup["external_tokens"] != 0
            or turn["p_lmcache_prefix_tokens"] != 0 or d_local != turn["d_gpu_prefix_tokens"]
            or remote != turn["d_prefix_loaded_tokens"] or d_local + remote != total
            or p_local % block_size or d_local % block_size or not ready["success"]
            or ready["computed_tokens"] != total or ready["ts_ns"] != turn["d_kv_ready_ns"]):
        raise ValueError(f"Prompt and KV coverage differ from trace for {d_req}")

    p_plan = max(trace.select("vllm_gpu_work_planned", worker="p0", request_id=p_req),
                 key=lambda row: row["ts_ns"])
    if any(len(event["blocks"]) != 1 for event in (p_plan, ready)):
        raise ValueError(f"Expected one KV group for {d_req}")
    p_table, d_table = p_plan["blocks"][0][:blocks], ready["blocks"][0][:blocks]
    p_local_blocks, d_local_blocks = p_local // block_size, d_local // block_size
    if (len(p_table) != blocks or len(d_table) != blocks
            or p_table[:p_local_blocks] != p_lookup["local_blocks"][0]
            or d_table[:d_local_blocks] != d_lookup["local_blocks"][0]
            or len(turn["blocks"]) != blocks - d_local_blocks):
        raise ValueError(f"Incomplete prompt block table for {d_req}")
    for logical, block in enumerate(turn["blocks"], start=d_local_blocks):
        if (block["group"] != 0 or block["token_start"] != logical * block_size
                or block["token_end"] != min((logical + 1) * block_size, total)
                or block_identity(block["p_block"]) != block_identity(p_table[logical])
                or block_identity(block["d_block"]) != block_identity(d_table[logical])):
            raise ValueError(f"NIXL block {logical} differs from scheduler tables for {d_req}")
        if block["token_end"] - block["token_start"] == block_size:
            check_published_hash(trace, block, p_table[logical], d_table[logical], d_worker, d_req)

    p_writes = trace.select("vllm_gpu_kv_written", worker="p0", request_id=p_req)
    d_writes = trace.select("vllm_gpu_kv_written", worker=d_worker, request_id=d_req)
    check_prompt_writes(p_writes, p_table, p_local, total, block_size, p_req)
    check_prompt_writes(d_writes, d_table, total - 1, total, block_size, d_req)
    final_writes = [row for row in d_writes if row["token_start"] <= total - 1 < row["token_end"]]
    if not p_writes or len(final_writes) != 1:
        raise ValueError(f"Missing prompt write boundaries for {d_req}")
    stamps = (max(row["ts_ns"] for row in p_writes), turn["decode_dispatch_ns"],
              d_arrival["ts_ns"], d_lookup["ts_ns"], ready["ts_ns"],
              final_writes[0]["ts_ns"], release["ts_ns"])
    zero = p_arrival["ts_ns"]
    if tuple(sorted((zero, *stamps))) != (zero, *stamps):
        raise ValueError(f"Unexpected event order for {d_req}")
    return {"blocks": blocks, "p_table": p_table, "d_table": d_table, "zero": zero,
            "stamps": stamps, "p_lookup": p_lookup, "d_lookup": d_lookup,
            "p_writes": p_writes, "d_writes": d_writes, "ready": ready}


def trace_totals(summary, turns, trace):
    first = turns[0]
    result = {
        "first_turn_p_gpu_prefix_tokens": first["p_gpu_prefix_tokens"],
        "first_turn_d_gpu_prefix_tokens": first["d_gpu_prefix_tokens"],
        "nixl_blocks": sum(len(turn["blocks"]) for turn in turns),
        "nixl_bytes": sum(turn["nixl_transferred_bytes"] for turn in turns),
        "lmcache_gpu_restores": len(trace.select("lmcache_retrieve_completed", success=True)),
    }
    if (result["nixl_blocks"] != summary["nixl_restored_blocks"]
            or result["nixl_bytes"] != summary["nixl_transferred_bytes"]):
        raise ValueError("NIXL turn totals differ from the arm summary")
    for direction in ("read", "write"):
        events = trace.select(f"lmcache_disk_{direction}_completed")
        result[f"disk_{direction}s"] = len(events)
        result[f"disk_{direction}_bytes"] = sum(row["bytes"] for row in events)
    return result


def scale_trace_totals(turns, trace):
    return {
        "p_lmcache_prefix_tokens": sum(turn["p_lmcache_prefix_tokens"] for turn in turns),
        "gpu_to_lmcache_bytes": sum(row["bytes"] for row in trace.select("lmcache_store_completed", success=True)),
        "nixl_transfer_seconds": sum(turn["nixl_transfer_seconds"] for turn in turns),
    }


def load_arm_receipts(root, topology, manifest, manifest_hash, *, mode="disk", layout=LAYOUT):
    arm = root / topology
    summary = json.loads((arm / "summary.json").read_text())
    expected = {"status": "passed", "mode": mode, "layout": layout, "handoff": "nixl",
                "lmcache_topology": topology, "cold_d": False, "manifest_sha256": manifest_hash,
                "conversation_id": manifest["conversation_id"]}
    if any(summary[key] != value for key, value in expected.items()):
        raise ValueError(f"Unexpected arm configuration or manifest at {arm}")
    if json.loads((arm / "fixture.json").read_text()) != manifest:
        raise ValueError(f"Arm fixture differs from the frozen manifest at {arm}")
    turns = [json.loads(line) for line in (arm / "requests.jsonl").read_text().splitlines()]
    prompts = manifest["layouts"][layout]
    if not turns or len(turns) != len(prompts) or len(turns) != summary["turns"]:
        raise ValueError(f"Missing prompt or request receipts at {arm}")
    fields = ("turn", "request_key", "prompt_sha256", "prompt_tokens", "decode_worker")
    for index, (turn, prompt) in enumerate(zip(turns, prompts, strict=True)):
        if tuple(turn[field] for field in fields) != prompt_identity(prompt, index):
            raise ValueError(f"Manifest prompt or decode routing differs at {arm}, turn {prompt['turn']}")
    trace = Trace(arm / "traces", mode)
    trace.refresh()
    controls = (summary["lmcache_l1_budget_gb"], summary["lmcache_save_decode_cache"])
    return {"turns": turns, "trace": trace, "controls": controls,
            "metrics": trace_totals(summary, turns, trace)}


def load_arm(root, topology, manifest, manifest_hash, *, mode="disk", layout=LAYOUT):
    arm = load_arm_receipts(root, topology, manifest, manifest_hash, mode=mode, layout=layout)
    arm["timeline"] = [turn_timeline(arm["trace"], turn, manifest["block_size"]) for turn in arm["turns"]]
    return arm


def table(columns, rows):
    lines = [columns, ("---",) * len(columns), *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def offload_rows(trace, request):
    return trace.select("lmcache_store_completed", request_id=request, success=True)


def overview(manifest, manifest_hash, arms, output_mismatches, kv_mismatches, *, mode="disk", layout=LAYOUT):
    outputs = (f"Output token IDs differ on turns {output_mismatches}." if output_mismatches
               else "Output token IDs match on every turn.")
    movement = (f"KV coverage or movement differs on turns {kv_mismatches}." if kv_mismatches
                else "KV coverage and NIXL movement match on every turn.")
    title = f"# Paired NIXL {mode} {layout.replace('_', '-')} timeline"
    lines = [title, "",
             f"Conversation `{manifest['conversation_id']}` · frozen manifest SHA-256 `{manifest_hash}`.",
             "", f"{outputs} {movement}", ""]
    labels = {
        "first_turn_p_gpu_prefix_tokens": "Turn 1 P GPU prefix tokens",
        "first_turn_d_gpu_prefix_tokens": "Turn 1 D GPU prefix tokens",
        "nixl_blocks": "P → D NIXL blocks", "nixl_bytes": "P → D NIXL payload (B)",
        "lmcache_gpu_restores": "LMCache GPU restore events", "disk_writes": "Disk writes",
        "disk_write_bytes": "Disk write bytes", "disk_reads": "Disk reads",
        "disk_read_bytes": "Disk read bytes",
    }
    metrics = [arms[topology]["metrics"] for topology in TOPOLOGIES]
    lines.extend((table(("Measurement", "Per-engine", "Shared"),
                        ((label, *(f"{arm[key]:,}" for arm in metrics))
                         for key, label in labels.items())), "",
                  "Disk totals count complete events in the archived traces, including completions "
                  "after the runner's summary snapshot. LMCache disk reads move objects into server CPU "
                  "memory. A successful LMCache GPU restore is counted separately.", ""))
    for topology, arm in arms.items():
        lines.extend((f"## {topology.replace('_', ' ').capitalize()}", ""))
        rows = []
        stamps = []
        for turn, timing in zip(arm["turns"], arm["timeline"], strict=True):
            offloads = [offload_rows(arm["trace"], turn[key])
                        for key in ("p_request_id", "d_request_id")]
            stores = [f"{sum(len(row['objects']) for row in group):,} / "
                      f"{sum(row['bytes'] for row in group):,}" for group in offloads]
            rows.append((turn["turn"], turn["decode_worker"], f"{turn['prompt_tokens']:,}",
                         timing["blocks"], f"{turn['p_gpu_prefix_tokens']:,}",
                         f"{turn['d_gpu_prefix_tokens']:,}", f"{turn['d_prefix_loaded_tokens']:,}",
                         len(turn["blocks"]), f"{turn['nixl_transferred_bytes']:,}", *stores))
            stamps.append((turn["turn"], *(f"{(stamp - timing['zero']) / 1e6:,.3f}"
                                          for stamp in timing["stamps"])))
        lines.extend((table(("Turn", "D", "Prompt tokens", "vLLM blocks", "P local tokens",
                             "D local tokens", "NIXL tokens", "NIXL blocks", "NIXL bytes",
                             "P offload objects / B", "D offload objects / B"), rows), "",
                      "Times are elapsed milliseconds from P scheduler arrival on each turn "
                      "using the common host monotonic clock. D lookup is the recorded decision "
                      "after connector lookup.", "",
                      table(("Turn", "P last GPU write", "D dispatch", "D arrival", "D lookup",
                             "D KV ready", "D last prompt token write", "D releases request"), stamps),
                      ""))
    return "\n".join(lines)


def block_events(arm, identity, side, worker, block_size):
    trace = arm["trace"]
    slot_fields = dict(zip(BLOCK_FIELDS, identity, strict=True))
    life_events = {
        "vllm_gpu_block_allocated": "Allocated GPU block",
        "vllm_gpu_block_cached": "Indexed block under its prefix hash",
        "vllm_gpu_block_released": "Released reference to GPU block",
        "vllm_gpu_block_evicted": "Evicted prefix-cache entry",
    }
    rows = []
    objects = set()
    for event, label in life_events.items():
        for row in trace.select(event, worker=worker, **slot_fields):
            detail = row.get("reason", "")
            if "prefix_resident" in row:
                detail = f"{detail} · prefix resident {row['prefix_resident']}"
            rows.append((row["ts_ns"], worker, label, detail))

    for turn, timing in zip(arm["turns"], arm["timeline"], strict=True):
        if side == "d" and turn["decode_worker"] != worker:
            continue
        prefix = f"Turn {turn['turn']}"
        for logical, block in enumerate(timing[f"{side}_table"]):
            if block_identity(block) != identity:
                continue
            start = logical * block_size
            end = min(start + block_size, turn["prompt_tokens"])
            if start < turn[f"{side}_gpu_prefix_tokens"]:
                rows.append((timing[f"{side}_lookup"]["ts_ns"], worker,
                             f"{prefix} local prefix hit", f"Prompt tokens `[{start}, {end})`"))
            elif side == "d":
                rows.append((timing["ready"]["ts_ns"], worker,
                             f"{prefix} NIXL prefix ready", f"Includes prompt tokens `[{start}, {end})`"))
            for write in timing[f"{side}_writes"]:
                if write["block_id"] == identity[1] and start <= write["token_start"] < end:
                    rows.append((write["ts_ns"], worker, f"{prefix} model GPU write",
                                 f"Tokens `[{write['token_start']}, {write['token_end']})` · "
                                 f"recorded slots `[{write['slot_start']}, {write['slot_end']})`"))

            for store in offload_rows(trace, turn[f"{side}_request_id"]):
                for obj in store["objects"]:
                    if (obj["token_start"] <= start < obj["token_end"]
                            and identity[1] in obj["block_ids_by_group"]["0"]):
                        object_id = obj["object_id"]
                        objects.add((store["worker"], object_id))
                        rows.append((store["ts_ns"], worker, f"{prefix} GPU offload receipt",
                                     f"{store['worker']} object covers "
                                     f"`[{obj['token_start']}, {obj['token_end']})`"))
    return rows, objects


def focused_report(arm, topology, turn_number, logical, block_size):
    matches = [(turn, timing) for turn, timing in zip(arm["turns"], arm["timeline"], strict=True)
               if turn["turn"] == turn_number]
    if len(matches) != 1:
        raise ValueError(f"Turn {turn_number} is absent from {topology}")
    turn, timing = matches[0]
    if not 0 <= logical < timing["blocks"]:
        raise ValueError(f"Turn {turn_number} has logical blocks 0 through {timing['blocks'] - 1}")

    start = logical * block_size
    end = min(start + block_size, turn["prompt_tokens"])
    lines = [f"# {topology} · turn {turn_number} · logical block {logical}", "",
             f"Prompt tokens `[{start}, {end})` in a {turn['prompt_tokens']:,}-token request.", ""]
    slots = []
    events = []
    objects = set()
    for side, worker, alternative in (("p", "p0", "Model KV write"),
                                      ("d", turn["decode_worker"], "NIXL")):
        identity = block_identity(timing[f"{side}_table"][logical])
        slot = identity[1] * block_size
        origin = "Local GPU prefix" if start < turn[f"{side}_gpu_prefix_tokens"] else alternative
        slots.append((worker, *identity, f"`[{slot}, {slot + end - start})`", origin))
        worker_events, worker_objects = block_events(arm, identity, side, worker, block_size)
        events.extend(worker_events)
        objects.update(worker_objects)

    lines.extend((table(("Worker", "Pool", "Block ID", "Generation", "GPU token slots", "KV source"),
                        slots), "",
                  "Slot ranges above come from the scheduler block tables. The model write rows "
                  "use the GPU's recorded token-slot indices. NIXL readiness is measured for the "
                  "whole request, with the block included in its verified transfer list. Prefix-cache "
                  "publication records the index entry. The GPU write or NIXL-ready event records "
                  "when the corresponding KV becomes available.", ""))
    disk_events = {
        "lmcache_disk_write_completed": "Direct disk write completed",
        "lmcache_disk_read_completed": "Direct disk read completed",
        "lmcache_l1_resident": "LMCache CPU placement",
        "lmcache_l1_evicted": "LMCache CPU eviction",
    }
    for index, (server, object_id) in enumerate(sorted(objects), 1):
        lines.append(f"Object {index} on `{server}` · `{object_id}`")
        lines.append("")
        for event, label in disk_events.items():
            for row in arm["trace"].select(event, worker=server, object_id=object_id):
                detail = f"Object {index} · {row['bytes']:,} B"
                if "reason" in row:
                    detail += f" · {row['reason']}"
                events.append((row["ts_ns"], server, label, detail))

    lines.extend(("Times are elapsed milliseconds from P scheduler arrival on the selected turn. "
                  "Negative times show earlier events for the same slot generation or cache object. "
                  "Disk and CPU events are joined by server and object ID.", "",
                  table(("Elapsed (ms)", "Actor", "Observed event", "Detail"),
                        ((f"{(stamp - timing['zero']) / 1e6:,.3f}", actor, label, detail)
                         for stamp, actor, label, detail in sorted(events))), ""))
    return "\n".join(lines)


def write_movement_csv(output, arms, block_size, mode, layout):
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow((
        "topology", "mode", "layout", "turn", "d_worker", "logical_block", "token_start", "token_end",
        "p_pool_id", "p_block_id", "p_generation", "p_slot_start", "p_slot_end", "p_source",
        "p_model_write_ms", "d_pool_id", "d_block_id", "d_generation", "d_slot_start", "d_slot_end",
        "d_source", "d_local_lookup_ms", "nixl_dispatch_bound_ms", "nixl_ready_bound_ms", "d_model_write_ms",
    ))
    for topology, arm in arms.items():
        for turn, timing in zip(arm["turns"], arm["timeline"], strict=True):
            zero = timing["zero"]
            writes = {}
            for side in ("p", "d"):
                writes[side] = {
                    row["token_start"] // block_size: row["ts_ns"]
                    for row in timing[f"{side}_writes"] if row["token_start"] < turn["prompt_tokens"]
                }
            for index, (p_block, d_block) in enumerate(zip(timing["p_table"], timing["d_table"], strict=True)):
                start = index * block_size
                end = min(start + block_size, turn["prompt_tokens"])
                p_slot = p_block["block_id"] * block_size
                d_slot = d_block["block_id"] * block_size
                d_local = start < turn["d_gpu_prefix_tokens"]
                writer.writerow((
                    topology, mode, layout, turn["turn"], turn["decode_worker"], index, start, end,
                    *block_identity(p_block), p_slot, p_slot + end - start,
                    "local" if start < turn["p_gpu_prefix_tokens"] else "model",
                    elapsed_ms(writes["p"].get(index), zero),
                    *block_identity(d_block), d_slot, d_slot + end - start,
                    "local" if d_local else "nixl",
                    elapsed_ms(timing["d_lookup"]["ts_ns"], zero) if d_local else "",
                    "" if d_local else elapsed_ms(turn["decode_dispatch_ns"], zero),
                    "" if d_local else elapsed_ms(timing["ready"]["ts_ns"], zero),
                    elapsed_ms(writes["d"].get(index), zero),
                ))


def elapsed_ms(stamp, origin):
    return "" if stamp is None else f"{(stamp - origin) / 1e6:.3f}"


def load_pair(root, *, mode="disk", layout=LAYOUT):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = sha256(manifest_bytes).hexdigest()
    if manifest["block_size"] != 16 or manifest["chunk_size"] != 256:
        raise ValueError("Expected a 16-token vLLM block and a 256-token LMCache object")
    arms = {topology: load_arm(root, topology, manifest, manifest_hash, mode=mode, layout=layout)
            for topology in TOPOLOGIES}
    if len({arm["controls"] for arm in arms.values()}) != 1:
        raise ValueError("Arms use different LMCache budgets or decode offload settings")
    first, second = (arms[topology]["turns"] for topology in TOPOLOGIES)
    output_mismatches = matched_outputs(first, second, f"{mode}-{layout}")
    kv_mismatches = [a["turn"] for a, b in zip(first, second, strict=True)
                     if any(a[key] != b[key] for key in KV_FIELDS)
                     or len(a["blocks"]) != len(b["blocks"])]
    comparison = json.loads((root / "comparison.json").read_text())
    recount = {}
    for topology, arm in arms.items():
        metrics = arm["metrics"].copy()
        if "p_lmcache_prefix_tokens" in comparison["arms"][topology]:
            metrics.update(scale_trace_totals(arm["turns"], arm["trace"]))
        recount[topology] = metrics
    observed = {"arms": recount,
                "output_mismatch_turns": output_mismatches, "kv_mismatch_turns": kv_mismatches}
    if comparison != observed:
        raise ValueError("Archive comparison differs from the full-trace recount")
    return manifest, manifest_hash, arms, output_mismatches, kv_mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="extracted directory with manifest.json and both arms")
    parser.add_argument("--mode", choices=MODES, default="disk")
    parser.add_argument("--layout", choices=LAYOUTS, default=LAYOUT)
    parser.add_argument("--topology", choices=TOPOLOGIES, help="topology for a focused block report")
    parser.add_argument("--turn", type=int, help="turn for a focused block report")
    parser.add_argument("--block", type=int, help="zero-based logical block for a focused report")
    parser.add_argument("--movement-csv", action="store_true", help="emit all prompt block movements as CSV")
    args = parser.parse_args()
    focus = (args.topology, args.turn, args.block)
    if args.movement_csv and (args.turn is not None or args.block is not None):
        parser.error("--movement-csv accepts --topology only")
    if not args.movement_csv and focus.count(None) not in (0, len(focus)):
        parser.error("Use --topology, --turn, and --block together")
    try:
        manifest, manifest_hash, arms, output_mismatches, kv_mismatches = load_pair(
            args.archive, mode=args.mode, layout=args.layout,
        )
        if args.movement_csv:
            selected = arms if args.topology is None else {args.topology: arms[args.topology]}
            write_movement_csv(sys.stdout, selected, manifest["block_size"], args.mode, args.layout)
            return
        if args.topology is None:
            report = overview(manifest, manifest_hash, arms, output_mismatches, kv_mismatches,
                              mode=args.mode, layout=args.layout)
        else:
            report = focused_report(arms[args.topology], *focus, manifest["block_size"])
        print(report)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(1, f"Paired timeline failed: {error}\n")


if __name__ == "__main__":
    main()
