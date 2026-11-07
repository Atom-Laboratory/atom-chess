# Hardware workspace instructions

These instructions apply to `hardware/**` and to hardware tooling that reads its
data. Project-owner decisions and more specific instructions take precedence.

## Data integrity rules

1. Never invent component specifications, ratings, part numbers, pinouts, or
   quantities.
2. Never assume an owned component is installed.
3. Never map a simulated joint, actuator, link, or sensor to physical hardware
   without explicit confirmation and evidence.
4. Preserve the distinction between `confirmed`, `reported`, and `unknown`
   information. A report by a person is not independently verified evidence.
5. Keep physical availability (`owned`, `installed`, `planned`) independent from
   identification status (`complete`, `incomplete`, `unverified`).
6. Update both inventory and assembly data when physical hardware changes.
7. Keep generated artifacts in `hardware/generated/`; do not edit them as source.
8. Never declare an electrical design safe based on software or YAML validation.
9. Ask for missing critical information instead of guessing.
10. Preserve repository conventions, architectural boundaries, and existing
    historical evidence.

## Evidence policy

- Prefer repository-relative evidence paths.
- Identify the source of every non-null technical claim.
- Associate a datasheet only after its manufacturer and model match the physical
  component reliably.
- Do not silently promote reported information to confirmed information.
- Do not treat simulation parameters, product-family defaults, photographs of a
  similar item, or unit-test fixtures as physical measurements.

## Intended source relationships

- `inventory/components.yaml` is authoritative for component identity,
  availability, evidence, and known specifications.
- `inventory/assembly.yaml` is authoritative for which inventory items are
  installed and for evidence-backed physical-to-simulation mappings.
- A future KiCad project will be authoritative for electrical connectivity and
  electrical BOM generation. Inventory records may reference KiCad designators,
  but must not duplicate guessed connectivity.
- `simulation/mujoco` remains authoritative for the current mechanical
  simulation. Hardware data may map to its stable joint/actuator names only when
  evidence exists; it must not rewrite or reinterpret simulation geometry as
  physical calibration.

Changes spanning inventory, KiCad, firmware pin assignments, and MuJoCo mappings
must be reviewed by the relevant subsystem owners. Do not resolve discrepancies
by choosing one source silently; report them.
