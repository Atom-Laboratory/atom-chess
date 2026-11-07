# ATOM hardware engineering baseline

Use this package with the [hardware inventory](../inventory/components.yaml) and
[assembly record](../inventory/assembly.yaml). The inventory records possession
and identification. The assembly records installation and mappings. The future
KiCad revision will own electrical connectivity and its design BOM.

| Deliverable | Scope |
| --- | --- |
| [BOM and parts registers](bom.md) | Inventory, installed snapshot and mechanical source register |
| [Architecture and interfaces](architecture.md) | Logical system, power design boundaries and simulation mapping |
| [Verification and release](verification.md) | Evidence to collect, acceptance criteria and release gates |
| [MuJoCo integration](../mujoco-integration.md) | Supported bundles and headless verification |

The [October engineering audit](../../docs/audit/2026-10-30/README.md) and
[legacy electronics diagram](../Architechture/Eletronic/v0.0/) are historical
references. Preserve them with their original assumptions and compare them with
current inventory and evidence when revising the design.
