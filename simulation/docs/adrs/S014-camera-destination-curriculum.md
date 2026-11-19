# S014 — Camera-only destination curriculum and explicit policy transfer

## Context

The RGB-reward policy passed a fixed e4-to-d5 transfer. Repeating that fixed
task does not qualify task-conditioned movement. A destination curriculum must
expose the selected square to both the actor and visual verifier.

## Decision

Allow camera-only configurations to specify task_targets. Select a target
using the episode RNG, build nominal geometry for that target, and pass the
same target to the actor task vector and visual verifier. Keep the source and
one-piece fixture fixed for this increment. Use a distinct environment version
when a curriculum is configured.

A changed curriculum requires an explicit warm start. Load prior policy weights
into a fresh PPO instance after validating spaces and checkpoint integrity.
Record the source run and checkpoint hash. Exact resume continues to require
identical provenance and retains optimizer state.

Qualify deterministic camera confirmation for each target before including it.
Keep failed target results and avoid inferring success from nominal commands.

## Consequences

A successful curriculum remains a one-piece, five-actuator simulation.
Camera observations cannot certify grip forces or collision safety.
Evaluation must record each selected target and report per-target results.
Warm start resets optimizer history, step count and training RNG.
