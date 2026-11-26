"""Read and join lifecycle receipts from the four engines and the cache server."""

from collections import defaultdict
import hashlib
import json
import os


class Trace:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        self.offsets = {}
        self.by_event = defaultdict(list)

    def refresh(self):
        for path in self.path.glob("*.jsonl"):
            with path.open("rb") as stream:
                stream.seek(self.offsets.get(path, 0))
                for line in stream:
                    if not line.endswith(b"\n"):
                        break
                    row = json.loads(line)
                    self.by_event[row["event"]].append(row)
                    self.offsets[path] = self.offsets.get(path, 0) + len(line)
        if self.by_event["lmcache_disk_io_failed"]:
            raise RuntimeError(f"Direct I/O failed: {self.by_event['lmcache_disk_io_failed'][-1]}")
        if self.mode == "memory" and any(self.by_event[event] for event in DISK_EVENTS):
            raise RuntimeError("Unexpected filesystem I/O in CPU memory mode")

    def select(self, event, **fields):
        return [row for row in self.by_event[event]
                if all(row.get(key) == value for key, value in fields.items())]

    def latest_time(self, event, **fields):
        return max((row["ts_ns"] for row in self.select(event, **fields)), default=0)

    def gpu_written(self, block, position, block_size, before):
        group, block_id = block["group"], block["block_id"]
        identity = {key: block[key] for key in ("pool_id", "block_id", "generation")}
        positions = set()
        for write in self.select("vllm_gpu_kv_written", worker=block["worker"], group=group, block_id=block_id):
            start = max(position, write["token_start"])
            end = min(position + block_size, write["token_end"])
            if write["ts_ns"] > before or end <= start:
                continue
            plans = self.select("vllm_gpu_work_planned", worker=block["worker"],
                                step=write["step"], request_id=write["request_id"])
            if any(plan["blocks"][group][position // block_size] == identity for plan in plans):
                positions.update(range(start, end))
        return len(positions) == block_size

    def direct_io(self, event, obj, start=0):
        matches = [row for row in self.select(event, object_id=obj["object_id"])
                   if row["ts_ns"] >= start]
        for row in matches:
            # Linux O_DIRECT is checked on the descriptor by the adapter.
            if not row["direct"] or not row["fd_flags"] & getattr(os, "O_DIRECT", 0x4000) or row["bytes"] != obj["bytes"]:
                raise RuntimeError(f"Invalid direct I/O receipt: {row}")
        return matches

    def absent_from_l1(self, obj, after=0):
        fields = {"object_id": obj["object_id"]}
        resident = self.latest_time("lmcache_l1_resident", **fields)
        evicted = self.latest_time("lmcache_l1_evicted", **fields)
        return evicted >= after and evicted > resident


DISK_EVENTS = ("lmcache_disk_write_completed", "lmcache_disk_read_completed")


def prefix_keys(tokens, length, chunk_size):
    return [hashlib.sha256(json.dumps(tokens[:end], separators=(",", ":")).encode()).hexdigest()
            for end in range(chunk_size, length + 1, chunk_size)]


def store_sources(trace, request_id, prefixes, chunk_size, sources):
    for row in trace.select("lmcache_store_completed", request_id=request_id):
        if not row["success"]:
            raise RuntimeError(f"P cache store failed: {request_id}")
        for obj in row["objects"]:
            start, end = obj["token_start"], obj["token_end"]
            if start < 0 or start % chunk_size or end - start != chunk_size:
                raise RuntimeError(f"Unexpected P object token span: {obj}")
            key = prefixes[start // chunk_size]
            sources[key] = {**obj, "store_request_id": request_id,
                            "p_store_completed_ns": row["ts_ns"]}


def storage_ready(trace, prefixes, sources):
    if any(key not in sources for key in prefixes):
        return None
    expected = [sources[key] for key in prefixes]
    for obj in expected:
        fields = {"object_id": obj["object_id"]}
        if trace.mode == "memory":
            if trace.latest_time("lmcache_l1_resident", **fields) <= trace.latest_time(
                "lmcache_l1_evicted", **fields
            ):
                return None
        else:
            writes = trace.direct_io(DISK_EVENTS[0], obj)
            if not writes or not trace.absent_from_l1(obj, max(row["ts_ns"] for row in writes)):
                return None
    return expected


def restore_receipt(trace, request_id, worker, expected, dispatch, block_size, prefix_tokens):
    lookups = trace.select("vllm_prefix_lookup", worker=worker, request_id=request_id)
    if any(row["local_tokens"] for row in lookups):
        raise RuntimeError(f"Controlled D request used a GPU prefix hit: {request_id}")
    transfers = trace.select("lmcache_retrieve_completed", request_id=request_id)
    if any(not row["success"] for row in transfers):
        raise RuntimeError(f"D cache load failed: {request_id}")
    ready = trace.select("vllm_external_kv_ready", worker=worker, request_id=request_id)
    if any(not row["success"] for row in ready):
        raise RuntimeError(f"vLLM reported a failed external load: {request_id}")
    if not (lookups and transfers and ready):
        return None
    if ready[-1]["computed_tokens"] < prefix_tokens:
        raise RuntimeError(f"D connector declared only a partial prefix ready: {request_id}")

    def object_key(obj):
        return obj["object_id"], obj["token_start"], obj["token_end"]

    restored = {object_key(obj): (obj, row["ts_ns"])
                for row in transfers for obj in row["objects"]}
    if set(restored) - {object_key(obj) for obj in expected}:
        raise RuntimeError(f"D retrieved an unexpected object: {request_id}")
    if len(restored) < len(expected):
        return None
    results = []
    for source in expected:
        destination, complete = restored[object_key(source)]
        if destination["bytes"] != source["bytes"] or complete < dispatch:
            raise RuntimeError(f"Invalid cache transfer: {destination}")
        reads = []
        if trace.mode == "disk":
            reads = [row for row in trace.direct_io(DISK_EVENTS[1], source, dispatch)
                     if row["ts_ns"] <= complete]
            if not reads or not trace.absent_from_l1(source, max(row["ts_ns"] for row in reads)):
                return None
        blocks = join_blocks(trace, source, destination, worker, request_id, ready[-1]["blocks"], block_size)
        results.append({
            "object_id": source["object_id"],
            "token_start": source["token_start"],
            "token_end": source["token_end"],
            "bytes": destination["bytes"],
            "p_store_request_id": source["store_request_id"],
            "p_store_completed_ns": source["p_store_completed_ns"],
            "d_retrieve_completed_ns": complete,
            "disk_reads": reads,
            "blocks": blocks,
        })
    return results


def join_blocks(trace, source, destination, worker, request_id, ready, block_size):
    blocks = []
    source_groups = source["block_ids_by_group"]
    destination_groups = destination["block_ids_by_group"]
    if source_groups.keys() != destination_groups.keys():
        raise RuntimeError("P and D KV groups differ")
    expected_count = (source["token_end"] - source["token_start"]) // block_size
    for group, src_ids in source_groups.items():
        dst_ids = destination_groups[group]
        group_id = int(group)
        if len(src_ids) != expected_count or len(dst_ids) != expected_count:
            raise RuntimeError(f"Wrong block count for {source['object_id']}")
        for i, (src_id, dst_id) in enumerate(zip(src_ids, dst_ids, strict=True)):
            position = source["token_start"] + i * block_size
            cached = [row for row in trace.select(
                "vllm_gpu_block_cached", worker="p0", block_id=src_id,
                group=group_id, token_start=position, partial=False
            ) if row["ts_ns"] <= source["p_store_completed_ns"]]
            dst = ready[group_id][position // block_size]
            if not cached or dst is None or dst["block_id"] != dst_id:
                raise RuntimeError(f"Missing or inconsistent KV block mapping at {position}")
            src = max(cached, key=lambda row: row["ts_ns"])
            d_cached = trace.select(
                "vllm_gpu_block_cached", worker=worker, request_id=request_id,
                group=group_id, token_start=position, partial=False, **dst,
            )
            if not any(row["block_hash"] == src["block_hash"] for row in d_cached):
                raise RuntimeError(f"P and D block hashes differ or are missing at {position}")
            if not trace.gpu_written(src, position, block_size, source["p_store_completed_ns"]):
                raise RuntimeError(f"P GPU writes did not populate the stored block at {position}")
            blocks.append({
                "group": group_id,
                "token_start": position,
                "token_end": position + block_size,
                "p_block": {key: src[key] for key in ("pool_id", "block_id", "generation", "block_hash")},
                "d_block": dst,
            })
    return blocks
