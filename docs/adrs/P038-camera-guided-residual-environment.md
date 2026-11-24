# P038 — Camera-guided residual manipulation environment

## Context

P037 provides a persistent native image boundary. The legacy v3 environment uses
oracle reset/IK and an isolated lift task. P015 exposes acmotion planning only for
a fixed E2/E3 demonstration. A controlled one-piece transfer now has explicit
authorization before full chess captures or graveyards.

## Decision

Add a small native motion C ABI backed by the existing MotionPlanner and
InverseKinematics classes. Derive the simulation robot mapping from static model
kinematics and verify it against forward kinematics. Generate one-piece scenes
in new directories, preserving original meshes, joints and piece dimensions.

Implement a new Gymnasium environment with P037 actor features, nominal C++
waypoints, nonaccumulating bounded Cartesian/aperture residuals, swept collision
supervision and independent simulator reward. Explicit configured initial poses
and a fixed camera replace oracle resets. The actor receives only copied numeric
features. Image-only multi-frame evidence remains distinct from oracle success.

Provide fresh-run/resume/evaluation launchers and execute a short PPO smoke test.
Smoke completion validates the training cycle, while measured task success and
visual confirmation remain separate report fields.

## Consequences

The simulation robot mapping, contact proxies, action bounds and event thresholds
remain explicitly experimental and model-derived. Initial scope is one known
piece with fixed source/target. The policy cannot modify logical chess state.
Historical v3 data and all current local work remain preserved. No commit or push.
