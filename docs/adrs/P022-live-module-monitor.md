# P022 — Module lifecycle trace

## Context

Developers need to identify which orchestration module is active during
chess requests and physical transfers.

## Decision

Expose bounded ModuleMonitor lifecycle events from the Python orchestration
boundary. Events have monotonic timestamps, module, status and detail.
The queue retains 200 events and latest keeps the most recent event per module.
An optional on_event subscriber can consume the trace.

Chess Core validation is observed as one bridge call. Planning, controller,
supervision and confirmed-state transitions emit explicit events.
The trace reports orchestration activity. CPU profiling and a live Tk graph
require separate instrumentation/UI work.

## Validation

Existing Playground/chess regression tests cover normal calls with tracing
enabled. The new camera-RL environment has its own independent pipeline.
