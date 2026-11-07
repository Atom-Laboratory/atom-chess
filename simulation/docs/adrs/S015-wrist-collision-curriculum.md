# S015 — Wrist residual actions and progressive gripper collision training

## Context

The bounded wrist exists in the physical model but native IK and camera RL
encode five actuator commands and four residual actions. Full-gripper hull
assets were generated earlier but fingertip-only collision remains the default.

## Decision

Extend static IK mapping for a specified wrist angle by measuring the rotated
TCP offset in scratch kinematics and using the existing native planar solver.
Return six commands for wrist bundles. Add a fifth residual action for wrist
angle and six commanded-joint observations. Preserve the legacy spaces.

Expose full gripper collision as a separate build profile using the existing
mesh decomposition, with hashes recorded among bundle assets. Start wrist
learning with the isolated piece and fingertip contacts. Qualify complete
gripper hulls separately before crowded-board training. Keep failures visible.

Future obstacle rewards must compare camera observations of neighboring pieces.
Simulator piece poses and contacts must not supply camera-only task reward.
The wrist policy has different action and observation shapes, so train a fresh
policy unless explicit compatible feature transfer is implemented.

## Consequences

Static geometry supplies nominal trajectories and the camera supplies actor
images and reward. Full hulls are experimental CAD-derived convex parts with
documented concavity limitations. They do not establish hardware accuracy or
self-collision qualification. Wrist limits remain bounded to one revolution.

## Neighbor evidence and exploration

Obstacle pieces are retained as free rigid bodies in prepared fixtures. Task
success also requires the rectified images of their initial squares to remain
within an experimental visual-change threshold after retreat. The reward uses
a graded changed-pixel penalty. A blocked privileged-reward replay checks this
boundary. This does not establish continuous visibility or hardware safety.

A rate limit on the wrist residual prevents random policy samples from
continually resetting phase dwell. Unsmoothed failures remain preserved. Start
with a sparse neighboring piece and retain adjacent-piece failures for later
qualification rather than treating them as successful transfers.
