# BOM and parts registers

| Register | Authority | Current baseline |
| --- | --- | --- |
| [Inventory BOM](../generated/inventory-bom.csv) | Component inventory and assembly references | 12 records, including two lots with unknown quantities |
| [Installed BOM](../generated/installed-bom.csv) | Assembly references | Zero confirmed installation records |
| Mechanical source register below | Repository CAD and export records | Sources identified; occurrence counts and manufacturing releases pending |
| Electrical design BOM | Future revisioned KiCad project | Pending approved schematic and exact part selection |

The exported quantity is the inventory quantity, including in the installed
snapshot. The assembly schema records installation by ID and has no separate
installed count. For a partially installed lot, record individual occurrences or
extend the schema before publishing an installed quantity. Blank quantities and
part numbers are unknown. Procurement needs a design quantity, verified usable
stock and an approved part or drawing revision for each line. The
[historical BOM audit](../../docs/audit/2026-10-30/bom-audit.csv) is a source of
candidates and gaps.

## Mechanical source register

| Group | Source | Required quantity / release evidence |
| --- | --- | --- |
| Base, arm links, Z mechanism and gripper | [Mechanical evidence and CAD references](../../docs/mechanics/README.md) | TBD per assembly occurrence; verify revision, interfaces and drawings |
| Bearings, guides, transmission and fasteners | [Mechanical audit](../../docs/audit/2026-10-30/mechanical-cad.md) | TBD per assembly occurrence; identify exact parts, fits and quantities |
| Board sections | [Board source and print assets](../Project/chess_board/README.md) | TBD for fabrication release; verify plate geometry, joining and print configuration |
| Chess pieces | [Piece source and exports](../Project/chess_pieces/README.md) | TBD for physical release; verify material, mass, base dimensions and production count |
| SBC enclosure | [Banana Pi M5 enclosure sources](../Project/Banana%20Pi%20M5%20case/) | TBD after confirming host model, mounting and enclosure revision |

For each fabricated part, record occurrence ID, drawing revision, material,
process, tolerances, inspection criteria and quantity. For each purchased part,
record manufacturer, exact part number, revision, datasheet and quantity. Keep
required, on-hand, installed and purchase quantities separate.
