# P025 — Visible camera-policy training and grasp curriculum

## Context
P023 proves PPO weight updates but its first trial failed all five evaluations.
Reset used fully open jaws and an arbitrary grasp height. P024 established a
verified proxy-based aperture for E2. Training must expose real RGB observations,
progress and resumable results, rather than imply a scripted demonstration learns.
The workstation has an RTX 5070 Ti but its previous PyTorch was CPU-only.

## Decision
Offer two explicit curricula: lift starts with a reset-only verified grip;
grasp starts just above the stem with pre-shaped open fingers. Use P024's
experimental stem and fingertip proxies for staging. Preserve settled piece
poses when positioning the arm, and reject disturbed or invalid reset states.
Use a fixed episode camera; the policy consumes RGB only. Reward/success remain
simulation-oracle signals, never described as acvision confirmation.

Expose a live 3D viewer, exact policy RGB preview, episode metrics, pause/resume
and graceful stop. Save periodic checkpoints, append episode records and write
an atomic progress snapshot. Closing the viewer stops training and preserves a
checkpoint; it must not silently leave an invisible expensive run. UI simulation
runs at an adjustable maximum speed; headless mode omits deliberate pacing.
Resume only checkpoints with matching bundle, stage and environment version.
Evaluate held-out seeds and preserve the hold baseline and deployment block.
Use an explicitly verified CUDA PyTorch distribution for policy computation;
standard MuJoCo dynamics remain CPU work. No hardware commands are dispatched.

## Alternatives
End-to-end full-game training would make the existing grasp failure harder to
diagnose. Blindly running the old task longer was rejected. Making acvision's
board detector a required policy input is unnecessary for this RGB curriculum:
its current interface detects board corners, not reliable gripper/held-object
poses. Real-camera calibration and acvision-based manipulation verification
remain separate prerequisites for physical deployment.

## Consequences
Lift success does not mean the policy learned to close the gripper. Grasp and
full transfers require separate evaluation. The viewer slows data collection.
Experiments use experimental dynamics and fingertip-only collisions. The UI is
observational and cannot directly change actuator commands or physical board
state. All run metadata must identify the curriculum and oracle supervision.

Environment version 3 uses differences of a bounded grasp/lift potential plus
a terminal success bonus and step cost. Version 2 pilots paid for lift every
step, potentially favoring hovering below the terminal threshold. They are not
compatible checkpoints. A STOP file in the run directory requests a graceful
save for non-GUI supervision. Resume does not restore the exact rollout/RNG.

References: https://pytorch.org/get-started/locally/ and
https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html


## Validation
Five environment/monitor tests passed. A version-3 CUDA run completed 128 PPO
steps, changed policy parameters and verified checkpoint reload parity; held-out
lifts scored 0/1, so deployment remains disabled. Resume restored that policy,
trained to cumulative step 257, then a STOP file ended the run with interrupted
true, a reloadable saved policy and no claimed evaluation. A separate visible
pilot opened the MuJoCo and RGB panel windows. Windows automation could list
them but screenshots/activation failed with FrameArrived/activate timeouts;
actual button clicks could not be verified. Pause/stop state transitions were
unit-tested. See visual-lift-v3-128-report.json for the current curriculum's
short experiment; superseded version-2 pilot rewards are not comparable.
