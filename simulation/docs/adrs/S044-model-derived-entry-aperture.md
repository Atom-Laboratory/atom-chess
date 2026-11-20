# S044 — Prepare the aperture before local reach in crowded positions

Status: experimental. Date: 2026-11-20.

## Context

The S042/S043 populated-board reference reached 19.93/18.85 mm instead of the
17.5 mm threshold. Its 48 mm fully open gripper was then rejected near the D2
pawn. Holding the maximum aperture through a crowded reach is unnecessary.
The existing deterministic movement pipeline already derives a pregrasp opening
from the compiled fingertip and selected stem proxies.

## Decision

Offer an opt-in approach preshape using that same static model-derived aperture.
Plan and screen the actual simultaneous finger/arm path and retain the aperture
through contact-free XYZ reach. The initial park remains unchanged. Fingers do
not close on the piece; selected-pad contact remains forbidden in v8.

Compute the geometric aperture from model qpos0 with open fingers, not live joint
or piece poses. Gap along the pad normal is a relative geometric property, and
the selected stem radius is a known model parameter. Keep the existing 3 mm side
gap as an explicitly experimental proxy assumption, not a hardware measurement.

## Alternatives and consequences

Removing neighbor pieces or gripper collisions is rejected. Training indefinite
rollouts against a maximum-aperture dead end wastes exploration. A planned
preshape reuses the deterministic pipeline and is independently collision-checked.
Changing aperture changes the start distribution: retain the configuration hash,
use explicit compatible weight transfer and repeat before/after and held-out
evaluation. This does not qualify grasping, friction, lift or physical hardware.
