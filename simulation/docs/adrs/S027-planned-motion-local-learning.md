# S027 — Plan travel and learn local manipulation

## Status

Proposed deployment architecture, documented on 2026-11-07. The recommendation
is recorded for review alongside the research paper. End-to-end integration
and physical qualification remain pending.

## Context

The watched free temporal pilot reached its 35 mm neighborhood in five of
24 training episodes and two of four final evaluation episodes. It recorded
no bilateral grip or lift. Earlier residual execution and finite full-board
approach searches also failed their corresponding gates. Those experiments
leave open both planning feasibility and local manipulation learning.

The operator's practical task is a square-to-square transfer using camera
observations, Chess Core context and an arm with limited feedback. The
repository already supplies native vision, task expansion, IK, motion
contracts, collision checking, simulation and experimental learned policies.

## Proposed decision

Use an explicit supervisor to combine planned workspace travel with learned
local approach, grasp/lift and later placement/release. Validate the handoff
region and the full path from the actual starting condition before local
training. Keep sufficient local policy freedom to discover alternative entry,
height, wrist and finger choices. Preserve one shared object-conditioned
policy as the intended multi-object architecture.

Keep actor inputs limited to images/perception, task context, calibration
and command history. Separate simulator reward/safety evidence from actor
features. Verify physical results before updating confirmed occupancy.
Preserve free temporal and residual runs as comparison groups.

The first proposed implementation uses stage handoff. MoPA-RL's magnitude
gate is an additional experimental design to evaluate separately. This
distinction is documented in the [reading guide](../../../docs/camera-rl/mopa-rl-reading-guide.md).

## Alternatives

Free temporal learning permits broader strategy discovery and has larger
exploration demands. Fixed nominal residual control supplies structure but
its tested approach family has feasibility failures. Pure conventional
execution requires demonstrated robust grasp/release under the available
perception and calibration. Planner-augmented policy actions offer another
shared architecture with a different action/execution contract.

## Consequences and acceptance

Implement one command owner, explicit scene/calibration identities, handoff
criteria, cancellation and reconciliation. Test complete approach paths,
local grip/lift, carried-object transport and release independently. Declare
how non-target contact penalties and hard stop conditions interact. Validate
hardware observability and experimental geometry before physical deployment.

The [architecture document](../../../docs/camera-rl/hybrid-motion-learning.md)
defines responsibilities, state transitions, open issues and the experiment
sequence. Long training is gated on measured acquisition of the named skill.
