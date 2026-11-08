#!/usr/bin/env python3
"""Check that a Nav2 params file has a RangeSensorLayer in both costmaps."""
import sys

import yaml

COSTMAPS = ("local_costmap", "global_costmap")


def range_layers(params, costmap):
    block = params[costmap][costmap]["ros__parameters"]
    return [
        name
        for name in block.get("plugins", [])
        if isinstance(block.get(name), dict)
        and "RangeSensorLayer" in str(block[name].get("plugin", ""))
    ]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_range_layer.py <nav2_params.yaml>")
    with open(sys.argv[1]) as f:
        params = yaml.safe_load(f)
    ok = True
    for costmap in COSTMAPS:
        try:
            layers = range_layers(params, costmap)
        except KeyError as err:
            print(f"{costmap}: missing key {err}")
            ok = False
            continue
        print(f"{costmap}: range layers = {layers}")
        ok = ok and bool(layers)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
