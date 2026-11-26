#!/usr/bin/env python3
"""Build an offline browser view of KV residency for one archived conversation."""

import argparse
import json
from pathlib import Path
from zipfile import BadZipFile

from lifecycle_paired_timeline import LAYOUTS, MODES
from lifecycle_residency_data import build_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", type=Path, help="extracted phase with manifest.json and both topology directories")
    parser.add_argument("--mode", choices=MODES, default="disk")
    parser.add_argument("--layout", choices=LAYOUTS, default="carry_forward")
    parser.add_argument("--prompt-archive", type=Path, help="optional verified Run 3 replication ZIP")
    parser.add_argument("--output", type=Path, required=True, help="standalone HTML file to write")
    args = parser.parse_args()
    try:
        data = build_data(args.phase, args.mode, args.layout, args.prompt_archive)
        template = Path(__file__).with_suffix(".html").read_text(encoding="utf-8")
        marker = "__TRACE_DATA__"
        if template.count(marker) != 1:
            raise ValueError("Viewer template must contain exactly one trace data marker")
        # Prevent prompt text or raw trace strings from closing the JSON script element.
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        args.output.write_text(template.replace(marker, payload), encoding="utf-8")
    except (OSError, ValueError, KeyError, RuntimeError, BadZipFile) as error:
        parser.exit(1, f"Residency view failed: {error}\n")
    print(args.output)


if __name__ == "__main__":
    main()
