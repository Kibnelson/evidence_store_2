#!/usr/bin/env python3
"""Materialize or verify pinned seed checkouts using local Git copies."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "third_party"
CHECKOUTS = SOURCE_ROOT / "checkouts"
V1_CHECKOUTS = ROOT.with_name("evidence_store_1") / "third_party/checkouts"
GIT_ENV = {
    **os.environ,
    "GIT_ALLOW_PROTOCOL": "file",
    "GIT_LFS_SKIP_SMUDGE": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
}


def git(path, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(path), *map(str, args)],
        check=check,
        env=GIT_ENV,
        stdout=subprocess.PIPE,
        text=True,
    )


def verify(path, commit):
    metadata = path / ".git"
    if path.is_symlink() or metadata.is_symlink() or not metadata.is_dir():
        raise ValueError(f"{path} is not a standalone source checkout")
    objects = metadata / "objects"
    if (objects.is_symlink() or not objects.is_dir()
            or any((objects / "info" / name).exists() for name in ("alternates", "http-alternates"))):
        raise ValueError(f"{path} must own its Git objects")
    actual = git(path, "rev-parse", "HEAD").stdout.strip()
    if actual != commit:
        raise ValueError(f"{path} is at {actual}, expected {commit}")
    if git(path, "symbolic-ref", "--quiet", "HEAD", check=False).returncode != 1:
        raise ValueError(f"{path.name} must have a detached HEAD")
    if git(path, "remote").stdout.strip():
        raise ValueError(f"{path.name} has a configured Git remote")
    if git(path, "status", "--porcelain", "--ignored=matching").stdout.strip():
        raise ValueError(f"{path} has modified or extra files")


def checkout(name, commit, donors, verify_only):
    destination = CHECKOUTS / name
    if destination.exists() or destination.is_symlink() or verify_only:
        verify(destination, commit)
    else:
        donor = donors / name
        verify(donor, commit)
        CHECKOUTS.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=CHECKOUTS) as temp:
            staged = Path(temp) / name
            staged.mkdir()
            fetch_local_commit(staged, donor, commit)
            git(staged, "switch", "--quiet", "--detach", "FETCH_HEAD")
            verify(staged, commit)
            staged.rename(destination)
    print(f"{name}: {commit} (detached, no remotes, clean)", flush=True)


def fetch_local_commit(destination, source, commit):
    git(destination, "init", "--quiet")
    git(destination, "fetch", "--quiet", "--no-tags", "--depth=1", source.resolve().as_uri(), commit)


def source_pins():
    entries = json.loads((SOURCE_ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    pins = {}
    for entry in entries:
        name, commit = entry["name"], entry["commit"]
        if (not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)
                or not re.fullmatch(r"[a-f0-9]{40}", commit) or name in pins):
            raise ValueError(f"Invalid or duplicate source pin for {name}")
        pins[name] = commit
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify existing V2 checkouts")
    parser.add_argument("--from-checkouts", type=Path, default=V1_CHECKOUTS,
                        help="directory of local donor checkouts (default: sibling V1 checkout directory)")
    parser.add_argument("sources", nargs="*", metavar="SOURCE", help="source name, or all if omitted")
    args = parser.parse_args()
    if CHECKOUTS.is_symlink():
        parser.error(f"The V2 checkout directory must be local: {CHECKOUTS}")
    pins = source_pins()
    names = args.sources or list(pins)
    unknown = [name for name in names if name not in pins]
    if unknown:
        parser.error(f"unknown sources: {', '.join(unknown)}")

    failed = False
    for name in names:
        try:
            checkout(name, pins[name], args.from_checkouts.expanduser(), args.verify)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            print(f"{name}: {error}", flush=True)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
