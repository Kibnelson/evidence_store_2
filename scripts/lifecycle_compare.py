#!/usr/bin/env python3
"""Compare four completed lifecycle arms with the same frozen conversation."""

import argparse
import json
from pathlib import Path


def load(root, mode, layout):
    arm = root / f"{mode}-{layout}"
    summary = json.loads((arm / "summary.json").read_text())
    turns = [json.loads(line) for line in (arm / "requests.jsonl").read_text().splitlines()]
    if (summary["status"], summary["mode"], summary["layout"]) != ("passed", mode, layout):
        raise ValueError(f"Unexpected arm status or configuration: {arm}")
    if len(turns) != summary["turns"]:
        raise ValueError(f"Missing turn receipts: {arm}")
    return summary, turns


def compare(root):
    layouts = {}
    manifests = set()
    request_keys = []
    for layout in ("chat", "carry_forward"):
        memory, memory_turns = load(root, "memory", layout)
        disk, disk_turns = load(root, "disk", layout)
        manifests.update((memory["manifest_sha256"], disk["manifest_sha256"]))
        if len(memory_turns) != len(disk_turns):
            raise ValueError(f"Mismatched count of measured turns: {layout}")
        mismatched_outputs = []
        for cpu, direct_disk in zip(memory_turns, disk_turns, strict=True):
            fields = ("turn", "request_key", "prompt_sha256", "decode_worker", "d_prefix_loaded_tokens")
            if any(cpu[key] != direct_disk[key] for key in fields):
                raise ValueError(f"Mismatched run inputs at {layout} turn {cpu['turn']}")
            if cpu["output_token_ids"] != direct_disk["output_token_ids"]:
                mismatched_outputs.append(cpu["turn"])
        request_keys.append([turn["request_key"] for turn in memory_turns])
        layouts[layout] = {"memory": memory, "disk": disk, "output_mismatch_turns": mismatched_outputs}
    if len(manifests) != 1 or request_keys[0] != request_keys[1]:
        raise ValueError("Expected the same frozen workload and turn keys in all four arms")
    return {"layouts": layouts,
            "token_outputs_match": all(not entry["output_mismatch_turns"] for entry in layouts.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.results)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Lifecycle comparison failed: {error}\n")
    print(json.dumps(result, indent=2))
    return 0 if result["token_outputs_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
