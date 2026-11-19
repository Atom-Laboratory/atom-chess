# P036 — Experimental perception qualification

## Context

P033 and P034 use different capture conditions and orientation conventions.
P035 foreground coverage remains low. The user requests a reproducible
qualification layer before algorithm work, with preservation of historical data.

## Decision

Preserve native perception unchanged. Reproduce the nine-view P033 and 27-frame
P034 protocols in exclusive output directories. Add an opt-in evaluator-only
export to P034 capture and a saved-image paired runner. Both detector variants
receive identical RGB files. Ground truth is loaded only after native execution.
Use the existing evaluator for orientation-invariant geometric diagnostics,
and separately report named-square addressing when orientation is available.
Archive identities, commands, per-frame failures, overlays and latency scope.

## Alternatives

Historical aggregate comparisons conflate resolution, pose and estimator.
Reimplementing perception in Python would invalidate module parity.
Adding new detectors or camera fusion before this qualification would confound
the first comparison.

## Consequences

Historical reproduction is assessed against hashes and numeric results.
Elapsed subprocess time includes startup, decoding and artifact export.
Missing historical latency or raw corner correspondences remains unavailable.
Mechanical error budgets need physical measurements. This increment stops
after the first paired feasibility study. No commit or push is authorized.
