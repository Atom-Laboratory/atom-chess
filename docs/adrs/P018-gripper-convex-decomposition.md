# P018 — Gripper convex decomposition

Replace whole-finger convex collision envelopes with CoACD-derived parts of
hand1, hand2 and gripper_back STL assets. Retain the localized contact pads.
The source millimetre coordinates and attachment translations are preserved.
Generated OBJ hulls are shared assets attached to each original moving body.
The manifest binds decomposition to source SHA256. Visual assets remain distinct.

Generation used CoACD 1.0.14, threshold 0.05, maximum 24 hulls, preprocessing
resolution 30, sampling resolution 1500, MCTS iterations 30, nodes 10, depth 3,
and seed 0. These parameters describe an approximate decomposition rather than
measured manufacturing tolerances. Runtime does not need CoACD installed.
Existing friction, masses and inertias remain experimental. Qualification of
contact response and tight-fit clearances remains necessary.

Validation: 66 hulls compiled in the new bundle. Both coupled fingers reached -0.021 m and 0 m within 0.001 m during 160 control steps per endpoint. All positions remained finite and MuJoCo reported no warnings. CoACD reported maximum concavity 0.10435 on the back support, exceeding the requested 0.05 because of the 24-hull cap. Close-clearance contact and complete manipulation are not qualified by this initial test.

## Temporary rollback

Following observed gripper obstruction, generation now uses fingertip pads only.
The decomposed mesh assets are retained for later qualification but are not
attached to generated scenes. Finger bodies and back-support contacts are disabled.
The launcher uses a new bundle to avoid reopening the previous hull configuration.
