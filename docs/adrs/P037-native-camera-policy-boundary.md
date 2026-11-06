# P037 — Persistent native camera and policy boundary

## Context

P036 established paired feasibility. The existing VisualGraspEnv reset reads
piece truth and places the arm using oracle IK. Its camera-only observations
therefore rely on an oracle initialization. The offline executable also incurs
process and image-file overhead per observation.

## Decision

Expose the existing native offline orchestration through an optional C ABI
shared runtime. Python sends only contiguous RGB and explicit reference layout.
Keep a context per worker, use actual acvision classes and return rectified RGB,
geometry and candidate labels. Expose experimental foreground evidence only
after an explicitly supplied RGB empty-board frame. Missing geometry clears
all frame outputs and invalid empty reference clears stored background.

Build a strict policy-input object containing image/task/command history and
perception validity/freshness. It accepts no simulator, body poses, reward or
measured joint truth. Simulation state remains in acquisition/evaluation adapters.
Preserve the old environment and its checkpoints.

## Alternatives

Per-step subprocesses impose measured startup/export overhead. A Python vision
rewrite diverges from acvision. A pybind11 dependency is unavailable locally.
A small versioned C ABI reuses the same library with Python ctypes.

## Consequences

Native contexts are single-call resources serialized by the Python adapter.
This increment enables a continuous camera-to-policy path. It does not qualify
piece pose or close the deterministic full-transfer gates. Training must retain
those explicit requirements. The native runtime uses experimental ideal-camera
geometry until physical calibration is measured.
