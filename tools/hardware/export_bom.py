#!/usr/bin/env python3
"""Export CSV inventory and installed BOM snapshots from validated hardware data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from validate import Validator, repository_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    root = repository_root(Path(__file__))
    validator = Validator(root)
    components = validator.validate_components(
        validator.load(root / "hardware/inventory/components.yaml")
    )
    assembly = validator.load(root / "hardware/inventory/assembly.yaml")
    validator.validate_assembly(assembly, components)
    print(validator.render(), end="")
    if any(message.severity == "ERROR" for message in validator.messages):
        return 1

    installed = set(assembly["assembly"]["installed_components"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = (
        "id", "category", "status", "identification_status", "manufacturer",
        "model", "inventory_quantity", "datasheet", "evidence",
    )
    for filename, identifiers in (
        ("inventory-bom.csv", components),
        ("installed-bom.csv", installed),
    ):
        with (args.output_dir / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fields)
            for identifier in sorted(identifiers):
                item = components[identifier]
                writer.writerow((
                    identifier, item["category"], item["status"],
                    item["identification"]["status"], item["manufacturer"],
                    item["model"], item["quantity"], item["datasheet"],
                    " | ".join(item["evidence"]),
                ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
