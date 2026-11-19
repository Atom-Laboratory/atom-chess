# Training experiments

See the [proposed planner/local-policy architecture](../../../docs/camera-rl/hybrid-motion-learning.md)
and [paper reading guide](../../../docs/camera-rl/mopa-rl-reading-guide.md)
for the recommended evolution and its qualification gates.

- [Grasp and lift](grasp-lift/README.md) describes the legacy local manipulation policy.
- [Camera manipulation](camera-manipulation/README.md) describes the P038 residual policy.
- [Autonomous manipulation](autonomous-manipulation/README.md) describes the
  experimental continuous temporal policy with independent collision supervision.

Each execution owns a complete runs/<unique-id>/ directory, containing its
configuration, checkpoints, optimizer state, episode logs, reports and lineage.
Keep these files together when resuming or archiving. Default output paths are
resolved relative to this module even when the terminal is elsewhere.
Explicit relative inputs remain relative to the caller's terminal directory.

Existing runs are listed in the
[migration inventory](../docs/reorganization-audit-2026-11-06/README.md).
Their physical migration remains pending. Presence of policy.zip does not imply
compatibility. The old four-action policies have no learned wrist action.
P038 source-signature checks can reject a historical run after code changes,
including this entry-point/output update. Preserve original provenance and
use the original source revision to reproduce that environment.
