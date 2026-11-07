# S017 — Penalize every simulated contact with a non-target piece

## Context

Final camera images cannot establish whether the gripper briefly touched a
neighbor and left it in place. The requested training objective now includes
penalizing contact with any physical piece other than the selected object.

## Decision

Keep the actor observation contract camera-based. Add an explicit
non_target_contact_penalty configuration for training. Check contacts at each
MuJoCo physics substep. Detect robot-to-non-target and selected-piece-to-non-target
contact. Apply the configured negative reward for each control interval containing
contact, and continue execution. Stop at a physics substep and terminate only
if a piece tilts beyond the declared toppling threshold (60 degrees). Apply
a larger toppling penalty. Track the selected piece as well as neighbors.

This mode uses privileged contact information in the training reward and
supervision. Report reward_source as rgb_plus_non_target_contacts. Pure RGB
reward mode remains available when the contact penalty is absent.

## Consequences

The policy never receives contact arrays or piece poses as features.
Simulation contact feedback does not imply that hardware has contact sensors.
The qualification report distinguishes camera target/upright evidence,
neighbor image changes and forbidden physical contacts. Approval requires correct placement, no toppling and stable neighbor images.
Contacts are penalized and counted independently from episode approval. No geometry, collision mask or threshold is
disabled to meet the acceptance target.
