#!/usr/bin/env python3
"""Restore or verify the historical Full Blend sources from local bundles."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from checkout_sources import CHECKOUTS, SOURCE_ROOT, fetch_local_commit, git, source_pins, verify


FORKS = SOURCE_ROOT / "forks"
COMPONENTS = ("vllm", "lmcache")


def verify_fork(path, receipt):
    verify(path, receipt["source_commit"])
    actual = git(path, "rev-parse", "HEAD^{tree}", "HEAD^").stdout.splitlines()
    if actual != [receipt["historical_tree"], receipt["base_commit"]]:
        raise ValueError(f"{path} differs from its recorded tree or upstream parent")


def prepare(component, pins, verify_only):
    base_name = f"{component}-legacy-base"
    name = f"{component}-full-blend"
    seed = CHECKOUTS / base_name
    fork = FORKS / name
    bundle = SOURCE_ROOT / f"{name}.bundle"
    receipt = json.loads((SOURCE_ROOT / f"{name}-fork.json").read_text(encoding="utf-8"))
    pin = pins[base_name]
    if receipt["base_commit"] != pin or hashlib.sha256(bundle.read_bytes()).hexdigest() != receipt["bundle_sha256"]:
        raise ValueError(f"The bundle checksum or base pin disagrees with the receipt for {name}")
    verify(seed, pin)
    heads = git(seed, "bundle", "list-heads", bundle).stdout.splitlines()
    if heads != [f"{receipt['source_commit']} {receipt['ref']}"]:
        raise ValueError(f"The bundle ref disagrees with the receipt for {name}")
    git(seed, "bundle", "verify", bundle)

    if fork.exists() or fork.is_symlink() or verify_only:
        verify_fork(fork, receipt)
    else:
        FORKS.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=f".{name}-", dir=FORKS) as temp:
            staged = Path(temp) / name
            staged.mkdir()
            fetch_local_commit(staged, seed, pin)
            git(staged, "fetch", "--quiet", "--no-tags", bundle, receipt["ref"])
            git(staged, "switch", "--quiet", "--detach", "FETCH_HEAD")
            verify_fork(staged, receipt)
            staged.rename(fork)
    print(f"{name}: {receipt['source_commit']} (detached, clean, tree and base verified)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify existing V2 Full Blend snapshots")
    args = parser.parse_args()
    if FORKS.is_symlink() or CHECKOUTS.is_symlink():
        parser.error("The V2 source directories must be local directories")
    try:
        pins = source_pins()
        for component in COMPONENTS:
            prepare(component, pins, args.verify)
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Full Blend source setup failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
