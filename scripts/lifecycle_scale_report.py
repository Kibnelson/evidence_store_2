#!/usr/bin/env python3
"""Validate a NIXL conversation pair and report measured campaign milestones."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from lifecycle_compare import matched_outputs
from lifecycle_paired_timeline import (
    KV_FIELDS,
    LAYOUTS,
    MODES,
    TOPOLOGIES,
    block_identity,
    check_published_hash,
    load_arm_receipts,
    one_event,
    scale_trace_totals,
    table,
)


PHASES = tuple(f"{mode}-{layout}" for mode in MODES for layout in LAYOUTS)
METRICS = (
    ("nixl_blocks", "NIXL GPU blocks"),
    ("nixl_bytes", "NIXL payload (B)"),
    ("nixl_transfer_seconds", "Native NIXL transfer time (s)"),
    ("p_lmcache_prefix_tokens", "P external prefix tokens from LMCache lookups"),
    ("gpu_to_lmcache_bytes", "GPU-to-LMCache copy bytes"),
    ("lmcache_gpu_restores", "LMCache-to-GPU restores"),
    ("disk_writes", "Completed disk writes"),
    ("disk_write_bytes", "Disk write bytes"),
    ("disk_reads", "Completed disk reads"),
    ("disk_read_bytes", "Disk read bytes"),
)


def verify_turn(trace, turn, block_size):
    p_request, d_request = turn["p_request_id"], turn["d_request_id"]
    decoder, total = turn["decode_worker"], turn["prompt_tokens"]
    for worker, request, local, external in (
            ("p0", p_request, turn["p_gpu_prefix_tokens"], turn["p_lmcache_prefix_tokens"]),
            (decoder, d_request, turn["d_gpu_prefix_tokens"], turn["d_prefix_loaded_tokens"])):
        arrival = one_event(trace, "vllm_request_arrived", worker, request)
        lookups = trace.select("vllm_prefix_lookup", worker=worker, request_id=request)
        if (arrival["prompt_tokens"] != total or not lookups or not 0 <= local <= total
                or not 0 <= external <= total - local
                or (lookups[0]["local_tokens"], lookups[0]["external_tokens"]) != (local, external)):
            raise ValueError(f"Invalid traced prompt coverage for {request}")

    local, loaded = turn["d_gpu_prefix_tokens"], turn["d_prefix_loaded_tokens"]
    covered = local + loaded
    ready = trace.select("vllm_external_kv_ready", worker=decoder, request_id=d_request)
    if trace.select("lmcache_retrieve_completed", request_id=d_request):
        raise ValueError(f"Unexpected D-side LMCache restore for {d_request}")
    if loaded:
        if (not ready or any(not row["success"] for row in ready)
                or ready[-1]["ts_ns"] != turn["d_kv_ready_ns"] or ready[-1]["computed_tokens"] < covered
                or turn["nixl_transfers"] <= 0 or turn["nixl_transferred_bytes"] <= 0):
            raise ValueError(f"Missing completed native NIXL transfer for {d_request}")
        p_plan = max(trace.select("vllm_gpu_work_planned", worker="p0", request_id=p_request),
                     key=lambda row: row["ts_ns"])
        p_groups, d_groups = p_plan["blocks"], ready[-1]["blocks"]
        first, stop = local // block_size, (covered + block_size - 1) // block_size
        expected = [(group, index) for group in range(len(p_groups)) for index in range(first, stop)]
        if (not p_groups or len(p_groups) != len(d_groups) or len(turn["blocks"]) != len(expected)
                or any(len(group) < stop for group in (*p_groups, *d_groups))):
            raise ValueError(f"Incomplete NIXL block coverage for {d_request}")
        for block, (group, index) in zip(turn["blocks"], expected, strict=True):
            p_slot, d_slot = p_groups[group][index], d_groups[group][index]
            if (block["group"] != group or block["token_start"] != max(index * block_size, local)
                    or block["token_end"] != min((index + 1) * block_size, covered)
                    or block_identity(block["p_block"]) != block_identity(p_slot)
                    or block_identity(block["d_block"]) != block_identity(d_slot)):
                raise ValueError(f"NIXL block receipt differs from the trace for {d_request}")
            if block["token_end"] - block["token_start"] == block_size:
                check_published_hash(trace, block, p_slot, d_slot, decoder, d_request)
    elif (ready or turn["d_kv_ready_ns"] is not None or local < total - 1
          or turn["nixl_transfers"] or turn["nixl_transferred_bytes"] or turn["blocks"]):
        raise ValueError(f"Expected a GPU-local D prompt without a transfer for {d_request}")

    writes = trace.select("vllm_gpu_kv_written", worker=decoder, request_id=d_request)
    positions = {pos for row in writes for pos in range(row["token_start"], row["token_end"])}
    first_write = min(covered, total - 1)
    generated = len(turn["output_token_ids"]) - 1
    if (positions != set(range(first_write, total + generated))
            or turn["d_tail_computed_tokens"] != total - first_write
            or turn["d_generated_input_tokens_written"] != generated):
        raise ValueError(f"Unexpected traced D model writes for {d_request}")


def paired_comparison(pair_dir, *, mode="disk", layout="carry_forward", manifest_path=None):
    """Recount a completed pair from raw traces, including late disk events."""
    if mode not in MODES or layout not in LAYOUTS:
        raise ValueError(f"Unsupported campaign phase {mode}-{layout}")
    manifest_bytes = (manifest_path or pair_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["block_size"] != 16 or manifest["chunk_size"] != 256:
        raise ValueError("Expected 16-token GPU blocks and 256-token LMCache objects")
    digest = sha256(manifest_bytes).hexdigest()
    arms = {topology: load_arm_receipts(pair_dir, topology, manifest, digest, mode=mode, layout=layout)
            for topology in TOPOLOGIES}
    for topology, arm in arms.items():
        if arm["controls"] != (8, False):
            raise ValueError(f"Unexpected LMCache budget or decode offload setting for {topology}")
        metrics = arm["metrics"]
        if (metrics["first_turn_p_gpu_prefix_tokens"] or metrics["first_turn_d_gpu_prefix_tokens"]
                or arm["turns"][0]["p_lmcache_prefix_tokens"]):
            raise ValueError(f"Expected fresh GPU prompt caches for {topology}")
        for turn in arm["turns"]:
            verify_turn(arm["trace"], turn, manifest["block_size"])
        metrics.update(scale_trace_totals(arm["turns"], arm["trace"]))

    per_engine, shared = (arms[topology]["turns"] for topology in TOPOLOGIES)
    output_mismatches = matched_outputs(per_engine, shared, f"{mode}-{layout}")
    kv_mismatches = [a["turn"] for a, b in zip(per_engine, shared, strict=True)
                     if any(a[key] != b[key] for key in KV_FIELDS) or len(a["blocks"]) != len(b["blocks"])]
    return {"arms": {topology: arms[topology]["metrics"] for topology in TOPOLOGIES},
            "output_mismatch_turns": output_mismatches, "kv_mismatch_turns": kv_mismatches}


def write_comparison(pair_dir, *, mode="disk", layout="carry_forward", manifest_path=None):
    comparison = paired_comparison(pair_dir, mode=mode, layout=layout, manifest_path=manifest_path)
    path = pair_dir / "comparison.json"
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=pair_dir, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(comparison, stream, indent=2)
            stream.write("\n")
            stream.close()
            try:
                path.hardlink_to(temporary)
            except FileExistsError:
                if json.loads(path.read_text()) != comparison:
                    raise ValueError(f"Existing comparison differs from the verified traces at {path}") from None
        finally:
            temporary.unlink()
    return comparison


def summarized_pairs(campaign, results, through):
    planned = campaign["conversations"]
    if not 1 <= through <= len(planned):
        raise ValueError(f"Expected a milestone between 1 and {len(planned)} conversations")
    by_conversation = {row["conversation_id"]: row for row in results}
    if len(by_conversation) != len(results):
        raise ValueError("Duplicate completed conversation receipt")
    selected = []
    for spec in planned[:through]:
        conversation = spec["conversation_id"]
        if conversation not in by_conversation:
            raise ValueError(f"Milestone is missing a completed pair for {conversation}")
        result = by_conversation[conversation]
        if any(spec[key] != result[key] for key in ("turns", "manifest_sha256")):
            raise ValueError(f"Completed pair differs from the frozen plan for {conversation}")
        comparisons = result["comparisons"]
        if set(comparisons) != set(PHASES):
            raise ValueError(f"Expected all four phase comparisons for {conversation}")
        for phase, comparison in comparisons.items():
            if set(comparison["arms"]) != set(TOPOLOGIES):
                raise ValueError(f"Expected both NIXL topologies for {conversation} ({phase})")
        selected.append(result)
    return selected


def disk_bytes(metrics):
    return metrics["disk_write_bytes"] + metrics["disk_read_bytes"]


def mismatch_turns(comparison, field):
    return ", ".join(map(str, comparison[field])) or "None"


def phase_report(selected, phase):
    totals = {topology: {metric: sum(row["comparisons"][phase]["arms"][topology][metric] for row in selected)
                         for metric, _ in METRICS} for topology in TOPOLOGIES}
    per_engine, shared = (totals[topology] for topology in TOPOLOGIES)
    baseline_io, shared_io = disk_bytes(per_engine), disk_bytes(shared)
    disk_change = shared_io - baseline_io
    outcome = []
    if phase.startswith("disk-"):
        if disk_change:
            direction = "fell" if disk_change < 0 else "rose"
            change = f" ({abs(disk_change) / baseline_io:.1%})" if baseline_io else ""
            outcome = [f"Total disk I/O {direction} by {abs(disk_change):,} B{change}.", ""]
        else:
            outcome = ["Total disk I/O matched across topologies.", ""]
    rows = []
    for key, label in METRICS:
        style = ",.3f" if key == "nixl_transfer_seconds" else ","
        rows.append((label, format(per_engine[key], style), format(shared[key], style)))
    rows.append(("Total disk I/O (B)", f"{baseline_io:,}", f"{shared_io:,}"))
    conversations = []
    for result in selected:
        comparison = result["comparisons"][phase]
        left, right = (comparison["arms"][topology] for topology in TOPOLOGIES)
        archive = result.get("archive")
        link = f"[Trace bundle]({quote(str(archive), safe=':/?&=#%+@')})" if archive else "—"
        conversations.append((f"`{result['conversation_id']}`", result["turns"],
                              f"{left['nixl_blocks']:,} / {right['nixl_blocks']:,}",
                              f"{left['p_lmcache_prefix_tokens']:,} / {right['p_lmcache_prefix_tokens']:,}",
                              f"{left['disk_write_bytes']:,} / {right['disk_write_bytes']:,}",
                              f"{left['disk_read_bytes']:,} / {right['disk_read_bytes']:,}",
                              mismatch_turns(comparison, "output_mismatch_turns"),
                              mismatch_turns(comparison, "kv_mismatch_turns"), link))

    return [
        f"## {phase.replace('_', '-').capitalize()}", "",
        table(("Measured total", "Per-engine LMCache", "Shared LMCache"), rows), "", *outcome,
        table(("Conversation", "Turns", "NIXL blocks", "P LMCache tokens", "Disk writes (B)", "Disk reads (B)",
               "Output mismatches", "KV mismatches", "Archive"), conversations), "",
    ]


def render_report(campaign, results, through):
    """Render a milestone from completed, checksum-verified pair receipts."""
    selected = summarized_pairs(campaign, results, through)
    total_turns = sum(row["turns"] for row in selected)
    noun = "conversation" if through == 1 else "conversations"
    tiers = []
    for result in selected:
        if "memory_disk_output_mismatch_turns" in result:
            differences = result["memory_disk_output_mismatch_turns"]
            cells = [", ".join(map(str, differences[layout][topology])) or "None"
                     for layout in LAYOUTS for topology in TOPOLOGIES]
            tiers.append((f"`{result['conversation_id']}`", *cells))
    cross_tier = []
    if tiers:
        cross_tier = ["## Memory versus disk output mismatches", "",
                      table(("Conversation", "Chat per-engine", "Chat shared",
                             "Carry-forward per-engine", "Carry-forward shared"), tiers), ""]
    return "\n".join([
        f"# NIXL run 3 lifecycle milestone for {through} {noun}", "",
        f"{through} CLAPNQ {noun} · {total_turns} turns per phase and topology.", "",
        "Each arm starts with fresh workers, GPU caches, LMCache servers, and a separate disk directory. "
        "Within each layout the two topologies use the same frozen prompt IDs and round-robin D routing. "
        "GPU prefixes can stay warm within each conversation.", "",
        "Disk amounts count completed events in the raw traces, including completions after the runner's "
        "summary snapshot. Disk reads enter CPU memory. LMCache GPU restores are counted separately. "
        "Native NIXL time sums the transfer metrics recorded for each turn.", "",
        "Paired cells list per-engine first and shared second. Mismatch turn numbers refer to the turns within "
        "that conversation. KV mismatches compare per-turn GPU prefix hits, P LMCache hits, NIXL coverage, D prompt compute, "
        "and NIXL bytes and block counts.", "",
        *(line for phase in PHASES for line in phase_report(selected, phase)),
        *cross_tier,
        "Each trace bundle contains the frozen manifest, both request streams, and the raw engine and "
        "LMCache events for each phase. The offline timeline and slot tools can inspect an individual turn or block.", "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    comparison = commands.add_parser("compare", help="verify a pair and write comparison.json")
    comparison.add_argument("pair_dir", type=Path)
    comparison.add_argument("--mode", choices=MODES, default="disk")
    comparison.add_argument("--layout", choices=LAYOUTS, default="carry_forward")
    comparison.add_argument("--manifest", type=Path)
    report = commands.add_parser("report", help="render a completed milestone to stdout")
    report.add_argument("campaign", type=Path)
    report.add_argument("results", type=Path, help="JSON array of completed pair receipts")
    report.add_argument("--through", type=int, choices=(1, 5, 10), required=True)
    args = parser.parse_args()
    try:
        if args.command == "compare":
            result = write_comparison(args.pair_dir, mode=args.mode, layout=args.layout, manifest_path=args.manifest)
            print(json.dumps(result, indent=2))
        else:
            campaign = json.loads(args.campaign.read_text())
            results = json.loads(args.results.read_text())
            print(render_report(campaign, results, args.through), end="")
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(1, f"Lifecycle milestone failed: {error}\n")


if __name__ == "__main__":
    main()
