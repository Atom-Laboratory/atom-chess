# EXP-0004 — Canonical sustained lift and GPU recorded-control replay

Date: 2026-11-21. Decisions: S054, S055, S057. Stage: isolated deterministic
manipulation and backend replay. No RL policy or autonomous GPU vision was used.

## Hypothesis and protocol

Can the camera-localized canonical grasp still lift after removing the live
simulator bias-force input, sustain the lift for one second, and reproduce the
recorded controls on GPU? The canonical native planner/supervisor retains full
gripper colliders, gravity, existing experimental friction/mass, elliptic/10,
closing load factor 2.5, selected-finger hull margin zero, other margins 1 mm,
requested travel 1.5 piece heights and lift speed fraction .25. Seed: 970200.

Static feedforward derives from issued commands; simulator qpos/qvel and
contacts remain privileged verification/safety data. A passive recorder saves
full integration states at each physics boundary. Independent CPU transition
and continuous-control replay must match before GPU assessment. The GPU receives
the recorded command tape, not future privileged coordinates.

## Results

[VERIFIED-RESULT] Canonical seed 970200 completed lift and held it for 1.02 s
(51 control checks). Final measured rise was 44.687 mm; maximum sampled vertical
drop was 0.270 mm, below the predeclared 3 mm limit. Both contacts and settled
feedback persisted. All 11,030 recorded CPU transitions and continuous CPU tape
replay matched exactly.

| GPU worlds | Steps/world | Minimum held rise | Maximum held drop | Hold contacts | Prohibited engine contact steps | Cumulative capacity/iteration flags |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11,030 | 44.688 mm | 0.268 mm | retained | 0 | 0 |
| 16 | 11,030 | 44.688 mm | 0.268 mm | retained in all worlds | 0 | 0 |

A separate offline evaluation of preserved GPU states checked settled velocity
limits (.01 m/s linear, .15 rad/s angular), upright angle .15 rad and hold
criteria at every stored step. All 1/16 worlds passed. Maximum upright angle
was about .00313 rad; maximum hold linear speed about .00431 m/s. The original
report predates these added fields; separate outcome-audit files preserve that.

Single-world maximum open-loop qpos difference was 0.000279 in mixed model
coordinates; qvel difference .0300 in mixed velocity units. These are not all
Cartesian metres/velocities. Screening limits were .001 and .05; dimensional
per-field/single-step checks remain separate in EXP-0003. Accumulated contact
drift does not establish exact float64 GPU equivalence. GPU replay/diagnostic
kernel wall times were 5.53 s and 5.92 s for one/sixteen worlds, excluding CPU
verification/setup. These are not end-to-end training speedups.

## Negative result retained

The first replay failed before rollout: MJWarp uses a Warp `vec2i` contact geom
field, while the initial diagnostic kernel expected an integer matrix. That
adapter error was corrected; an actual CUDA multiworld contact/forbidden-pair
test passed. The original failed run/traceback remains archived. It was not a
physical grasp failure or MuJoCo engine defect.

## Reproduction, artifacts and limitations

Use the [native diagnostic README](../../../simulation/mujoco/examples/qualify_hybrid_approach/README.md)
with `--lift-hold-s 1 --record-physics`, then the
[GPU replay README](../../../simulation/mujoco/accelerated/README.md).
[Small evidence package](../../../simulation/mujoco/accelerated/reports/EXP-0004)
contains canonical provenance, transition hash, raw GPU reports, derived outcomes
and the type failure. Large NPZ files remain in ignored local runs. Immutable
source snapshots identify precommit diffs; canonical source was over f90de4a
and the recording implementation is now bde833a.

Worlds replay the same inputs: 16 copies are not 16 independent generalization
trials. Engine masks do not reproduce all independently checked robot self pairs;
canonical swept validation remains distinct. This does not qualify arbitrary
new paths, crowded insertion, camera-only outcome verification, learned grasp,
capture/transport or real hardware.
