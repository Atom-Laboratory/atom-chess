# S010 — Shared-physics playground with truthful acceptance gates

Date: 2026-11-05. Status: accepted incremental implementation.

Reuse the existing MuJoCo model and Simulation backend for headless tasks and
the native viewer. Add numerical IK preflight on separate MjData and explicit
failure results before executing infeasible waypoint sequences. Keep baseline
and policy selection distinct: no policy checkpoint means RL unavailable.

The required standard-board E2/E3 test currently fails preflight with ~0.0891 m
best residual. Do not change physical dimensions or placement silently to pass.
This numerical failure does not prove global unreachability. CAD/calibration
must resolve the mismatch before full-move acceptance.

Initial GUI/API is intentionally documented as incomplete: FEN/scenario editing,
nonblocking task controls, fault injection, full sensor/FSM integration and learned
policy comparison remain pending. Simulation truth is labeled oracle and never
reported as camera verification. No Chess Core board commit is performed.
