# P004 — Evidence-gated hybrid manipulation development

Date: 2026-11-05. Status: accepted architecture proposal; implementation staged.

The owner requested hierarchical deterministic planning, reusable learned skills,
independent supervision and sensory confirmation. This expands the former
infrastructure-only RL scope. Preserve the owner-led learning workflow: do not
launch expensive training or physical motion before simulation/evidence gates.

Reuse Chess Core, TaskPlanner, CoordinateMapper, IK, MotionExecution and ACM1.
Introduce a Motion Intelligence orchestrator above these components, with skill
strategies behind a common contract and a deterministic baseline first. Learn
goal-conditioned manipulation skills, not chess rules or a policy per square.
Begin with one skill policy candidate; split policies only when measured negative
transfer or deployment constraints justify the complexity. No algorithm selected.

ACK/DONE means controller protocol completion, not physical success. Board commit
requires a fresh independent observation consistent with the entire expected
board change. Simulation truth must be labeled as an oracle, not camera feedback.
Fail closed on stale/conflicting/missing evidence. No automatic hardware deployment.

Phase 1 delivers the audit/proposal in docs/hybrid-control. Later phases require
explicit implementation evidence and quantitative results; diagrams of proposed
components must say proposed. No pretrained policy or embedded benchmark exists.
