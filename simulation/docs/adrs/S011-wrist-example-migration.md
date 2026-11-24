# S011 — Migrate examples to the wrist model and colocate run artifacts

## Context

The bounded wrist adds a sixth actuator. Existing finger slice assignments
include every actuator after J2, so they would overwrite a wrist target.
The P038 actor and native motion ABI still assume five commanded joints.
Existing checkpoints record those dimensions and model provenance.

## Decision

Restrict coupled finger operations to indices 3 and 4 before migrating consumers.
Keep historical commands available while adding a directory per runnable example
with a README and run.py entry point. Store new results under each example's
results directory using fresh run identifiers. Preserve existing run locations.

The wrist training migration requires a versioned observation/action contract,
kinematics that accounts for the offset between wrist axis and grasp center,
and successful collision and perception checks before training starts. Existing
five-actuator policies require explicit transfer or a fresh training run.

## Alternatives and consequences

Renaming every script immediately would break documented paths and imports.
Directory entry points preserve those paths during migration. Automatically
resuming old checkpoints would silently change action meanings and is rejected.
Generated results remain ignored by Git, while commands and limitations are
documented beside each example.
