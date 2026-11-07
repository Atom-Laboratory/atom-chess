# Generated hardware artifacts

Files in this directory are reproducible outputs, not source records. Update the
inventory or assembly YAML and regenerate instead of editing reports manually.

`validation-report.txt` is produced by:

```bash
python tools/hardware/validate.py --report hardware/generated/validation-report.txt
```

Export the inventory and installed BOM snapshots from the repository root with
Python 3.12 (standard library only):

```powershell
python -B tools/hardware/export_bom.py --output-dir hardware/generated
```

The exporter validates the inventory and assembly, prints the validation report
and writes `inventory-bom.csv` and `installed-bom.csv`. Validation errors exit
with code 1 before export. Warnings are reported and allow export. The current
installed snapshot contains only the header. See the [BOM guide](../docs/bom.md)
for quantity semantics and the boundary with future KiCad exports.

To verify a change, run the command with a fresh output directory and compare
both CSV files with the checked-in snapshots.
