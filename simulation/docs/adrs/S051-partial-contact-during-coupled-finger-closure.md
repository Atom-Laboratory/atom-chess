# S051 — Allow loaded partial contact while closing coupled fingers

Status: simulation local supervision. Date: 2026-11-21.

## Context

In the elliptic/10 trial, closure stopped at the first pad contact with a
51.6 micrometre finger tracking error against a 50 micrometre position tolerance.
The issued command had not yet reached the requested closing preload. The
supervisor allowed force-limited finger tracking only after bilateral contact,
preventing closure from proceeding through the normal first-contact stage.
The synthetic model mechanically couples the two finger slide coordinates.

## Decision

During `GRASPING` only, accept contact-loaded finger tracking when at least one
pad contacts the selected piece. Preserve correct error direction, compiled
force caps, bounded finger velocity and full arm/wrist tracking. Because the
finger coordinates are coupled, the loaded-coordinate check applies to both
fingers; it does not label the other pad as touching. Outside `GRASPING`, retain
the bilateral requirement. Pass the phase explicitly through preconditions,
settling and execution, for deterministic and admitted-policy calls alike.

## Alternatives and consequences

Increasing all tracking tolerances would also weaken free-space arm tracking.
Bypassing contact checks would hide physical failure. This change instead
distinguishes closing under unilateral load from a confirmed grasp. Sustained
bilateral contact is still required before lift, and lost bilateral contact
during lift still stops execution. Non-target contacts, force violations, wrong
tracking direction and arm/wrist errors retain their existing failure behavior.
The contact signal remains simulation safety/verification data, not an actor
observation or camera-derived command target. Hardware contact handling remains
unqualified.
