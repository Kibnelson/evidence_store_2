#!/usr/bin/env python3
"""Collect cumulative Run 3 NIXL lifecycle traces and publish each conversation."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory, mkdtemp

from lifecycle_compare import matched_outputs
from lifecycle_prepare import sha256_file
from lifecycle_scale_report import render_report, write_comparison


SOURCE = Path(__file__).resolve().parents[1]
MODES = ("memory", "disk")
LAYOUTS = ("chat", "carry_forward")
TOPOLOGIES = ("per_engine", "shared_engine")
CHECKPOINTS = (1, 5, 10)
PHASES = tuple(f"{mode}-{layout}" for mode in MODES for layout in LAYOUTS)


def git(repo, *args, capture=False):
    result = subprocess.run(["git", "-C", str(repo), *map(str, args)], check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def branch_tip(repo, branch):
    match = git(repo, "ls-remote", "--refs", "origin", f"refs/heads/{branch}", capture=True)
    return match.split("\t", 1)[0] if match else None


def prepare_publisher(repo, remote, branch, source_commit):
    git(repo, "init", "-q")
    git(repo, "remote", "add", "origin", remote)
    if branch_tip(repo, branch) is not None:
        git(repo, "fetch", "--depth=1", "--no-tags", "origin", f"refs/heads/{branch}")
    else:
        git(repo, "fetch", "--depth=1", "--no-tags", "origin", source_commit)
    git(repo, "checkout", "--quiet", "--detach", "FETCH_HEAD")


def publish(repo, branch, report, message):
    git(repo, "add", "--", report.relative_to(repo))
    git(repo, "commit", "-m", message)
    commit = git(repo, "rev-parse", "HEAD", capture=True)
    git(repo, "push", "origin", f"HEAD:refs/heads/{branch}")
    if branch_tip(repo, branch) != commit:
        raise RuntimeError(f"GitHub read-back differs for {branch}. Local captures are still available.")
    print(f"Verified {branch} at {commit}", flush=True)


def load_plan(path):
    plan = json.loads(path.read_bytes())
    if (plan["schema_version"] != 1 or tuple(plan["modes"]) != MODES
            or tuple(plan["layouts"]) != LAYOUTS or tuple(plan["topologies"]) != TOPOLOGIES
            or tuple(plan["checkpoints"]) != CHECKPOINTS or len(plan["conversations"]) != 10):
        raise ValueError("Expected the exact Run 3 ten-conversation plan")
    seen = set()
    for entry in plan["conversations"]:
        cid = entry["conversation_id"]
        if not re.fullmatch(r"[a-f0-9]{32}", cid) or cid in seen:
            raise ValueError(f"Invalid or duplicate conversation ID {cid}")
        seen.add(cid)
        manifest = fixture_path(path, entry)
        if sha256_file(manifest) != entry["manifest_sha256"]:
            raise ValueError(f"Frozen manifest checksum differs for {cid}")
        fixture = json.loads(manifest.read_bytes())
        if (fixture["conversation_id"] != cid or fixture["block_size"] != 16 or fixture["chunk_size"] != 256
                or any(len(fixture["layouts"][layout]) != entry["turns"] for layout in LAYOUTS)):
            raise ValueError(f"Frozen manifest does not match the plan for {cid}")
        for layout in LAYOUTS:
            lengths = [len(turn["token_ids"]) for turn in fixture["layouts"][layout]]
            if not lengths or max(lengths) > plan["max_prompt_tokens"]:
                raise ValueError(f"Prompt budget exceeded for {cid} {layout}")
            disk_bound = 2 * sum(size // 256 for size in lengths) * 37_748_736
            if entry["disk_bytes_upper_bound_by_layout"][layout] != disk_bound:
                raise ValueError(f"Disk bound differs from the frozen prompts for {cid} {layout}")
    return plan


def fixture_path(plan_path, entry):
    relative = f"manifests/{entry['conversation_id']}.json"
    if entry["manifest_path"] != relative:
        raise ValueError(f"Unexpected fixture path for {entry['conversation_id']}")
    return plan_path.parent / relative


def completed_arm(run_dir, entry, mode, layout, topology):
    summary_path = run_dir / "summary.json"
    if not summary_path.is_file():
        return False
    summary = json.loads(summary_path.read_bytes())
    expected = {"status": "passed", "mode": mode, "layout": layout, "handoff": "nixl",
                "lmcache_topology": topology, "cold_d": False, "manifest_sha256": entry["manifest_sha256"],
                "conversation_id": entry["conversation_id"], "turns": entry["turns"]}
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Arm receipt differs from the campaign at {run_dir}")
    if not (run_dir / "requests.jsonl").is_file() or not any((run_dir / "traces").glob("*.jsonl")):
        raise ValueError(f"Arm receipt is missing requests or traces at {run_dir}")
    return True


def run_arm(phase, disk_dir, failed, entry, mode, layout, topology, timeout):
    run_dir = phase / topology
    if completed_arm(run_dir, entry, mode, layout, topology):
        print(f"Reusing completed arm {run_dir}", flush=True)
    else:
        if run_dir.exists() or disk_dir.exists():
            failed.mkdir(parents=True, exist_ok=True)
            old = Path(mkdtemp(prefix=f"{phase.name}-{topology}.", dir=failed))
            for artifact in (run_dir, disk_dir):
                if artifact.exists():
                    artifact.rename(old / artifact.name)
            print(f"Preserved the previous attempt at {old}", flush=True)

        command = [sys.executable, "-B", str(SOURCE / "scripts/lifecycle_run.py"),
                   "--manifest", str(phase / "manifest.json"), "--mode", mode, "--layout", layout,
                   "--run-dir", str(run_dir), "--port-base", "18700" if topology == "per_engine" else "18800",
                   "--timeout", str(timeout)]
        if mode == "disk":
            bound = entry["disk_bytes_upper_bound_by_layout"][layout]
            free = shutil.disk_usage(disk_dir.parent).free
            if free < bound:
                raise RuntimeError(f"{disk_dir.parent} has {free:,} B free, below the {bound:,} B disk bound")
            command.extend(("--disk-dir", str(disk_dir)))
        env = {**os.environ, "EVIDENCESTORE_PD_HANDOFF": "nixl", "EVIDENCESTORE_PD_COLD_D": "0",
               "EVIDENCESTORE_LMCACHE_TOPOLOGY": topology}
        subprocess.run(command, cwd=SOURCE, env=env, check=True)
        if not completed_arm(run_dir, entry, mode, layout, topology):
            raise RuntimeError(f"Runner did not produce a completed arm at {run_dir}")

    # The runner exits and stops all workers before recording a passed arm.
    if disk_dir.exists():
        shutil.rmtree(disk_dir)
        print(f"Removed completed arm disk objects at {disk_dir}", flush=True)


def capture(root, plan_path, case, name, entry, timeout):
    case.mkdir(parents=True, exist_ok=True)
    manifest = fixture_path(plan_path, entry)
    (case / "manifest.json").write_bytes(manifest.read_bytes())
    disk_root = root / "disk-work" / name
    disk_root.mkdir(parents=True, exist_ok=True)
    comparisons = {}
    for mode in MODES:
        for layout in LAYOUTS:
            label = f"{mode}-{layout}"
            phase = case / label
            phase.mkdir(exist_ok=True)
            (phase / "manifest.json").write_bytes(manifest.read_bytes())
            for topology in TOPOLOGIES:
                print(f"{mode} {layout} · {topology}", flush=True)
                run_arm(phase, disk_root / f"{label}-{topology}", root / "failed" / name,
                        entry, mode, layout, topology, timeout)
            comparisons[label] = write_comparison(phase, mode=mode, layout=layout)
    disk_root.rmdir()
    return comparisons


def write_result(report, case, name, entry, comparisons):
    relative = f"conversations/{name}/traces.tar.gz"
    archive = report / relative
    archive.parent.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, "w:gz") as bundle:
        for item in ("manifest.json", *PHASES):
            bundle.add(case / item, arcname=item)
    result = {key: entry[key] for key in ("conversation_id", "turns", "manifest_sha256")}
    result.update(archive=relative, archive_sha256=sha256_file(archive), comparisons=comparisons)
    result["memory_disk_output_mismatch_turns"] = {}
    for layout in LAYOUTS:
        result["memory_disk_output_mismatch_turns"][layout] = {}
        for topology in TOPOLOGIES:
            requests = [
                [json.loads(line) for line in (case / f"{mode}-{layout}" / topology / "requests.jsonl")
                 .read_text().splitlines()]
                for mode in MODES
            ]
            result["memory_disk_output_mismatch_turns"][layout][topology] = matched_outputs(
                *requests, f"memory vs disk, {topology}, {layout}")
    (archive.parent / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def read_result(report, name, entry):
    path = report / "conversations" / name / "result.json"
    if not path.exists():
        return None
    row = json.loads(path.read_bytes())
    expected = f"conversations/{name}/traces.tar.gz"
    if (any(row[key] != entry[key] for key in ("conversation_id", "turns", "manifest_sha256"))
            or set(row["comparisons"]) != set(PHASES) or row["archive"] != expected
            or sha256_file(report / expected) != row["archive_sha256"]):
        raise ValueError(f"Published receipt or archive differs at {path}")
    return row


def run_campaign(args, plan_path, plan, publisher):
    root = plan_path.parent
    branch = f"results/lifecycle-{args.campaign}"
    source_commit = git(SOURCE, "rev-parse", "HEAD", capture=True)
    prepare_publisher(publisher, args.remote, branch, source_commit)
    report = publisher / "reports/lifecycle" / args.campaign
    report.mkdir(parents=True, exist_ok=True)
    parameters = {"campaign_sha256": sha256_file(plan_path), "source_commit": source_commit}
    provenance = report / "provenance.json"
    if provenance.exists() and json.loads(provenance.read_bytes()) != parameters:
        saved = json.loads(provenance.read_bytes())
        raise ValueError(f"Existing campaign uses plan and source {saved}. Restore them or choose another campaign.")
    provenance.write_text(json.dumps(parameters, indent=2) + "\n")
    (report / "campaign.json").write_bytes(plan_path.read_bytes())

    results = []
    for index, entry in enumerate(plan["conversations"][:args.through], 1):
        cid = entry["conversation_id"]
        name = f"{index:02d}-{cid}"
        case = root / "captures" / name
        print(f"[{index}/{args.through}] {cid} · {entry['turns']} turns", flush=True)
        row = read_result(report, name, entry)
        if row is None:
            comparisons = capture(root, plan_path, case, name, entry, args.timeout)
            row = write_result(report, case, name, entry, comparisons)
            results.append(row)
            if index in CHECKPOINTS:
                (report / f"run3-{index}-conversations.md").write_text(render_report(plan, results, index))
            publish(publisher, branch, report, f"Archive Run 3 lifecycle conversation {index}")
        else:
            results.append(row)
            print(f"Verified published archive for {cid}", flush=True)
        if case.exists():
            shutil.rmtree(case)
        if index in CHECKPOINTS:
            print(f"Published {report.relative_to(publisher)}/run3-{index}-conversations.md", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="frozen campaign.json from lifecycle_scale_prepare.py")
    parser.add_argument("--campaign", required=True, help="publication branch suffix and report name")
    parser.add_argument("--through", type=int, choices=CHECKPOINTS, required=True)
    parser.add_argument("--remote", default="git@github.com:Kibnelson/evidence_store_2.git")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.campaign) or args.timeout <= 0:
        parser.error("Use a simple campaign name and a positive timeout")
    if not os.getenv("SLURM_JOB_ID"):
        parser.error("Run inside a four-GPU Slurm allocation with the verified NIXL runtime active")
    os.environ.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    try:
        plan_path = args.plan.resolve(strict=True)
        plan = load_plan(plan_path)
        with (plan_path.parent / "campaign.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with TemporaryDirectory(prefix="publish-", dir=plan_path.parent) as publisher:
                run_campaign(args, plan_path, plan, Path(publisher))
    except (OSError, ValueError, RuntimeError, KeyError, KeyboardInterrupt, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Lifecycle campaign stopped: {error}\n")


if __name__ == "__main__":
    main()
