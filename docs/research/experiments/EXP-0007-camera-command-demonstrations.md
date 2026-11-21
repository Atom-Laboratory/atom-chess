# EXP-0007 — Camera/command demonstration export and independent Watch

Date: 2026-11-21. Decision: S060. Stage: isolated expert dataset infrastructure,
not neural-network training. Inputs are CPU-verified EXP-0006 candidates.

## Question and protocol

Can successful physical trajectories be preserved with causal camera observations
and issued commands, while keeping privileged physics outside actor inputs?
Re-execute each complete command tape on canonical MuJoCo. Require exact matching
qpos/qvel and the existing held-lift criteria. Render a scratch copy before each
50-step action chunk; do not forward or modify the live solver state. The original
1920×1440 fixed camera is resized to 96×96 RGB, with three originals retained.
Source XY is bound to the signed native camera reference. The sixth actuator is
the bounded gripper wrist; all six issued actuator commands are preserved.

## Results

| Reference seed | Entry scope | Physics steps | RGB/action chunks | CPU replay max qpos/qvel difference | Minimum held rise | Maximum held drop |
| --- | --- | --- | --- | --- | --- | --- |
| 970200 | Original isolated entry, hash-bound CEM winner | 8,049 | 161 | 0 / 0 | 43.454 mm | .312 mm |
| 970201 | New isolated entry after failed first attempt and headless retry | 7,312 | 147 | 0 / 0 | 44.162 mm | .311 mm |

Both re-executions passed the unchanged one-second held lift, bilateral contact,
settling/upright and forbidden engine-contact checks. The first headless export
took 6.76 s; this is export time, not policy training throughput. No previous
failure is relabeled: EXP-0006 retains the first camera-expiry entry rejection.

The initial combined exporter/Watch process exported successfully but exited with
native Windows access violation 3221225477 when opening/using passive Watch.
A separate-process Watch was implemented; its result is archived separately.
Do not confuse presentation failure with physical success or infer its root cause
without a controlled native/graphics investigation.

## Evidence, reproduction and boundaries

Use [the module README](../../../simulation/mujoco/accelerated/README.md#verified-cameracommand-demonstrations-and-watch).
Small reports, per-frame CSV and representative camera images are archived in
`simulation/mujoco/accelerated/reports/EXP-0007`; full NPZ archives and immutable
executed sources remain in the referenced local run directories. Reports contain
artifact hashes and exact camera/model/config/reference identities.

`actor.npz` is strictly allowlisted. `actions.npz` carries exact command chunks
and validity lengths. `privileged.npz` separately contains actual states/contact
measurements for reset reproduction, reward and auditing. Camera images precede
their action interval; `issued_command` is command history, not an encoder.

These 308 frames represent **two** isolated physical entries, not 308 independent
demonstrations. One entry supplies a possible development split and the other a
small held-out split; further independent scenes/seeds are needed. The original
view can be occluded by the arm. Source geometry is frozen at entry, not updated
from hidden simulator coordinates during lift. No learned grasp, placement,
occupied-board manipulation, camera-only success verifier or hardware transfer
is qualified here.
