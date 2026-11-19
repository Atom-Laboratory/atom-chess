# S022 — Learn continuous motion decisions with an independent supervisor

## Context

The full-board sweep rejected a finite family with fixed grasp Z and
intermediate descent height. Residual PPO retains the nominal waypoint
sequence and a small correction range. These observations do not establish
global physical infeasibility. The next experiment must allow different
pickup heights and paths without supplying a winning trajectory.

## Decision

Create a separate experimental environment. The actor chooses Cartesian
velocity, wrist velocity, finger-slide velocity, elbow branch, and a bounded
action duration. Each action persists for its chosen control intervals.
The host predicts the current TCP from commanded joints and static geometry,
then requests native AC:Motion IK for the chosen displacement and elbow.
Velocity scales derive from the model's link geometry and joint speeds.
There are no target manipulation waypoints or automatic grasp/lift phases.

Use two consecutive rectified images and host/task context. Keep all
simulator-derived physical feedback in reward, safety and diagnostics.
The supervisor may inspect live simulation state, rejects invalid or
unresolved swept segments, and stops after unexpected dynamic contact,
toppling, or a disturbed scene. Pre-motion rejection permits another action.
Physical recovery after unknown state remains gated by reconciliation.

Use PPO for the first interface experiment to limit algorithm changes
relative to the residual baseline. SAC's replay and entropy objective and
recurrent PPO are explicit alternatives for later matched comparisons.
Short stacked observations are a bounded-memory first test. Action duration
is chosen by the actor, so discounting is initially per decision.

The initial 32-decision pilots rejected every sampled request before the
swept check. The revision maps wrist and finger speeds to available travel
and shortens infeasible Cartesian requests along the requested direction
before collision validation. A neutral elbow control preserves the current
branch. Explicit branch changes still require native IK, speed and sweep
validation. This projection has no task target or learned policy state.

## Watch and throughput

Keep a certified collision pair out of descendant sweep intervals. The
parent certificate covers both children. In the optimized mode, refresh
only kinematics for distance queries. Provide an optional native viewer
with a private state copy, alongside the camera diagnostics. Select the
PPO compute device independently of the simulator and record the selection.
Allow the operator to retain the native viewer after a completed run using
an explicit flag. The report is saved before the viewer waits for dismissal.

## Consequences

The action and observation spaces differ from the archived residual policy.
A fresh policy is required for this first experiment. Curriculum levels must
share this interface if policy transfer is to preserve meaning. Learned
options, visual grip tracking, transport, placement, physical recovery and
generalization remain separate acceptance gates. A short training run tests
the interface and learning loop, not autonomous manipulation success.
