# S034 — Portable training diagnosis

## Context

Historical configurations refer to ignored machine-local fixture directories.
Short training runs changed weights without producing held-out success.
Performance telemetry could not distinguish optimizer time from the visual
environment and native validation.

## Decision

Define a canonical short CPU protocol with tracked scene inputs and fixed
training and evaluation seeds. Regenerate the fixture per run and keep
configuration and provenance beside the policy. Export allowlisted telemetry
and verified checkpoint hashes. Treat scene/config changes during warm start
as explicit transfer and record the source configuration hash. Record actual
optimizer wall time separately from rollout time.

## Alternatives

A large shared checkpoint would shorten startup but would inherit the
historical fixture dependency. A long GPU benchmark would consume more
resources while leaving install, evaluation and resume paths untested.

## Consequences

Contributors can reproduce a bounded reach comparison without prior runs.
Small held-out counts establish workflow behavior and expose failure cases.
Warm starts transfer weights and recreate optimizer and RNG state. Fixture
qualification and diagnostic results remain simulation-scoped.
