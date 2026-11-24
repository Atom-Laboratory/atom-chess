# P027 — Curriculum weight transfer

Lift starts with a prepared grip. Grasp starts above the piece. Transfer the
verified policy tensors between these stages to test whether learned lift
behavior accelerates grasp training. Keep a fresh optimizer and step counter.
Same-task resume continues to restore the optimizer and counter.

Require matching environment version, bundle, horizon and policy spaces.
Validate checkpoint provenance and verify copied tensors before training.
Random initialization remains a comparison baseline. Reusing optimizer state
across tasks would also transfer accumulated gradient statistics.

A lifted piece and an ungrasped piece require different actions. Transfer can
hurt performance. Compare both initializations at matched budgets. Expanded
collision geometry requires its own compatibility and evaluation experiment.

The full-open grasp reset uses an explicit reset revision. It starts 20 mm
above the stem and requires no initial fingertip contact with the target.
Resume compares the reset revision. Weight transfer may cross this reset
change when switching from lift to grasp on the same bundle.

## Partial transfer after observed negative transfer

The fully open reset was feasible in a scripted probe. The lift donor's
first deterministic Z action was +1 at the grasp reset, commanding motion
away from the target. Add explicit feature-only transfer. Copy and verify
the CNN encoder while initializing the actor, critic and exploration scale
from the new target agent. Record the transfer mode in the run lineage.
