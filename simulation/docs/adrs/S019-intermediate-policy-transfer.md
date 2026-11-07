# S019 — Transfer saved intermediate PPO policies

## Context

An interrupted PPO run may contain usable checkpoints without a final report.
The camera localization and reward revision changes the environment used by
the opening pawn, but it preserves the policy input and output spaces.

## Decision

Allow explicit transfer from an intermediate checkpoint in its original run
directory. Check its archive digest when supplied, validate policy spaces and
record the source, archive digest, source steps and initial weights digest.
Initialize a fresh optimizer and step counter for the transfer.

## Alternatives

Requiring a final policy report discards usable progress from interrupted
runs. Exact resume preserves optimization state and requires an unchanged
environment and a finalized run.

## Consequences

The new run preserves checkpoint lineage independently of its local step
counter. Checkpoint integrity and compatible policy spaces establish that
weights were transferred. Manipulation performance needs separate evaluation.
