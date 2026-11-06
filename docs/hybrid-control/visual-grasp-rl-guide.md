# Experimental visual grasp PPO

Install the optional rl dependencies in the existing MuJoCo environment.
The current workstation experiment used Gymnasium 1.4.0, SB3 2.9.2 and
PyTorch 2.15.0+cpu. CUDA was unavailable in this environment. Use --device cuda
only after installing a matching CUDA-enabled PyTorch distribution and verifying
torch.cuda.is_available(). This command rejects an unavailable CUDA device.

From the repository root:

    & ./simulation/mujoco/.venv/Scripts/python.exe -m pip install -e './simulation/mujoco[rl]'
    & ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/train_visual_grasp.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --output simulation/mujoco/runs/visual-grasp-first --steps 100000 --eval-episodes 10 --device auto

Use a new output directory every run. The directory contains policy.zip and
report.json with model hash, device, training seed, held-out episodes and
checkpoint hash. The script evaluates a hold-position control on the same seeds.
This baseline is a lower-bound diagnostic, not the full deterministic pick/place
controller. The checkpoint is reloaded and deterministic action parity is checked.

The task is local E2 pawn lift with randomized initial joint offsets. Policy
input is 96x96 RGB. Actions are J1/Z/J2/finger reference increments, bounded
by joint/velocity constraints through the existing controller. Rewards favor
approach, bilateral grip and 35 mm lift sustained for three steps. Moving any
other piece over 8 mm terminates with a penalty. Reward and success use simulation
oracle state. Visual acvision confirmation remains pending. Reset uses legacy IK
to stage the task, while learned action steps use no IK. This is an experimental
curriculum with fingertip-only contacts and experimental dynamics.

A 128-step run updated the model and saved a valid reloadable checkpoint but
scored 0/2 successful lifts. It is insufficient to qualify a policy for normal
chess execution. No checkpoint is automatically enabled in the console. Generic
source/destination transport, captures and hardware inference remain future work.

The Gymnasium environment checker runs before learning. The environment regression
checks pixel observations, deterministic resets, invalid actions and horizon.

Inspect a recorded experiment with the viewer:

    & ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/replay_visual_grasp.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --run PATH_TO_RUN --seed 10000

The replay verifies model/checkpoint hashes against report.json and prints the
episode result. The viewer remains open at the final state for inspection.

The 2048-step CPU follow-up took 114 seconds and scored 0/5 lifts. All five
evaluation episodes terminated after disturbing another piece; hold-position
control disturbed none. Higher reward therefore does not establish improved
manipulation. See visual-grasp-2048-report.json for the recorded metrics.
