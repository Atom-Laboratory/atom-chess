# Develop your own ATOM RL experiment

Start with the [MuJoCo manual](../../mujoco/docs/mujoco-user-guide.md).
You implement the agent; no policy, optimizer or training pipeline was added.

## 1. Understand the components

MJCF describes the robot. A learned policy is a separate function mapping
observations to actions. An environment advances simulation, evaluates rewards
and identifies episode boundaries. observe returns simulator state; you choose
which fields become observations. advance receives position targets in [rad,m,rad].
Normalized actions or increments need explicit conversion and validation.

Reward expresses task quality; return accumulates rewards. An episode starts at
reset. terminated means a task-defined end; truncated means an external limit.
Both may be true on the final step. Conventional demo control uses fixed rules;
learned control updates a policy from experience. Movement alone is not learning.

## 2. Implement the task interface

atom_mujoco.experiment.Episode(simulation, task, max_steps=...) requires your Task:

| Method | Your decision |
|---|---|
| reset(state, rng) | Goal/task initialization using the supplied RNG |
| observation(state) | Fields, dimensions, units, normalization |
| target(action, state) | Action validation/conversion into SI joint targets |
| evaluate(before, after) | Finite scalar reward, boolean termination, diagnostics dict |

reset(seed=..., position=... or randomize=True) returns (observation, info).
step returns (observation, reward, terminated, truncated, info), with state,
steps and task diagnostics in info. max_steps * sim.dt determines the time limit.
Invalid targets consume no step. After completion or an error following physics
mutation, reset is required. Reset and task use independent seeded RNG streams.
Avoid global randomness and hardware access in callbacks.
The default randomized reset samples the central 40% of joint ranges, without
collision guarantees. The zero-reward Task in tests is only a test double.

This is not yet Gymnasium.Env. Once spaces are chosen, add Env, action_space,
observation_space and Gymnasium seeding, then run its environment checker.
[Official API](https://gymnasium.farama.org/api/env/).

## 3. Specify a first reaching experiment

Version this specification before implementing a reward:

| Field | Open decision |
|---|---|
| Task/frame | Reach arm2_frame or an explicit tool offset? Which coordinates? |
| Reset/goals | Fixed first? Which targets/seeds are held out? |
| Observations | q, qdot, goal/error? Can hardware provide these signals? |
| Actions | Absolute position or increment? Scale, frequency, limits? |
| Reward | Distance/progress/time/effort? Which shortcuts are possible? |
| Success | Distance tolerance and dwell time? |
| Failure | Nonfinite state, limit excess, timeout? Contacts remain unavailable. |
| Metrics | Final error, time, success rate, joint excess, variation across seeds |

arm2_frame is the last joint origin; its position does not change when that
joint rotates. Choose an experimental offset or extract the physical TCP from
CAD. Compute p_tool = p_arm2 + R_arm2 @ offset; experimental_tool exposes this
composition. Synthetic offsets are not physical measurements.
Generate reachable targets with FK of valid joint configurations, while retaining
the collision limitation. Keep training, selection and final evaluation sets distinct.
Negative distance may tolerate stalling; progress reward may permit cycles;
excessive effort penalties may prevent movement. Test hand-checked reward ordering
before choosing weights. No final reward is selected here.

## 4. Follow verifiable personal steps

1. Run inspect_joints and predict the three responses and SI units.
2. Configure a tool point; verify its pose by independent rigid composition.
3. Complete the experiment specification and discuss its tradeoffs.
4. Implement Task; test dimensions, invalid actions, reset, reward cases,
   success/failure and timeout with predetermined commands.
5. Record a conventional baseline using identical goals/model conditions.
6. Compare methods before choosing: PPO collects fresh batches; SAC/TD3 reuse
   transitions with replay/critics. Start small on CPU and measure cost.
7. Implement policy/update logic incrementally, review it, then explicitly train.
8. Evaluate held-out goals across seeds; report failures/distributions and
   sample/time cost alongside return, rather than only the best run.

## 5. Reproduce and compare

recording.provenance/save_record includes commit, dirty/untracked flags, platform,
versions, manifest and exclusive JSON writes. Demos record wall time and results;
task/algorithm are null. For your task add identifier/revision/code/configuration,
spaces, goals, reward/termination, max_steps, seed, algorithm/hyperparameters,
episodes/transitions and metrics. Future checkpoints need hashes, architecture
and normalization metadata. Preserve bundle/lock and task code alongside results.
The recorder does not snapshot dirty/untracked sources: preserve those manually.
runs stays outside Git; back it up. Bitwise replay is only tested on one installation.
JSON suffices initially; see [dependency evaluation](dependencies.md).

## 6. Respect the hardware boundary

Main is integrated, but no policy bridge exists. acmotion expects J1/J2/J3 in rad,
Z in mm and gripper percentage. This model has two revolutes, Z in metres and
a fixed gripper. Do not invent missing axes to force a mapping. Future strategies
must pass an independent validation/control layer before MotionExecution/ACM1.
Its segment ACK/DONE execution is not a 50 Hz policy servo. This module has no
motor transport or automatic deployment. See [deployment boundaries](deployment-acmotion.md).
