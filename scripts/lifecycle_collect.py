#!/usr/bin/env python3
"""Collect the completed four-arm lifecycle pilot for Git review."""

import argparse
import gzip
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from lifecycle_compare import compare
from lifecycle_prepare import sha256_file


WORKERS = ("p0", "d0", "d1", "d2")


def require_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular file at {path}")
    return path


def compress(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, destination.open("wb") as compressed:
        with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0, compresslevel=6) as stream:
            shutil.copyfileobj(original, stream)


def collect(results, destination, manifest, include_worker_logs):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Output already exists at {destination}")

    original = require_file(manifest)
    manifest_sha = sha256_file(original)
    fixture = json.loads(original.read_bytes())
    arms = {}
    for mode in ("memory", "disk"):
        for layout in ("chat", "carry_forward"):
            phase = f"{mode}-{layout}"
            arm = results / phase
            trace_dir = arm / "traces"
            if arm.is_symlink() or trace_dir.is_symlink():
                raise ValueError(f"Expected local phase and trace directories at {arm}")
            summary = require_file(arm / "summary.json")
            requests = require_file(arm / "requests.jsonl")
            arm_fixture = require_file(arm / "fixture.json")
            if json.loads(arm_fixture.read_bytes()) != fixture:
                raise ValueError(f"Frozen fixture differs in {phase}")
            traces = sorted(require_file(path) for path in trace_dir.glob("*.jsonl"))
            if not traces:
                raise ValueError(f"No lifecycle traces found in {trace_dir}")
            logs = []
            if include_worker_logs:
                topology = json.loads(summary.read_bytes()).get("lmcache_topology", "shared")
                servers = tuple(f"lmcache-{worker}" for worker in WORKERS) if topology == "per_engine" else ("lmcache",)
                logs = [require_file(arm / f"{worker}.log") for worker in (*servers, *WORKERS)]
            arms[phase] = summary, requests, traces, logs

    comparison = compare(results)
    if not comparison["token_outputs_match"]:
        raise ValueError("Expected matching output tokens between CPU memory and disk")
    recorded_sha = comparison["layouts"]["chat"]["memory"]["manifest_sha256"]
    if recorded_sha != manifest_sha:
        raise ValueError(f"Manifest SHA-256 differs from the completed run at {original}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{destination.name}-", dir=destination.parent) as work:
        archive = Path(work) / "archive"
        archive.mkdir()
        shutil.copyfile(original, archive / "manifest.json")
        (archive / "comparison.json").write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
        for phase, (summary, requests, traces, logs) in arms.items():
            target = archive / phase
            target.mkdir()
            shutil.copyfile(summary, target / "summary.json")
            shutil.copyfile(requests, target / "requests.jsonl")
            for trace in traces:
                compress(trace, target / "traces" / f"{trace.name}.gz")
            for log in logs:
                compress(log, target / "logs" / f"{log.name}.gz")

        files = sorted(path for path in archive.rglob("*") if path.is_file())
        checksums = "".join(f"{sha256_file(path)}  {path.relative_to(archive).as_posix()}\n" for path in files)
        (archive / "SHA256SUMS").write_text(checksums, encoding="utf-8")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Output already exists at {destination}")
        archive.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, help="original prompt manifest, defaults to RESULTS/../manifest.json")
    parser.add_argument("--include-worker-logs", action="store_true", help="include compressed server logs")
    args = parser.parse_args()
    manifest = args.manifest if args.manifest is not None else args.results.parent / "manifest.json"
    try:
        collect(args.results, args.output, manifest, args.include_worker_logs)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Lifecycle collection failed: {error}\n")
    print(f"Collected lifecycle report at {args.output}")


if __name__ == "__main__":
    main()
