# S025 — Qualify autonomous learning from safe randomized starts

## Context

The version 2 autonomous pilot starts about 0.33 m from the pawn and grants
reach success only within a mean pad clearance of 1.5 mm. The 128-decision
pilot had 106 accepted commands and no successful episode. Reset also invokes
the residual environment's waypoint construction and destination appearance
calibration, although autonomous reach/grasp/lift does not consume them.

## Decision

Build the autonomous scene from the existing simulation, camera, AC:Vision,
AC:Motion, controller and collision components. Give it a reset procedure
with cached synthetic calibration images and no manipulation waypoints.
Measure piece bounds from the collision primitives used by physics. The
reward evaluates distances to these same primitives.

Version the actor schema. Add expected piece kind/color from task context and
source XY estimated from RGB, expressed relative to forward kinematics of the
last commanded joints. Include target visibility and age. The static
board-to-robot transform is experimental calibration. Image observations,
task context and host commands are the only actor inputs. Simulator contacts,
poses and clearance stay in reward, supervision and diagnostics.

Define a configurable reach neighborhood in board-square units. Default to
one square for the first reach experiment. Keep grasp and lift as separate
physical criteria. Report the threshold with every result. A larger reach
neighborhood alone cannot qualify grasp, lift or full-board manipulation.

Optionally sample initial commands around the visually localized source.
Reject starts violating joint bounds, IK, geometric clearance or perception.
Keep orientations and approach directions variable. Initialization resets
the simulation and supplies no trajectory to the actor. Evaluate the same
distribution on disjoint seeds and retain evaluation from the parked start
as a separate harder condition. Advance the start radius only after a
declared held-out gate. Full-board and isolated-object results stay distinct.

Bound Cartesian exploration by both existing joint-speed-derived limits and
the distance of one board square per maximum-duration action. Keep wrist,
fingers, elbow and duration under policy control. Log actual physical action
scales. A new environment version prevents loading incompatible old actors.

Keep current hard collision supervision while validating this increment.
Penalized non-toppling contact requires a separately explicit supervision
contract. Reset, stop and training failure must remain visible in logs.

## Alternatives

Longer training with the old reset retains its cost and difficult initial
distribution. Hand-selected successful trajectories would remove the
strategy-discovery question. Disabling collision checks would change the
physical task. Starting with a task-relative visual context retains useful
known calibration while reducing the burden on the image encoder.

## Consequences and acceptance

Run observation-isolation, action-effect, reward-sign, collision-boundary,
reset-diversity and checkpoint tests. Compare a fresh policy and trained policy
on held-out seeds. Record counts, distances, failures and component timings.
Overnight training requires stable resets, finite updates, verified saves,
and improvement over the fresh policy on the explicitly named stage.
Physical geometry and hardware deployment remain separate qualifications.

Curriculum learning from easier starting states motivates the experiment.
The sampling distribution here is a declared engineering baseline whose
benefit must be measured. [Florensa et al.](https://proceedings.mlr.press/v78/florensa17a.html)
