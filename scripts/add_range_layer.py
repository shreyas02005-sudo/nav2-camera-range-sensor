#!/usr/bin/env python3
"""Add the range sensor layer to the local and global costmaps.

Works on a copy of the stock TurtleBot3 waffle Nav2 parameter file. It finds
the `plugins:` list inside each costmap section by content rather than by line
number, so it keeps working across parameter file versions.

Usage:
    python3 add_range_layer.py input.yaml output.yaml
"""
import sys
from pathlib import Path

LAYER_BLOCK = [
    'range_layer:',
    '  plugin: "nav2_costmap_2d::RangeSensorLayer"',
    '  topics: ["/front_range"]',
    '  phi: 1.2',
    '  clear_threshold: 0.46',
    '  mark_threshold: 0.98',
    '  clear_on_max_reading: True',
]


def patch_section(lines: list[str], section: str) -> bool:
    """Patch the first plugins list found under a top-level `section:` key."""
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(f"{section}:"))
    except StopIteration:
        print(f"Section '{section}' not found.")
        return False

    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line and not line[0].isspace():
            break  # reached the next top-level key
        if line.strip().startswith("plugins:") and "inflation_layer" in line:
            if "range_layer" in line:
                print(f"{section}: range_layer already present.")
                return True
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = line.replace('"inflation_layer"', '"range_layer", "inflation_layer"')
            lines[i + 1 : i + 1] = [indent + l for l in LAYER_BLOCK]
            print(f"{section}: range_layer added.")
            return True

    print(f"{section}: plugins list not found.")
    return False


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    lines = src.read_text().split("\n")

    ok_local = patch_section(lines, "local_costmap")
    ok_global = patch_section(lines, "global_costmap")
    if not (ok_local and ok_global):
        print("Not all sections were patched; output not written.")
        return 1

    dst.write_text("\n".join(lines))
    print(f"Wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
