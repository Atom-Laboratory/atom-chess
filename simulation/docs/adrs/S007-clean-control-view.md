# S007 — Keep robot controls from enabling native debug graphics

Date: 2026-10-30. Status: accepted.

## Cause

The passive viewer processes native shortcuts alongside our callback. A, used
to reverse the first joint, enables Auto Connect: large blue connecting capsules
obscure the robot and board. C, used to close the gripper, toggles contact markers.
Other controls also overlap native rendering shortcuts. These are diagnostic
graphics, not collision meshes or additional robot parts.

## Decision

Restore default visualization options under the viewer lock before every sync,
and hide collision group 3. Keep camera, physics, contacts and robot controls
unchanged. The normal control viewer intentionally does not retain native debug
flag toggles; developers can use a separate diagnostic viewer when needed.

## Validation

Regression test enables all flags as if native shortcuts had run, restores the
control view and checks Auto Connect/contact points/contact forces/inertia off,
static bodies on and collision group hidden. This correction is runtime-only;
existing bundles do not need rebuilding. Restart the viewer to load the code.

Source: [official native shortcut table](https://github.com/google-deepmind/mujoco/blob/main/doc/programming/samples.rst).
