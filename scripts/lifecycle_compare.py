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


def deployment(summary):
    # Published shared-LMCache pilot receipts predate explicit deployment fields.
    return {
        "handoff": summary.get("handoff", "lmcache"),
        "lmcache_topology": summary.get("lmcache_topology", "shared"),
        "cold_d": summary.get("cold_d", True),
        "lmcache_l1_budget_gb": summary.get("lmcache_l1_budget_gb", 8),
        "lmcache_save_decode_cache": summary.get("lmcache_save_decode_cache", False),
    }


def matched_outputs(first, second, label):
    if len(first) != len(second):
        raise ValueError(f"Mismatched count of measured turns: {label}")
    fields = ("turn", "request_key", "prompt_sha256", "decode_worker")
    mismatches = []
    for a, b in zip(first, second, strict=True):
        if any(a[key] != b[key] for key in fields):
            raise ValueError(f"Mismatched run inputs at {label} turn {a['turn']}")
        if a["output_token_ids"] != b["output_token_ids"]:
            mismatches.append(a["turn"])
    return mismatches


def compare(root):
    layouts = {}
    manifests = set()
    request_keys = []
    config = None
    for layout in ("chat", "carry_forward"):
        memory, memory_turns = load(root, "memory", layout)
        disk, disk_turns = load(root, "disk", layout)
        for summary in (memory, disk):
            manifests.add(summary["manifest_sha256"])
            arm_config = deployment(summary)
            if config is None:
                config = arm_config
            elif arm_config != config:
                raise ValueError("Expected the same deployment controls in all four arms")
        mismatched_outputs = matched_outputs(memory_turns, disk_turns, layout)
        if config["handoff"] == "lmcache" and any(
            a["d_prefix_loaded_tokens"] != b["d_prefix_loaded_tokens"]
            for a, b in zip(memory_turns, disk_turns, strict=True)
        ):
            raise ValueError(f"Mismatched shared-LMCache prefix coverage for {layout}")
        request_keys.append([turn["request_key"] for turn in memory_turns])
        layouts[layout] = {"memory": memory, "disk": disk, "output_mismatch_turns": mismatched_outputs}
    if len(manifests) != 1 or request_keys[0] != request_keys[1]:
        raise ValueError("Expected the same frozen workload and turn keys in all four arms")
    return {
        "deployment": config,
        "layouts": layouts,
        "token_outputs_match": all(not entry["output_mismatch_turns"] for entry in layouts.values()),
    }


def compare_deployments(root, against, result):
    baseline = compare(against)
    workloads = {
        output["layouts"]["chat"]["memory"]["manifest_sha256"]
        for output in (result, baseline)
    }
    if len(workloads) != 1:
        raise ValueError("Deployment comparison requires the same frozen manifest")
    arms = {}
    for layout in ("chat", "carry_forward"):
        arms[layout] = {}
        for mode in ("memory", "disk"):
            _, measured = load(root, mode, layout)
            _, reference = load(against, mode, layout)
            arms[layout][mode] = matched_outputs(measured, reference, f"{mode}-{layout}")
    return {
        "reference": baseline,
        "output_mismatch_turns": arms,
        "same_cold_d_control": result["deployment"]["cold_d"] == baseline["deployment"]["cold_d"],
        "same_lmcache_l1_budget": result["deployment"]["lmcache_l1_budget_gb"] ==
                                  baseline["deployment"]["lmcache_l1_budget_gb"],
        "same_decode_offload_policy": result["deployment"]["lmcache_save_decode_cache"] ==
                                      baseline["deployment"]["lmcache_save_decode_cache"],
        "token_outputs_match": all(not turns for row in arms.values() for turns in row.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--against", type=Path, help="compare the same four arms from another deployment")
    args = parser.parse_args()
    try:
        result = compare(args.results)
        if args.against is not None:
            result["against"] = compare_deployments(args.results, args.against, result)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Lifecycle comparison failed: {error}\n")
    print(json.dumps(result, indent=2))
    all_match = result["token_outputs_match"]
    if "against" in result:
        all_match = all_match and result["against"]["token_outputs_match"]
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
