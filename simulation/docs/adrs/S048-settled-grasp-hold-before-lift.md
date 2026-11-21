# S048 — Require a settled grasp window before a diagnostic lift

Status: experimental simulation diagnostic. Date: 2026-11-21.

## Context

The isolated full-gripper test at load factor 1.4 reached bilateral contact at
closure, but lost it during lift; the measured piece rise was only 0.020 mm.
The old diagnostic sampled contacts once and immediately labeled grasp success.
One contact sample cannot demonstrate a sustained hold or establish lift success.

## Decision

After closure, keep issuing the unchanged command through the existing local
supervisor. Require bilateral contact and settled piece feedback for one existing
scene dwell window of consecutive control decisions. Allow at most two dwell
windows to acquire that streak. A broken streak resets its count. An execution
fault stops immediately; expiry rejects the grasp before lift. Record every
hold proposal and each simulation-only contact/settling sample.

This uses simulator feedback solely for diagnostic outcome and safety. Targets
remain camera-estimated XY plus existing experimental static geometry. No live
piece position or joint measurement is introduced into a policy observation or
command. Full collision, freshness, tracking and recovery checks still run on
every unchanged command.

## Alternatives and consequences

Increasing the success label's tolerance or ignoring a lost pad contact would
hide a failed grasp. A sustained-contact window is a stricter prerequisite, not
a guarantee against later slip. The initial contact observation and settled-hold
result are reported separately; lift still requires the original measured rise
criterion. This does not admit an RL policy or qualify camera-only hardware
outcome verification.
