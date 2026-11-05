# P010 — Conservative swept-path preflight and collision diagnostics

Date: 2026-11-05. Status: implementation in progress.

## Context

P009 demonstrates a specific physical capture but waypoint IK alone cannot prove
collision clearance. Current convex robot meshes can fill mechanical gaps. The
profile disables self-collision response and the moving finger meshes have only
pad proxies. Those limitations cannot be hidden by a successful final pose.

## Decision

Introduce a separate geometric preflight on cloned MjData. Enumerate collision
geometry explicitly, including otherwise disabled finger visual hulls for a
conservative envelope. Check robot/environment and nonadjacent articulated links
independently of physics masks. Same welded rigid bodies and immediately connected
joint bodies are structural exclusions; record them in the report.

For each joint-linear trajectory interval, use signed geom distances at its
midpoint and a conservative bound on surface displacement over the interval.
For a hinge the bound is angular travel times an upper bound on chain radius;
for a slide it is linear travel. A pair is clear only when separation exceeds
both bodies' displacement bounds plus configured clearance. Otherwise subdivide;
actual overlap or unresolved intervals fail closed. A held piece follows the
grasp-frame rigid transform and participates in checking. Allowed pad/selected-piece
and selected-piece/support contacts are explicit phase-specific exceptions.

Preflight covers approach, descent, closure, lift, transport, placement, opening
and retreat before any controller step. Default execution requires clearance.
An explicitly named diagnostic mode retains prior manipulation experiments but
labels results as unchecked and is not an RL eligibility path. Runtime contact
monitoring complements preflight; neither certifies hardware or dynamic uncertainty.

## Alternatives and consequences

Checking endpoints misses intervening collisions. Fixed dense sampling alone has
no between-sample guarantee. Ignoring initial robot overlap would hide geometry
defects. Conservative hulls may therefore block otherwise plausible motion until
collision geometry is repaired using actual mesh evidence. Do not weaken the
gate or invent CAD fidelity to make a demo pass.

The bound concerns the nominal joint-linear geometric path and rigid grasp
assumption, not arbitrary actuator deviations. Runtime monitoring and measured
tracking margins remain necessary; no policy or hardware safety certification is
implied. Source: MuJoCo official computation/geom-distance documentation,
https://mujoco.readthedocs.io/en/latest/computation.html and
https://mujoco.readthedocs.io/en/3.10.0/APIreference/APIfunctions.html#mj-geomdistance.
