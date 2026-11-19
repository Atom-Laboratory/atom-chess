# S029 — Qualify a native wrist-aware approach before local learning

## Context

M1 found fixed C++ transfer waypoints, separate Python collision checking,
five-command legacy automatic interfaces, failed full-board descent endpoints
and an unqualified dynamic capture. NativeMotion, the six-command wrist model,
camera localization, SweptChecker and MotionController are reusable. The M2
increment must demonstrate actual travel from park, with enabled collision
checking and explicit rejection evidence.

## Decision

Add a motion-intelligence approach adapter that delegates Cartesian waypoint
generation to the existing native MotionPlanner and IK to NativeMotion. Build
candidate travel using the high-clearance rows of that plan. Test the direct
joint path first, then staged travel and different in-limit wrist/elbow
choices. Every complete candidate path must pass the existing swept checker.
Preserve all rejected candidates and their exact phase/pair/limit evidence.

Derive candidate clearance heights from the existing scene collider bounds,
the tool's lower extent relative to TCP, and the checker's existing clearance.
Sample alternative heights in board-pitch increments within the native IK
Z limits. These are deterministic search choices with model provenance.
They do not establish physical calibration or a learned grasp height.

Use native RGB source localization and calibrated static board geometry for
task endpoints. Keep model-based collision supervision and simulation feedback
explicitly separate from future actor inputs. A plan must bind the model,
starting configuration and observed scene identity. Detect changes before
execution and report partial execution as a reconciliation condition.

Use the existing controller and synchronized bounded interpolation, with
runtime contact, toppling, neighbor displacement and tracking checks. Execute
the approach and a separately checked retreat on the actual simulation. A
valid random pose alone cannot pass this gate. Report nominal local-region
bounds and their exact certification scope. Contact manipulation and a
carried-object transport require their own additional checks.

The first maximum-velocity linear traversal failed after 4 ms: the second
finger exceeded its upper bound by 0.1174 mm during arm acceleration, above
the unchanged 0.05 mm numerical excursion threshold. Replace the time law
with a quintic rest-to-rest profile and an explicit default velocity fraction
of 0.25. Its peak normalized derivative is 1.875, included when computing
duration. This is an experimental execution setting, not a calibrated motor
acceleration limit. Keep the geometric path, limits, contact checks and
thresholds unchanged. Bind dynamics and controller state into stale-plan
checks as well as geometry. Record the timing setting in every new run.

Provide a dedicated documented qualification entry point with native Watch
enabled by default. Keep the five-command legacy interfaces identified as
legacy. M2 does not connect RL, perform a grasp or silently migrate their
schemas. Subsequent milestones provide the shared handoff contract.

## Alternatives

Changing the original eight transfer waypoints would change existing callers.
Disabling gripper colliders or loosening clearance would change the experiment.
A second IK solver would duplicate native functionality. Introducing a general
sampling planner before testing complete native approach proposals would add
an algorithm and dependencies without establishing the immediate baseline.

## Consequences and acceptance

The bounded candidate family can fail, in which case M2 reports the blocker
without claiming global infeasibility. The scene remains experimental. At
least one actual collision-checked wrist-aware approach is required, with
full rejection diagnostics, reproducible configuration/seeds and relevant
regression tests. Distinguish approach/retreat success from grip, held-object
transport, complete transfer and hardware qualification. Stop and report M2
before connecting a learned policy.
