# S060 — Camera/command demonstrations from independently verified physics

**Status:** Accepted (isolated research dataset; no manipulation-policy admission)

**Date:** 2026-11-21

**Decision owners:** Perception, manipulation verification, ML research

**Related experiments:** EXP-0007

**Related findings:** RF-0001

**Supersedes:** None

### 1. Context

EXP-0006 found isolated close/lift/hold command sequences and verified a frozen
candidate on one additional camera-localized entry. Successful physics must be
preserved before imitation or RL can use it. Copying simulator joint/object
positions into an actor dataset would violate the single-camera sensor boundary.
The first additional entry also expired its camera observation while watched;
offline viewing must remain separate from control timing.

### 2. Evidence

The retained candidate NPZ contains complete initial integration state, issued
actuator commands, phases and canonical CPU qpos/qvel. The signed native camera
handoff supplies source XY; no new target coordinates need to come from physics.
Both CPU/GPU held-lift criteria passed, but occupied-board entry remains open.

### 3. Decision

Export a demonstration only after fresh canonical CPU re-execution matches the
stored CPU trajectory and passes the unchanged contact/lift/hold criteria.
Reconstruct every motion through mj_step with the original controls. Never
attach the object, set its pose during execution or fabricate a grasp.

Store actor observations in `actor.npz`: RGB before each action interval,
previously issued actuator command, signed camera source XY, source/target square
encoding, and planned phase. Store command labels in `actions.npz`. Store all
physics truth, contacts, initial integration state and full-resolution controls
separately in `privileged.npz`. Name fields explicitly; no qpos/qvel/contact field
is permitted in actor inputs. Issued commands are not measured joint positions.

Render the original configured camera into a scratch display state, then resize
RGB for learning. Save representative full-resolution images. Rendering must
not call forward on the live physics state or alter its hidden solver state.
Record frame/action indices so each image precedes its corresponding command.

Provide a separate, bounded Watch replay of the same validated command tape.
The export worker must exit before a new process opens Watch: the first combined
offscreen/export/passive-viewer process exited with Windows access violation
3221225477 after successful export. Keep that failed launch as infrastructure
evidence; it is not a failed physical grasp or proof of the native crash's cause.
It is replay/verification, not live optimization or RL. It may be replayed at a
different display speed without changing physics timestep. Close it automatically
after the finite replay; the user may interrupt it earlier.

### 4. Alternatives considered

Treating a report's success flag as sufficient would admit corrupted/mismatched
artifacts. Training directly from qpos or the target object's pose leaks sensors
unavailable on hardware. Rendering all candidate worlds wastes resources. Watching
inside camera-age-sensitive control couples presentation and safety timing.

### 5. Technical rationale

Pre-action RGB and issued-command history can exist on hardware. Simulation truth
remains useful for labels, reset reproduction and reward/safety auditing, while
separate archives make accidental observation leakage testable.

### 6. Implementation

Add an export/replay CLI with fresh immutable-source EXP-0007 runs, model/config/
camera/reference/tape hashes, exact trajectory comparison, strict actor allowlist,
control intervals aligned to physics steps, per-interval CSV and artifact hashes.
Use the canonical environment's existing Pillow/MuJoCo dependencies. Bound physics
steps, output frames, image dimensions, wall time and replay speed/repeat count.

### 7. Consequences

These are isolated Stage A expert demonstrations, conditional on successful
native entry, not generic transfers or a learned grasp. Frame count is not
independent sample count. Split future training/evaluation by reference/run,
never randomly by neighboring frames. Camera-derived source geometry is frozen
from entry, not refreshed after occlusion; online re-perception is a later gate.

### 8. Verification

Test observation leakage rejection, command history, pre-action alignment and
hold criteria. Export and Watch an actual accepted frozen candidate. Fail on
trajectory/model/reference mismatches or numerical warnings, retaining diagnostics.

### 9. Research relevance

The exporter supplies traceable successful demonstrations and an explicit actor/
privileged boundary for later imitation and reinforcement learning comparisons.

### 10. Report-ready summary

ATOM records pre-action camera/issued-command demonstrations from independently
re-executed physical grasps. Privileged physics remains a separate audit artifact.
The exporter does not establish a policy's accuracy or occupied-board feasibility.

### 11. References

- [EXP-0006](../../../docs/research/experiments/EXP-0006-isolated-cem-command-search.md)
- [Complete physics recording](S057-recorded-physics-and-sustained-lift.md)
- [Camera reference binding](S058-bounded-isolated-cem-grasp-pilot.md)
