"""Inspect DXF file inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kesit.cad_io.dxf_reader import read_dxf


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect DXF inventory")
    parser.add_argument("dxf_path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    inventory = read_dxf(args.dxf_path)
    data = inventory.to_dict()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Path: {data['path']}")
        print(f"Version: {data['dxf_version']}")
        print(f"INSUNITS: {data['insunits']} ({data['insunits_unit']})")
        print(f"Total entities: {data['total_entities']}")
        print("Entity counts:")
        for k, v in sorted(data["entity_counts"].items()):
            print(f"  {k}: {v}")
        print(f"Layers ({len(data['layers'])}):")
        for layer in data["layers"]:
            print(f"  {layer}")


if __name__ == "__main__":
    main()
