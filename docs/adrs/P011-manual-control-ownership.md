# P011 — Manual control ownership

Status: incremental implementation. Roadmap phase: P010 teleoperation.

## Context

ADR P010 already names collision preflight, so roadmap numbering must not replace
historical decisions. Existing viewer jogging bypasses task ownership. P007 must
not receive invented successful transfers from keyboard input.

## Decision

The task console owns keyboard press/release events. Losing focus clears held
keys. Its timer advances one controller interval per manual tick. Manual and
autonomous mode changes are explicit; autonomous submission is disabled while
manual mode is selected. Pause and simulation stop freeze timer-driven physics.
Reset is an explicit new experiment, never cancellation or recovery of a task.

The console captures jog shortcuts only while its dedicated keyboard control
has focus. Arrows control J1 and Z, Page Up/Down control J2, and Home/End open
and close the gripper. The mouse jog buttons use the same held-input path.
The native 3D viewer retains its own camera and visualization controls.

Introduce a reusable manual input mapper with explicit ownership, held-key state,
velocity-bounded joint targets and a latched simulation stop. Commands go through
MotionController.step. Releasing all keys holds the last target. Each actual manual
tick marks the confirmed state as requiring reconciliation and collects an
observation separately. Unknown observations remain errors, never confirmed state.
Autonomous dispatch is rejected while manual ownership is active. Pause freezes
physics at a tick boundary. Stop requires an explicit scene reset to clear.

## Alternatives and consequences

Direct qpos writes bypass physics and controller constraints. Assuming unchanged
pieces after manual motion permits stale dispatch. Conservatively requiring
reconciliation after any manual tick is restrictive but explicit. Cartesian
teleoperation, configured Cartesian workspace checks and integrated GUI lifecycle
remain subsequent work; joint limits alone do not establish collision safety.
