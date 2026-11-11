# S032 — Explicitly authorized experimental camera-actor PPO run

## Context

On 2026-11-09 the operator explicitly requested training now and an overnight
run, with the camera as the robot's only sensor and simulator supervision
allowed during training. M4's deterministic isolated trial grips but loses
contact during lift. Full-board approach-to-grasp candidates remain blocked.
There is no qualified local workspace artifact for hybrid policy deployment.

## Decision

Run the existing PyTorch/Stable-Baselines3 PPO autonomous comparison experiment,
explicitly labelled experimental, on the existing isolated full-gripper pawn
fixture. Begin with grasp acquisition, use camera-only actor features plus
logical task and issued-command history, and keep privileged simulator reward
and collision feedback outside actor observations. Native collision supervision,
joint bounds and toppling guards remain enabled. CUDA is required explicitly.

This is authorized learning before deployment qualification, not an assertion
that M5/M6 of the hybrid roadmap have passed. Do not fabricate a workspace
artifact, bypass LocalHandoff or deploy the autonomous policy as the qualified
hybrid controller. Preserve the seven-action comparison interface and label
its duration/elbow controls and initialization teleportation in documentation.
Use fresh output paths, periodic verified checkpoints, CSV metrics and Watch.

The newest inspected completed autonomous policy uses an earlier feature
architecture. Do not silently warm-start incompatible feature normalization
weights. Record fresh initialization for policy version 2 and preserve all
earlier checkpoints. A bounded smoke run must demonstrate finite updates,
checkpoint creation and working resets before the longer session continues.

## Alternatives and consequences

Claiming a failed deterministic lift is qualified would conceal an open issue.
Running a long unchanged reach-only job would not target the requested skill.
Adding another training framework would duplicate an existing tested PPO stack.
This experiment may fail to learn grasping; training reward and a changed weight
hash are not independent manipulation success or physical robot readiness.
Long training remains bounded by a recorded step count and saves checkpoints.

The operator subsequently requested background comparisons and conditional
2→4→8 training processes. Use complete bounded chunks, independent seeds and
separate policies/logs. Escalate only after at least 50% grasp success on eight
selection episodes, projected GPU/host memory headroom and measured aggregate
throughput. These reused selection seeds are validation, not an untouched
generalization test. Decrease the next round's capacity if throughput falls
by more than 10%; do not repeatedly reattempt that failed concurrency level.
Keep all earlier policies and select the best validation candidate for the
next round rather than averaging unrelated policy weights.

Recovery on 2026-11-10: both processes disappeared after approximately 3000
decisions; their latest intact archives are at 2048. Windows reports an unclean
restart (Kernel-Power event 41 at 08:53:16). This supports interruption by a
system lifecycle event but does not identify the exact shutdown cause/time.
Recover each branch from its own SHA-verified intermediate checkpoint using
the existing weights-only warm-start interface, with a fresh optimizer and
fresh output directories. Do not silently restart both branches from the pilot.
Record a periodic wall-clock heartbeat; a saved `running` label is not proof
that a process survived a system restart.
