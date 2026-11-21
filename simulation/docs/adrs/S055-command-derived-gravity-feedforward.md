# S055 — Derive gravity feedforward from issued commands

**Status:** Accepted (simulation command boundary; hardware calibration unqualified)

**Date:** 2026-11-21

**Decision owners:** Motion control, robotics, learning verification

**Related experiments:** EXP-0004

**Related findings:** RF-0004

**Supersedes:** Live-state bias input in the simulation MotionController

### 1. Context

The actor uses camera/task/command data, but MotionController.step added live
`sim.data.qfrc_bias` to arm commands. That includes simulator state unavailable
to the real camera-only arm. Actor observation isolation alone therefore did
not establish an observation-independent low-level command path.

### 2. Evidence

The historical controller reads live generalized bias forces at every control
interval. Those values depend on measured qpos/qvel. Simulator truth is allowed
for evaluation and safety, not for deciding deployable movement coordinates.

### 3. Decision

Compute static gravity bias on a separate scratch model state at the validated
desired command, with zero velocities and default object states. Apply only the
existing three arm-actuator compensation terms using compiled gains. Keep
actuator control bounds and reference velocity limiting. Never read live
simulation data while constructing the feedforward command.

### 4. Alternatives considered

Removing compensation changes the existing controller's gravity support.
Using measured joint positions or inferred contact forces would introduce extra
sensor requirements. A command-derived static model is available on hardware
once its masses, directions and actuator mapping are calibrated.

### 5. Technical rationale

Static gravity is computable from known geometry and issued coordinates. It
does not estimate actual joint tracking, payload or contact forces. Tracking and
collision truth may still stop simulated execution as privileged safety checks;
that does not authorize those quantities as actor observations or target inputs.

### 6. Implementation

MotionController owns a scratch MjData and an explicit `command` construction
method. Tests perturb live robot/object position, velocity and bias force while
requiring identical commands for identical issued targets. Canonical physical
trials must be rerun; old measurements remain attributed to the old controller.

### 7. Consequences

The controller no longer compensates live velocity bias or unknown payload.
Static model assumptions remain experimental. This fixes one truth dependency;
it does not qualify camera-only outcome verification or real servo homing.

### 8. Verification

Run command-boundary unit tests, existing local-supervisor checks, then a
canonical isolated grasp/lift/hold trial under unchanged geometry/solver inputs.
Record the new source identity and separate any changed outcome.

### 9. Research relevance

Deployable policy commands and privileged simulation diagnostics must remain
distinct at every layer, including low-level gravity support.

### 10. Report-ready summary

ATOM replaces live simulator bias-force feedforward with static gravity computed
from issued actuator coordinates on a scratch state. The command construction
is independent of live simulator joint, object and velocity state. Hardware
calibration and visual-only outcome verification remain separate open gates.

### 11. References

- [Motion controller](../../mujoco/src/atom_mujoco/motion_controller.py)
- [Research progress](../../../docs/research/RESEARCH_PROGRESS.md)
