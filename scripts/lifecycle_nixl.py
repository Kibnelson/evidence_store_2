"""Verify a serialized native NIXL handoff using vLLM's transport metrics."""

import math
import re
from urllib.request import urlopen


_METRICS = {
    "vllm:nixl_bytes_transferred_sum": "bytes",
    "vllm:nixl_bytes_transferred_count": "transfers",
    "vllm:nixl_xfer_time_seconds_sum": "transfer_seconds",
    "vllm:nixl_post_time_seconds_sum": "post_seconds",
    "vllm:nixl_num_descriptors_sum": "descriptors",
    "vllm:nixl_num_failed_transfers_total": "failures",
    "vllm:nixl_num_declined_expired_reads_total": "declined_expired_reads",
}
_SAMPLE = re.compile(r"^([^\s{]+)(?:\{.*\})?\s+(\S+)(?:\s|$)")


def _parse_metrics(body):
    totals = {}
    for line in body.splitlines():
        match = _SAMPLE.match(line)
        if not match or match[1] not in _METRICS:
            continue
        name, value = _METRICS[match[1]], float(match[2])
        if not math.isfinite(value) or value < 0:
            raise RuntimeError(f"Invalid vLLM NIXL metric {name}: {value}")
        totals[name] = totals.get(name, 0.0) + value
    for required in ("bytes", "transfers", "transfer_seconds", "failures"):
        if required not in totals:
            raise RuntimeError(f"vLLM did not expose the required NIXL metric: {required}")
    return totals


def nixl_metrics(port, timeout):
    """Read a decoder's native aggregate metrics before or after its only request."""
    with urlopen(f"http://127.0.0.1:{port}/metrics", timeout=timeout) as response:
        return _parse_metrics(response.read().decode("utf-8"))


def _metric_delta(before, after, request_id):
    if before.keys() != after.keys():
        raise RuntimeError(f"NIXL metrics changed between snapshots: {request_id}")
    delta = {name: after[name] - value for name, value in before.items()}
    if any(value < 0 for value in delta.values()):
        raise RuntimeError(f"NIXL counters went backwards: {request_id}")
    if delta["failures"] or delta.get("declined_expired_reads", 0):
        raise RuntimeError(f"vLLM reported a failed NIXL transfer: {request_id}")
    return delta


def _received_blocks(trace, worker, request_id, remote, ready, local, loaded, block_size):
    source_request = remote["remote_request_id"]
    p_plans = trace.select("vllm_gpu_work_planned", worker="p0", request_id=source_request)
    if not p_plans:
        return None
    p_groups = p_plans[-1]["blocks"]
    d_groups = ready["blocks"]
    wire_groups = remote["remote_block_ids"]
    if not wire_groups or not len(p_groups) == len(d_groups) == len(wire_groups):
        raise RuntimeError(f"P and D NIXL KV groups differ: {request_id}")

    end = local + loaded
    first_block, stop_block = local // block_size, (end + block_size - 1) // block_size
    blocks = []
    for group, (p_slots, d_slots, remote_ids) in enumerate(zip(p_groups, d_groups, wire_groups, strict=True)):
        # The pilot has an ordinary full-attention model with the same block
        # geometry on P and D. A remote block list trimmed by another attention
        # layout needs a different join.
        if min(len(p_slots), len(d_slots), len(remote_ids)) < stop_block:
            raise RuntimeError(f"Incomplete NIXL block mapping for group {group}: {request_id}")
        for index in range(first_block, stop_block):
            source, destination = p_slots[index], d_slots[index]
            if not source or not destination or source["block_id"] != remote_ids[index]:
                raise RuntimeError(f"NIXL source block does not match the P slot: {request_id}, {index}")
            start, stop = index * block_size, (index + 1) * block_size
            block = {
                "group": group,
                "token_start": max(start, local),
                "token_end": min(stop, end),
                "p_block": source,
                "d_block": destination,
            }
            if start >= local and stop <= end:
                fields = {"group": group, "token_start": start, "partial": False}
                published_p = trace.select("vllm_gpu_block_cached", worker="p0", **fields, **source)
                published_d = trace.select(
                    "vllm_gpu_block_cached", worker=worker, request_id=request_id, **fields, **destination,
                )
                if not published_p or not published_d:
                    return None
                if published_p[-1]["block_hash"] != published_d[-1]["block_hash"]:
                    raise RuntimeError(f"NIXL P and D prefix hashes differ: {request_id}, {index}")
                block["p_block"] = {**source, "block_hash": published_p[-1]["block_hash"]}
            blocks.append(block)
    return blocks


def nixl_block_receipt(
    trace, request_id, worker, prompt_tokens, block_size, remote, before, after, *, decode_output_tokens=8,
):
    """Join D scheduler receipts to the native metrics delta for one turn."""
    delta = _metric_delta(before, after, request_id)
    lookups = trace.select("vllm_prefix_lookup", worker=worker, request_id=request_id)
    if not lookups:
        return None
    local, loaded = lookups[0]["local_tokens"], lookups[0]["external_tokens"]
    if not (0 <= local <= prompt_tokens and 0 <= loaded <= prompt_tokens - local):
        raise RuntimeError(f"Invalid D prefix coverage for {request_id}: {local}, {loaded}")
    if trace.select("lmcache_retrieve_completed", request_id=request_id):
        raise RuntimeError(f"The D request was served by LMCache in the NIXL arm: {request_id}")

    blocks = []
    ready_ns = None
    if loaded:
        ready = trace.select("vllm_external_kv_ready", worker=worker, request_id=request_id)
        if any(not row["success"] for row in ready):
            raise RuntimeError(f"vLLM reported a failed NIXL prefix load: {request_id}")
        if not ready or not delta["transfers"] or not delta["bytes"]:
            return None
        if ready[-1]["computed_tokens"] < local + loaded:
            raise RuntimeError(f"vLLM did not make the full NIXL prefix available: {request_id}")
        if not remote.get("do_remote_prefill"):
            raise RuntimeError(f"Missing the native NIXL prefill handshake: {request_id}")
        blocks = _received_blocks(trace, worker, request_id, remote, ready[-1], local, loaded, block_size)
        if blocks is None:
            return None
        ready_ns = ready[-1]["ts_ns"]
    elif local < prompt_tokens - 1 or delta["transfers"] or delta["bytes"]:
        raise RuntimeError(f"Expected a native NIXL pull or a fully local D prompt: {request_id}")

    writes = trace.select("vllm_gpu_kv_written", worker=worker, request_id=request_id)
    written = {position for row in writes for position in range(row["token_start"], row["token_end"])}
    # On a full prefix hit the native scheduler replays its last token for
    # logits. Count that actual model write separately from handoff bytes.
    first_write = min(local + loaded, prompt_tokens - 1)
    expected = set(range(first_write, prompt_tokens + decode_output_tokens - 1))
    if written - expected:
        raise RuntimeError(f"D rewrote unexpected token positions: {request_id}")
    if written != expected:
        return None
    return {
        "d_gpu_prefix_tokens": local,
        "d_prefix_loaded_tokens": loaded,
        "d_tail_computed_tokens": sum(position < prompt_tokens for position in written),
        "d_generated_input_tokens_written": sum(position >= prompt_tokens for position in written),
        "d_nixl_ready_ns": ready_ns,
        "nixl_transferred_bytes": int(delta["bytes"]),
        "nixl_transfers": int(delta["transfers"]),
        "nixl_transfer_seconds": delta["transfer_seconds"],
        "nixl_post_seconds": delta.get("post_seconds"),
        "nixl_descriptors": int(delta["descriptors"]) if "descriptors" in delta else None,
        "blocks": blocks,
    }
