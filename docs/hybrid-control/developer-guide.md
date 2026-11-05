# Hybrid control implementation and phase status

Date: 2026-11-05. This is an incremental implementation, not a completed
physical chess robot. No neural model or trained-policy benchmark exists yet.

## Implemented components

`simulation/mujoco/src/atom_mujoco/supervision.py` provides immutable MoveTask
and Evidence records, SQLite TaskLedger and an evidence-gated Execution state
machine. It is transport-independent and does not send motor commands or mutate
Chess Core. It must not be advertised as a hardware safety controller.

New task IDs are persisted and claimed before work can proceed. Identical IDs
return persisted status; changed payloads are rejected. In-progress duplicates
and restarted tasks require reconciliation instead of automatic physical replay.
Sequence numbers, timestamps, source roles, board revision and signal sets gate
each transition. Simulation oracle sources require explicit allow_oracle=True.
ACK/DONE alone cannot satisfy grasp or final-board gates. Future sensor adapters
must compute the asserted signals; arbitrary callers are not trusted sensors.

Cancellation/timeout enters ABORTED; revision conflict and faults enter FAILED
with intervention_required. No automated recovery trajectory is implemented:
the caller must stop the actual controller before claiming physical abort.
Watchdog polling requires the caller to call advance with a monotonic time;
this library is not an independently running watchdog. Sensor dwell/fusion,
authentication, durable event history and distributed execution are pending.

## Reproduce locally

From Windows PowerShell at the repository root:

```powershell
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy -m pytest simulation/mujoco/tests/test_supervision.py -v
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
$output = 'simulation/mujoco/runs/baseline-' + [guid]::NewGuid().ToString('N') + '.json'
& $atomPy simulation/mujoco/examples/evaluate_joint_baseline.py --bundle simulation/mujoco/runs/interactive-chess-v6 --seed 7 --trials 5 --output $output
```

The baseline evaluates 4 seconds per randomized joint target in a restricted
diagnostic range, records per-axis errors, limit excess and robot contact steps.
It is not IK-based Cartesian reaching, pickup success or generalization evidence.
No aggregated error mixes radian and metre units. Keep the output and bundle
with the commit/configuration. Repeated outputs require fresh names.

## Phase gates and remaining work

| Requested phase | Current result / next evidence |
|---|---|
| 1 Audit | Repository audit and architecture proposal delivered in README |
| 2 Architecture/instrumentation | Task/evidence/ledger/FSM implemented and unit-tested; live sensor adapters and independent supervisor pending |
| 3 Simulation | Existing gravity/contact/free pieces and isolated grip tests pass; physical fidelity and complete gripper/J3 unresolved |
| 4 Baseline | Reproducible joint-tracking evaluation added; full deterministic task controller pending geometry/reachability checks |
| 5 RL | Episode hooks exist; spaces/reward/algorithm comparisons and training pending validated manipulation baseline |
| 6 Generalization | Evaluation partitions specified; learned policy/held-out manipulation results absent |
| 7 Sim-to-real | Calibration plan specified; measured linkage/TCP/masses/inertia/actuation/latency data missing |
| 8 Embedded inference | No exported policy; no attached SBC benchmark interface or measured resource data |
| 9 Integration | Logical contracts implemented; no live Chess Core orchestration/vision/serial bridge |
| 10 Physical tests | Blocked: firmware configured=false, GPIO=-1, conversions=0; measured feedback and stop validation absent |
| 11 Documentation | Current implementation and blockers documented; training/export/install commands cannot be supplied before those tools exist |

Do not skip physical validation by randomizing invented ranges. Next independent
software work is sensor-oracle adapters, a calibrated-frame reachability audit,
full deterministic baseline and fault-injected integration tests. Then define a
Gymnasium environment, evaluate candidate algorithms on fixed budgets and document
why one is selected. The owner must be able to inspect/reproduce each choice.

## Hardware/calibration handoff

Before physical phases, obtain measured joint zeros/signs/limits and homing,
link/TCP/gripper geometry and servo-opening mapping, motor conversions and force
limits, sensor types/wiring/sample rates, independent stop behavior and camera
calibration/occlusion/confidence. Configure firmware from these records only.
Record each measurement with units, instrument, revision and uncertainty.

Before choosing an SBC/runtime, inventory exact device models/RAM/OS and workloads.
Benchmark identical exported policy inputs across CPU runtimes, verifying numerical
and action parity before measuring p50/p95/p99 latency, RSS and CPU offline.
No physical or on-device result can be inferred from workstation tests.
