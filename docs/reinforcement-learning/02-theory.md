# How the model learns: mathematics and implementation

Current camera-guided implementation and test commands are in the
[MuJoCo README](../../simulation/mujoco/README.md). The material below records the
earlier v3 study baseline or its theoretical foundations.

Read this alongside [the exact ATOM implementation](00-current-system.md).
The equations below teach the concepts; the code page identifies the actual
settings and deviations. Reproducing a derivation is useful only if you can map
its symbols to real arrays, sampled data and failure modes.

## State, observation, action and history

A state s_t summarizes the variables needed to predict the next state given an
action. In a robot this can include joint positions/velocities, object poses,
contact modes, actuator state and delays. The learner usually does not observe
that state directly. It receives o_t, such as a rendered RGB image.

An MDP has transition distribution p(s_next|s,a), reward and a policy. A camera
robot is generally a POMDP: two identical images can hide different velocities,
contact forces or occluded objects. A memoryless policy pi(a|o) cannot necessarily
choose correctly in both cases. History, filtering, multiple views or additional
measurements may resolve some ambiguity. A belief distribution is a principled
representation of uncertainty over hidden state; it is not the same thing as a
single guessed pose.

In ATOM version 3, the actor sees one image and no history. The simulator supplies
privileged reward/reset information. Do not confuse a successful restricted
curriculum with solving arbitrary partially observed robot control.

## Return and value functions

A discounted return is G_t = sum_k gamma^k r_(t+k). A value V_pi(s) is the expected
return under a policy; Q_pi(s,a) conditions additionally on an initial action.
The advantage A_pi(s,a)=Q_pi(s,a)-V_pi(s) measures improvement relative to the
policy's expectation at that situation, not an action's universal goodness.

Bellman's relation connects value now with reward and value later:

    V_pi(s) = E[r + gamma*V_pi(s_next) | s, policy pi]

Discounting affects both the objective and temporal credit. At a decision period
Delta_t, gamma^k discounts k decisions, not k seconds. A rough e-folding horizon
is -Delta_t/log(gamma): with 0.1 s and gamma=0.99 it is about 9.95 s. Changing the
action frequency without reconsidering gamma changes the physical-time objective.
This is a modeling choice, not a fixed physical law.

## Why gradients can train an action policy

For a stochastic policy, the score-function identity rewrites the derivative of
expected return in terms of sampled actions and log probabilities. A conceptual
policy-gradient estimator uses:

    grad_theta J ~= mean(grad_theta log pi_theta(a_t|o_t) * advantage_t)

The data say which actions performed better than expected. Automatic
differentiation says how changing the network parameters changes their log
probabilities. The learner need not differentiate through the simulator to use
this estimator. Standard PPO here does **not** backpropagate through MuJoCo
contacts, the camera renderer or the IK solver. See the [PPO paper](https://arxiv.org/abs/1707.06347)
for the original method; it does not guarantee physically safe behavior.

An intuitive scalar example: a parameter changes the mean of an upward-action
Gaussian. If an upward sample has positive estimated advantage, the policy term
can shift probability toward similar samples. The actual update includes all
samples, clipping, value loss and shared-feature gradients; it is not a rule
that adds a fixed amount to one weight after every successful grasp.

## Temporal difference error and GAE

A one-step TD error is:

    delta_t = r_t + gamma*bootstrap_t*V(o_next) - V(o_t)

For a true absorbing terminal outcome, bootstrap_t is zero. Time-limit truncation
is different: the task may have continued, and a suitable value bootstrap is
needed. Handle actual terminal observations rather than the reset frame supplied
after vector-environment auto-reset. See [Gymnasium time limits](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/).

GAE combines several TD residuals:

    A_hat_t = delta_t + gamma*lambda*delta_(t+1)
              + (gamma*lambda)^2*delta_(t+2) + ...

Boundary masks and rollout-end bootstrapping matter in a real implementation.
Lambda controls a bias/variance tradeoff, not how far a robot is allowed to move.
A critic can reduce variance while introducing estimation bias. The current
settings gamma=0.99 and lambda=0.95 are implementation choices, not universal
constants. Reference: [Generalized Advantage Estimation](https://arxiv.org/abs/1506.02438).

## PPO's update

Collect a rollout with frozen old policy parameters theta_old. For each sampled
transition define a likelihood ratio:

    rho_t(theta) = pi_theta(a_t|o_t) / pi_old(a_t|o_t)

The clipped surrogate being maximized is:

    L_clip = mean(min(rho_t*A_hat_t,
                      clip(rho_t,1-epsilon,1+epsilon)*A_hat_t))

A positive advantage favors increasing that sample's likelihood, with an
incentive limit after the ratio grows. A negative advantage favors decreasing it.
The minimum and advantage sign matter: clipping is not simply clipping every
policy gradient or constraining every probability to a fixed interval.

The critic fits value targets; exploration can be encouraged through an entropy
term. A typical minimized loss combines negative L_clip, weighted value error and
negative entropy. The present entropy coefficient is zero. PPO clipping does not
provide a hard trust-region or collision-safety guarantee. `target_kl=None` also
means the current run has no configured KL early-stop threshold. The [Spinning Up
PPO explanation](https://spinningup.openai.com/en/latest/algorithms/ppo.html) is a
useful companion; its default hyperparameters are not ATOM's configuration.

## From loss to weights: CNN, autograd and Adam

A convolution applies learned local filters. Nonlinearities and successive
layers combine features into a 512-dimensional representation in this policy.
The actor produces action means, and the critic predicts value. Shared encoder
weights can receive gradients from both objectives; competition between those
objectives is a real representation-learning issue.

For a simplified neuron z=w*x+b, chain rule gives dL/dw=(dL/dz)*x. In a network,
autograd composes these local derivatives over the recorded computation graph.
It does not discover the intended task; the chosen loss, rewards and data define
what is optimized. See [PyTorch autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html).

Adam maintains moving estimates of the first and second gradient moments:

    m_t = beta1*m_previous + (1-beta1)*gradient
    v_t = beta2*v_previous + (1-beta2)*gradient**2
    weights_next = weights - learning_rate*m_hat/(sqrt(v_hat)+epsilon)

Bias-corrected m_hat/v_hat account for zero initialization of these estimates.
Current learning rate is 3e-4; gradient norm is clipped at 0.5 before the update.
The maximum gradient norm and PPO's probability-ratio clip are different
operations. See [SB3 PPO documentation](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html)
and inspect the local installed source when exact implementation details matter.

## Reward engineering and its traps

A reward is a numerical objective, not a measurement of human intent. If staying
just below a success threshold earns money every step, delaying success can be
optimal. If one frame is enough to declare success, bouncing or losing grip
immediately afterward may exploit the definition. A high score can be a precise
solution to the wrong problem.

Version 3 replaces a repeated partial-lift payment with potential differences.
In an undiscounted finite sequence, sum(Phi_next-Phi_current) telescopes to final
minus initial potential. The policy-invariance theorem for discounted shaping
instead uses F=gamma*Phi_next-Phi_current, with appropriate boundary conditions.
ATOM's current formula and terminal handling must therefore not be advertised
as an application of that guarantee. Study [Ng, Harada and Russell](https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf),
then test a proposed correction against version 3 as a new environment version.

Use explicit outcome metrics independent of reward. Penalizing neighbor movement
above 8 mm does not mean smaller movement, rotation or transient contact is
irrelevant. A reward that depends on inaccessible simulator state can be useful
for simulation training, while the deployment verifier still needs its own
observable evidence contract.

## Comparing algorithm families

| Family | Data and objective | Reason to investigate | Main ATOM question |
|---|---|---|---|
| Tabular TD/Q-learning | Small discrete states/actions | Learn credit assignment without a CNN | Can you explain convergence assumptions and bootstrapping? |
| PPO | On-policy actor-critic | Existing baseline, relatively direct rollout/update accounting | Is failure in the task/observation, not the optimizer? |
| SAC/TD3 | Off-policy continuous control with replay | Investigate sample reuse | How do visual representation, replay distribution and action limits affect learning? |
| HER with an off-policy learner | Relabel achieved goals | Sparse goal-conditioned manipulation | Are relabeled goals/rewards valid under obstacles and task semantics? |
| Behavior cloning | Supervised action prediction from demonstrations | Obtain an initial skill | Do demonstrations cover states produced by the learned policy? |
| Residual RL | Learned correction around a nominal controller | Preserve useful geometry/control structure | Are corrections bounded and rechecked for collisions? |
| Model-based RL/MPC | Learn or use dynamics to predict and plan | Investigate sample efficiency and constraints | What happens when the learned model is wrong at contact? |
| Diffusion/action-sequence imitation | Learn action distributions from demonstrations | Multimodal manipulation sequences | What latency and closed-loop correction does deployment permit? |

SAC, HER, residual control, world models and diffusion policies are research
options, not implemented alternatives in the current ATOM trainer. Diffusion
policy imitation is not automatically reinforcement learning. Read the primary
papers listed in resources (chapter pending) before designing a comparison.

## What to derive before changing the network

Derive Bellman's equation on a two-state example; compute one TD/GAE trajectory;
calculate PPO's clipped objective for positive and negative advantages; verify a
small network's gradients numerically; and explain what reset distribution the
reported success rate integrates over. Then identify a specific failure that a
new architecture could address. More layers do not fix an incorrect reference
frame, a mislabeled episode boundary or a reward exploit.
