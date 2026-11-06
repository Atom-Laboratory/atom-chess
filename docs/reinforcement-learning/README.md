# Reinforcement learning for ATOM: foundations to research

This is the English learning and engineering hub for camera-based robot control.
The target is the ability to formulate, implement, diagnose and evaluate a robot
learning system, and then transfer a qualified behavior to hardware. Watching a
successful animation is an observation; mastering the subject requires explaining
why it works, where it fails, and which experiment could disprove the explanation.

The operational descriptions below belong to the earlier v3 lift/grasp study
material. Current setup and training commands are in the
[MuJoCo README](../../simulation/mujoco/README.md), with the
[P038 pipeline walkthrough](../camera-rl/P038-pipeline-walkthrough.md).

## Read this hub by purpose

| Need | Document |
|---|---|
| Understand the exact running implementation | [Current system and limitations](00-current-system.md) |
| Decide what to implement next | [Engineering roadmap and acceptance gates](01-next-steps.md) |
| Understand models, gradients and PPO | [Mathematical and computational mechanics](02-theory.md) |
| Run, compare and debug experiments | [Experiment laboratory](03-experiment-lab.md) |
| Understand robot physics, vision and deployment | [Robotics and sim-to-real](04-robotics-and-transfer.md) |
| Connect mathematics, physics, biology and information theory | Multidisciplinary research track (chapter pending) |
| Prove mastery through implementations and measurements | Exercises and capstones (chapter pending) |
| Select books, courses, papers and official documentation | Annotated resources (chapter pending) |
| Start, pause, stop, resume or replay the actual software | [Windows operational guide](../hybrid-control/visual-grasp-rl-guide.md) |

## Two tracks, pursued together

The **engineering track** develops ATOM through measured experiments. The
**foundations track** develops the mathematical and computational tools needed to
understand those experiments. Do not wait until every textbook is finished to
collect your first data. Do not use a working library as a substitute for being
able to derive its objective and audit its assumptions.

Start at a higher level if you can already complete its exit exercise. Progress
is measured by artifacts and explanations, not by a fixed number of study weeks.
Choose one core resource per subject; add another only to answer a specific gap.

## Roadmap: zero to independent researcher

The IDs below are study milestones, not implemented software features. The
engineering feature status is maintained in [01-next-steps.md](01-next-steps.md).

| Level | Topics to command | Build or demonstrate | Exit criterion |
|---|---|---|---|
| R00: reproducible computing | Python, NumPy, Git, venvs, arrays, units, tests, deterministic seeds | A reproducible experiment folder and finite-difference derivative checker | Reproduce another person's result from its manifest; identify what is still nondeterministic |
| R01: linear algebra and geometry | Bases, rank, null spaces, projections, eigensystems, SVD, positive definiteness, homogeneous transforms | Least-squares camera/point fitting and damped Jacobian inversion | Explain singular values, conditioning and why a pseudoinverse amplifies noise |
| R02: calculus and optimization | Multivariable derivatives, chain rule, Jacobians, Hessians, constrained optimization, SGD, Adam | Backpropagation for a small MLP using NumPy | Match numerical gradients and distinguish parameter gradients from robot Jacobians |
| R03: probability and experimental statistics | Conditional probability, Bayes, expectation, covariance, sampling, confidence intervals, hypothesis tests | A seeded Bernoulli experiment with confidence bounds and paired comparisons | Explain why 5/5 demonstrations do not establish near-perfect reliability |
| R04: dynamical systems and control | ODEs, discretization, stability, observability, PID, linearization, LQR, constrained control | Stabilize a simulated system and characterize delay/overshoot | Predict how changing sample period affects the controller |
| R05: rigid-body robotics and contact | SE(3), frames, forward/inverse kinematics, Jacobians, inertia, friction, grasp mechanics | Predict the TCP motion and demonstrate a physically feasible grip | Separate visual geometry, collision geometry and measured physical parameters |
| R06: vision and estimation | Pinhole projection, intrinsics/extrinsics, distortion, homography, tracking, occlusion, filtering | Calibrate a board and measure held-out pixel-to-world error | Explain why a board homography does not recover the height of an airborne piece |
| R07: decision processes | Bandits, MDPs, POMDPs, Bellman equations, returns, discounting | Solve a small MDP by dynamic programming | State which information makes an observation non-Markov |
| R08: learning values | Monte Carlo, TD, SARSA, Q-learning, bootstrapping, approximation | Implement tabular algorithms and investigate a failure case | Distinguish sample efficiency, policy evaluation and off-policy instability |
| R09: deep learning and policy gradients | CNNs, stochastic policies, log probabilities, REINFORCE, baselines, actor-critic, GAE | Derive and implement a minimal actor-critic on a small task | Explain how actions with delayed consequences receive credit |
| R10: PPO and practical deep RL | Clipped objectives, likelihood ratios, entropy, optimizer updates, action distributions | Reproduce a small PPO experiment and inspect actual checkpoints | Explain every rollout/update dimension and recognize misleading metrics |
| R11: experimental robot learning | Reset distributions, rewards, success predicates, baselines, ablations, train/validation/test splits | Compare ATOM lift/grasp policies across multiple training seeds | Demonstrate a visual-information ablation and report uncertainty |
| R12: general manipulation | Goal conditioning, curriculum, collision costs, task planning, options, recovery | A proposed-to-implemented generic pick/place skill with a frozen evaluation suite | Complete unseen source/target pairs without inventing state updates |
| R13: sim-to-real engineering | System identification, camera calibration, latency, uncertainty, domain randomization, deployment profiling | A measured simulator-to-hardware discrepancy report | Identify which quantities are measured, estimated, assumed or unavailable |
| R14: advanced methods | SAC/TD3, HER, demonstrations, residual RL, model-based RL, world models, constrained RL | Compare one justified alternative under matched budgets | Explain why it helps this failure mode, rather than merely being more recent |
| R15: independent research | Causal experimental design, literature criticism, reproducibility, negative results | A complete reproducible paper-style investigation | A third party can reproduce the claim and its stated limitations |

Suggested dependencies: R00 -> R01/R03; R01 -> R02/R04/R05; R03 -> R07/R08;
R02/R03 -> R09/R10; R05/R06/R10 -> R11/R12; R11/R12 -> R13/R14/R15.
You can study physics and probability in parallel while collecting baseline data.

## First practical sequence

1. Read the current-system page and identify every simulator-only signal.
2. Read the current run's `progress.json`; distinguish training success from evaluation.
3. After a normal finish, inspect `report.json` and replay both successes and failures.
4. Work through exercises E01-E05 before changing architecture or reward weights.
5. Design the lift evaluation described in gate G1. The broad evaluator is planned,
   not already available as a command.
6. Start `grasp` as a **new** stage/run; the current resume guard deliberately
   rejects treating a lift checkpoint as an unchanged grasp environment.
7. Keep the controller and task planner as baselines while investigating learning.

## Definition of advanced competence

You can derive the update, explain its numerical implementation, design a
falsifiable experiment, audit its information assumptions, debug the robot's
frames and contacts, quantify uncertainty, and state precisely what transfers to
hardware. A large policy or a high training reward does not replace any of these.

## Documentation maintenance

The source of truth is the code plus a versioned experiment, not this roadmap.
Update the current-system page when behavior changes. Record architectural
changes in an ADR before implementation. Never rewrite an old result as evidence
for a new reward, camera configuration or reset distribution. Keep large runs,
checkpoints and videos out of Git; commit small reports and reconstruction steps.
