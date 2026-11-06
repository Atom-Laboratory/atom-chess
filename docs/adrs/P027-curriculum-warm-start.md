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
