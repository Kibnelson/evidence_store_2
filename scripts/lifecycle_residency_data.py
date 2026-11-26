"""Build GPU and LMCache residency data from a matched NIXL trace pair."""

from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

from lifecycle_paired_timeline import block_identity, load_pair
from lifecycle_prompt_timeline import prompt_text


def prefix_key(tokens, end):
    return sha256(json.dumps(tokens[:end], separators=(",", ":")).encode("ascii")).hexdigest()


class Recorder:
    def __init__(self, origin):
        self.origin = origin
        self.records = []
        self.indices = {}

    def ms(self, timestamp):
        return (timestamp - self.origin) / 1e6

    def refs(self, *rows):
        indices = []
        for row in rows:
            key = id(row)
            if key not in self.indices:
                self.indices[key] = len(self.records)
                self.records.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            indices.append(self.indices[key])
        return list(dict.fromkeys(indices))

    def segment(self, actor, first, last, *evidence):
        rows = (first, *evidence, last) if last is not None else (first, *evidence)
        return {
            "actor": actor,
            "start": self.ms(first["ts_ns"]),
            "end": None if last is None else self.ms(last["ts_ns"]),
            "refs": self.refs(*rows),
        }


def gpu_endings(trace):
    endings = defaultdict(list)
    for row in trace.select("vllm_gpu_block_evicted"):
        endings[(row["worker"], block_identity(row))].append(row)
    for row in trace.select("vllm_gpu_block_released", ref_count=0, prefix_resident=False):
        endings[(row["worker"], block_identity(row))].append(row)
    return {key: sorted(rows, key=lambda row: row["ts_ns"]) for key, rows in endings.items()}


def group_ranges(size, step):
    for start in range(0, size, step):
        yield start, min(start + step, size)


def cache_objects(trace, prompts, arm, block_size, chunk_size):
    requests = {}
    for prompt, turn, timing in zip(prompts, arm["turns"], arm["timeline"], strict=True):
        tokens = prompt["token_ids"]
        requests[turn["p_request_id"]] = (tokens, timing["p_table"])
        requests[turn["d_request_id"]] = (tokens, timing["d_table"])

    objects = {}
    for store in trace.select("lmcache_store_completed", success=True):
        tokens, slots = requests[store["request_id"]]
        for obj in store["objects"]:
            start, end = obj["token_start"], obj["token_end"]
            source_ids = [slot["block_id"] for slot in slots[start // block_size:end // block_size]]
            if (start < 0 or start % chunk_size or end - start != chunk_size or end > len(tokens)
                    or set(obj["block_ids_by_group"]) != {"0"}
                    or obj["block_ids_by_group"]["0"] != source_ids):
                raise ValueError(f"LMCache source slots do not match the prompt in {store['request_id']}")
            identity = (store["worker"], obj["object_id"])
            metadata = (start, end, prefix_key(tokens, end), obj["bytes"])
            item = objects.setdefault(identity, {"metadata": metadata, "stores": [], "events": []})
            if item["metadata"] != metadata:
                raise ValueError(f"LMCache identity changes its source prefix: {identity}")
            item["stores"].append(store)

    for event in ("lmcache_l1_resident", "lmcache_l1_evicted",
                  "lmcache_disk_write_completed", "lmcache_disk_read_completed"):
        for row in trace.select(event):
            identity = (row["worker"], row["object_id"])
            item = objects.get(identity)
            if item is None or item["metadata"][3] != row["bytes"]:
                raise ValueError(f"LMCache event has no matching stored object: {identity}")
            item["events"].append(row)
    return objects


def cache_copies(objects, recorder):
    copies = defaultdict(list)
    for (actor, object_id), item in sorted(objects.items()):
        start, end, key, size = item["metadata"]
        segments = copies[(start, end, key)]
        stores = item["stores"]
        events = sorted(item["events"], key=lambda row: row["ts_ns"])
        disk_writes = [row for row in events if row["event"] == "lmcache_disk_write_completed"]
        if disk_writes:
            disk_events = [row for row in events if row["event"] == "lmcache_disk_read_completed"]
            segment = recorder.segment(actor, disk_writes[0], None, *stores, *disk_writes[1:], *disk_events)
            segments.append({**segment, "tier": "disk", "object_id": object_id, "bytes": size})

        placement = None
        evidence = []
        last_read = None
        for row in events:
            event = row["event"]
            if event == "lmcache_disk_read_completed":
                last_read = row
            elif event == "lmcache_l1_resident":
                if placement is None:
                    placement = row
                    evidence = list(stores)
                else:
                    evidence.append(row)
                if row["reason"] == "prefetch" and last_read is not None:
                    evidence.append(last_read)
            elif event == "lmcache_l1_evicted":
                if placement is None:
                    raise ValueError(f"LMCache CPU release with no placement: {object_id}")
                segment = recorder.segment(actor, placement, row, *evidence)
                segments.append({**segment, "tier": "cpu", "object_id": object_id, "bytes": size})
                placement = None
        if placement is not None:
            segment = recorder.segment(actor, placement, None, *evidence)
            segments.append({**segment, "tier": "cpu", "object_id": object_id, "bytes": size})
    for segments in copies.values():
        segments.sort(key=lambda segment: (segment["start"], segment["actor"], segment["tier"]))
    return copies


def gpu_slot_evidence(arm, prompts, block_size, recorder):
    """Index each verified prompt span by logical offset and physical slot generation."""
    endings = gpu_endings(arm["trace"])
    starts = {}
    candidates = defaultdict(list)
    turn_blocks = []
    for prompt, turn, timing in zip(prompts, arm["turns"], arm["timeline"], strict=True):
        tokens = prompt["token_ids"]
        decoder = turn["decode_worker"]
        plans = {row["step"]: row for row in arm["trace"].select(
            "vllm_gpu_work_planned", worker="p0", request_id=turn["p_request_id"],
        )}
        writes = defaultdict(list)
        for row in timing["p_writes"]:
            writes[row["token_start"] // block_size].append(row)
        receipt = {"actor": decoder, "start": recorder.ms(turn["decode_dispatch_ns"]),
                   "end": recorder.ms(timing["ready"]["ts_ns"]),
                   "refs": recorder.refs(turn, timing["ready"])}
        blocks = []
        boundaries = group_ranges(len(tokens), block_size)
        for logical, ((start, end), p_slot, d_slot) in enumerate(zip(
            boundaries, timing["p_table"], timing["d_table"], strict=True,
        )):
            key = prefix_key(tokens, end)
            placements = []
            for side, actor, slot in (("p", "p0", p_slot), ("d", decoder, d_slot)):
                physical = (actor, block_identity(slot))
                location = (*physical, key)
                if start < turn[f"{side}_gpu_prefix_tokens"]:
                    observed = timing[f"{side}_lookup"]
                    first, evidence = starts.setdefault(location, (observed, []))
                    evidence.append(observed)
                elif side == "p":
                    first = observed = max(writes[logical], key=lambda row: row["ts_ns"])
                    plan = plans[first["step"]]
                    if plan["blocks"][0][logical] != slot:
                        raise ValueError(f"GPU model write differs from turn {turn['turn']} slot generation")
                    evidence = [plan]
                    starts[location] = (first, evidence)
                else:
                    first = observed = timing["ready"]
                    evidence = [turn]
                    starts[location] = (first, evidence)

                last = next((row for row in endings.get(physical, ())
                             if row["ts_ns"] >= first["ts_ns"]), None)
                if last is not None and last["ts_ns"] < observed["ts_ns"]:
                    raise ValueError(f"GPU block {slot['block_id']} observed after its generation ended")
                segment = recorder.segment(actor, first, last, *evidence)
                placements.append({**segment, **slot})

            moves = [] if start < turn["d_gpu_prefix_tokens"] else [receipt]
            slot = {"logical": logical, "start": start, "end": end, "key": key, "p": p_slot, "d": d_slot}
            blocks.append(slot)
            candidates[start].append((end, tokens, placements, moves))
        turn_blocks.append(blocks)

    for prompt, blocks in zip(prompts, turn_blocks, strict=True):
        tokens = prompt["token_ids"]
        for block in blocks:
            end = block["end"]
            prefix = tokens[:end]
            gpu, moves = {}, []
            for available, other, placements, receipts in candidates[block["start"]]:
                if available < end or other[:end] != prefix:
                    continue
                moves.extend(receipts)
                for row in placements:
                    key = (row["actor"], block_identity(row), row["end"])
                    if key not in gpu:
                        gpu[key] = row.copy()
                    else:
                        gpu[key]["start"] = min(gpu[key]["start"], row["start"])
                        gpu[key]["refs"] = list(dict.fromkeys((*gpu[key]["refs"], *row["refs"])))
            block["gpu"] = sorted(gpu.values(), key=lambda row: (row["start"], row["actor"]))
            block["moves"] = sorted(moves, key=lambda row: (row["start"], row["actor"]))
    return turn_blocks


def arm_data(arm, prompts, texts, block_size, chunk_size):
    origin = arm["timeline"][0]["zero"]
    recorder = Recorder(origin)
    trace = arm["trace"]
    objects = cache_objects(trace, prompts, arm, block_size, chunk_size)
    copies = cache_copies(objects, recorder)
    turn_blocks = gpu_slot_evidence(arm, prompts, block_size, recorder)
    turns = []
    for prompt, text, turn, timing, blocks in zip(
        prompts, texts, arm["turns"], arm["timeline"], turn_blocks, strict=True,
    ):
        tokens = prompt["token_ids"]
        groups = []
        for start, end in group_ranges(len(tokens), chunk_size):
            key = prefix_key(tokens, end)
            groups.append({
                "start": start, "end": end, "key": key,
                "blocks": blocks[start // block_size:(end + block_size - 1) // block_size],
                "copies": copies.get((start, end, key), []),
            })
        turns.append({
            "turn": turn["turn"], "ms": recorder.ms(timing["zero"]), "decoder": turn["decode_worker"],
            "token_ids": tokens, "text": text, "p_local": turn["p_gpu_prefix_tokens"],
            "d_local": turn["d_gpu_prefix_tokens"], "nixl_tokens": turn["d_prefix_loaded_tokens"],
            "groups": groups,
        })
    final = max(row["ts_ns"] for events in trace.by_event.values() for row in events)
    return {"end_ms": recorder.ms(final), "records": recorder.records, "turns": turns}


def build_data(phase, mode, layout, prompt_archive=None):
    manifest, digest, arms, _, _ = load_pair(Path(phase), mode=mode, layout=layout)
    block_size, chunk_size = manifest["block_size"], manifest["chunk_size"]
    prompts = manifest["layouts"][layout]
    texts = [None if prompt_archive is None else prompt_text(prompt_archive, manifest, digest, prompt, layout)
             for prompt in prompts]
    return {
        "conversation_id": manifest["conversation_id"], "mode": mode, "layout": layout,
        "block_size": block_size, "chunk_size": chunk_size,
        "arms": {name: arm_data(arm, prompts, texts, block_size, chunk_size) for name, arm in arms.items()},
    }
