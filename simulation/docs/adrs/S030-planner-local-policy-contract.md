# S030 — Explicit planner-to-local-policy contract

## Context

S029 demonstrated a particular six-command native approach and retreat. Its
small entry-neighborhood certificate does not qualify grasp/lift exploration.
The existing autonomous controller exposes seven controls, including elbow
branch and variable duration, and has global exploration semantics. Connecting
that action space directly would bypass the intended local scope. Existing
MoveTask, Evidence, Execution and VisualHistory already supply reusable task,
evidence ordering, global phase tracking and camera/command history interfaces.

## Decision

Implement M3 as a pure, versioned, independently tested interface, without
actuator execution or policy training. Reuse MoveTask/Execution rather than
creating another global task state machine. A local control lease is permitted
only after actual approach, a qualified local workspace, matching task/board,
camera/reference/model identities and an explicitly eligible qualification.
An approach followed by retreat cannot grant local control. The M2 output
therefore remains ineligible; do not reinterpret its small box as a grasp volume.

The policy proposes five normalized controls: local robot-frame TCP delta XYZ,
wrist delta and coupled-finger opening delta. Duration is one explicitly bound
model control interval. No elbow-branch toggle, global destination or direct
joint target is accepted. Static-model-derived rates and a separately qualified
local envelope are supplied by the host. Reject out-of-range proposals without
clipping, projection or reinterpretation. A decoded proposal is not collision
approval: IK, swept-path checking and actual execution belong to M4.

Build actor observations only from validated camera/perception values, the
existing task, logical kind/color, issued command history, previous action and
authorized phase. Reuse VisualHistory's two-frame 96x96 RGB preprocessing.
Detach and freeze all actor arrays. The observation builder accepts no model,
simulation, contact, body-pose, reward or execution-report object. Simulator
feedback remains outside this interface. Identical allowed input histories
must yield identical actor payloads regardless of hidden simulator state.

Lease ownership follows existing Execution phases: planner for global motion,
RL only for GRASPING/LIFTING after admission, supervisor for verification and
failures. Reject stale/replayed proposals, changed references and invalid phase
ownership. The existing global evidence machine remains responsible for
phase advancement; lease operations never mutate board occupancy or assert
that a grasp/lift occurred. Oracle-enabled executions cannot receive this lease.

## Alternatives

Reusing the seven-control autonomous action space would preserve incompatible
global exploration. Reusing five-axis pixel policies would lose wrist support.
A second task state machine would duplicate existing evidence/freshness logic.
Starting PPO now would train before local workspace and deterministic grip/lift
qualification. A raw simulator-derived observation would violate deployment
requirements.

## Consequences and acceptance

The action/observation schema differs from existing policies; old checkpoints
cannot be silently resumed. Tests cover observation invariance and immutability,
numeric/bounds rejection, lease admission, reference/task identity, ownership
and replay. This increment does not qualify a physical manipulation envelope,
implement a camera-only grasp/lift verifier or prove the truth of caller-supplied
evidence. It does not launch RL. Stop and report M3 before connecting proposals
to low-level execution in M4.
