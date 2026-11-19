# Hardware verification and release

Record each check with the hardware revision, component IDs, test configuration,
operator, date, instrument, expected result, actual result and evidence path.
Use `pending`, `pass` or `fail` to distinguish status. The [evidence
policy](../evidence/README.md) defines where to store records.

| Gate | Evidence for acceptance | Baseline |
| --- | --- | --- |
| Inventory identification | Readable labels and model-matched datasheets; count and identify lot members | Pending |
| Mechanical assembly | Revisioned CAD and measured axes, travel, zeros, endstop locations, clearances and TCP | Pending |
| Electrical design | Reviewed schematic, design BOM, connector and harness schedule, current/thermal budget, protection and ERC disposition | Pending |
| Physical inspection | As-built photos, continuity/polarity checks and wiring reconciliation against the released schematic | Pending |
| Electrical bench validation | Reviewed test results for supply domains, load, faults and independent stop behavior | Pending |
| Motion and recovery | Measured direction/conversion, homing, travel, stop, link loss and restart behavior for each axis | Pending |
| Simulation correlation | Identified bundle and measured reference poses with errors against agreed limits | Pending physical measurements |

Collect labels and connector photos first. Record each physical mounting location
and traceable component ID. For the harness schedule, record source and
destination designators, pin names, signal or rail, conductor, connector and
revision. Resolve discrepancies against the schematic before releasing the
schedule. For each rail, record the specified operating envelope and the
measured idle, sustained and transient load with the test conditions.

A release should identify the Git commit, assembly revision, CAD and KiCad
revisions, BOM exports, harness schedule, firmware configuration, MuJoCo bundle
manifest and reviewed test records. Assign open requirements to owners and retain
the evidence for each gate with the release.
