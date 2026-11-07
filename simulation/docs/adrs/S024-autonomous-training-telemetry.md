# S024 — Observe autonomous policy learning and preserve recovery evidence

## Context

The autonomous runner offers a MuJoCo viewer and a camera viewer. Its PPO
dashboard was never connected. ACCEPTED describes a supervised motion
segment, while the user needs to see distance to the target, manipulation
feedback, reward components, optimizer updates and execution progress.
The existing residual dashboard already consumes real persisted events.

Short experiments also need reproducible device selection, adjustable PPO
rollout settings and independent evaluation. A failed reset can terminate
training before the first periodic checkpoint.

## Decision

Reuse the dashboard publisher and standalone consumer. Add an independent
dashboard flag to the autonomous runner. Open the native Watch by default,
retaining it after completion. An explicit headless flag disables it, as
requested by the operator. Publish real progress, network
structure, optimizer measurements and physical evaluation diagnostics.
Persist step performance and episode results beside existing CSV files.
Display simulator feedback as evaluation data. Actor observations remain
defined by the environment's observation builder.

Expose PPO rollout, minibatch, epoch, learning-rate and entropy settings.
Keep the original defaults explicit in the command help and run record.
Require a working CUDA installation for cuda and auto requests. CPU runs
require an explicit CPU selection. Record the selected device and versions.
Use a dedicated bounded model benchmark to distinguish neural optimization
cost from full-environment collection cost.

Add evaluation-only execution and verified weight transfer from completed
or intermediate checkpoints. Record archive hashes and environment versions.
Write checkpoints through a temporary archive and retain interruption
metadata. Weight recovery creates a fresh optimizer. Exact restoration of
the environment, RNG, optimizer schedule and unfinished rollout remains a
separate implementation requirement.

## Alternatives

A second dashboard implementation would duplicate graph and loss rendering.
Viewer frame rate does not expose PPO update frequency or learning progress.
Changing PPO defaults silently would make comparison with earlier pilots
ambiguous. Loading an arbitrary archive without checking its schema would
allow incompatible action meanings to pass unnoticed.

## Consequences

Dashboard monitoring uses a separate process and bounded publication rate.
CSV and event records support later analysis. GPU sampling and layer hooks
add overhead that must be measured separately from headless throughput.
A completed learning loop remains distinct from its reported task outcomes.
Interrupted archives support weight transfer only until full resume is
implemented and tested.
