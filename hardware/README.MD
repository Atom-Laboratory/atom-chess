# ATOM Hardware Workspace

This directory is the engineering record for ATOM Chess hardware. Phase 1
establishes traceable inventory and assembly data; it does **not** define a
safe electrical design or claim that the simulation is physically calibrated.

The [engineering baseline](docs/README.md) contains the BOMs, mechanical source
register, architecture diagrams and verification gates.

## Phase 1 layout

- [`inventory/components.yaml`](inventory/components.yaml): components owned or
  planned, including identification confidence and evidence.
- [`inventory/assembly.yaml`](inventory/assembly.yaml): explicit relationships
  between inventory, the physical assembly, and simulated joints.
- [`inventory/datasheets/`](inventory/datasheets/README.md): model-matched
  datasheets only.
- [`evidence/`](evidence/README.md): photographs, labels, measurements, and
  assembly evidence.
- [`generated/`](generated/README.md): reproducible reports; never edit these as
  source data.
- [`mujoco-integration.md`](mujoco-integration.md): relationship to the existing
  MuJoCo simulation.
- [`AGENTS.md`](AGENTS.md): rules for future automated contributors.

Existing historical diagrams, platform notes, onboarding material, and CAD files
remain in their original directories. They are evidence and design history, not
automatically verified inventory records.

## Validate the workspace

The `.yaml` files intentionally use the JSON-compatible subset of YAML 1.2 so
validation requires only Python's standard library:

```bash
python tools/hardware/validate.py
```

Regenerate the checked-in report with:

```bash
python tools/hardware/validate.py --report hardware/generated/validation-report.txt
```

Run the commands from the repository root with Python 3.12. The validator
prints a summary and individual findings, exits with code 1 on validation
errors, and exits with code 0 when there are only warnings or no findings.
Review warnings before relying on inventory data. Electrical validation
requires separate engineering evidence.

For a simulation compatibility check, follow the prerequisites and run the
headless bundle inspection in the [MuJoCo integration guide](mujoco-integration.md).

## Updating hardware data

1. Add a stable, lowercase `snake_case` component ID. Use one record per
   individually traceable item; use a lot record only when individual identity
   and quantity are unknown.
2. Set physical `status` independently from `identification.status`.
3. Record unknown values as `null`. Never infer a model or rating from appearance.
4. Store each specification as `value`, `unit`, `confidence`, and `source`.
   Confidence is `confirmed`, `reported`, or `unknown`.
5. Add evidence under `evidence/components/<component-id>/` and reference its
   repository-relative path. Record who/what supplied the fact.
6. Add a datasheet only after manufacturer and model are matched reliably.
7. Update `assembly.yaml` only when installation or mapping evidence exists.
8. Run the validator and review every warning before requesting review.

## Roadmap (not implemented in Phase 1)

### Phase 2 — Electrical design

Create an owner-approved KiCad project with multi-sheet schematics, power
distribution, controllers, drivers, sensors, endstops, connectors, BOM exports,
ERC, and PDF/SVG outputs. KiCad will become authoritative for electrical
connectivity. Inventory data must not be used as a substitute for schematic and
engineering review.

### Phase 3 — Engineering workspace

Create a local visual interface for inventory, evidence, datasheets, BOM,
schematics, wiring, MuJoCo integration, and validation reports. No dashboard is
implemented in this phase.

## Licensing

Hardware is governed separately from the repository's MIT-licensed software.
See [`LICENSE`](LICENSE) and the root project licensing notice before copying,
publishing, or manufacturing from hardware artifacts.
