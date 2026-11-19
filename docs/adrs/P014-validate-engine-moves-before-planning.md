# P014 — Validate engine moves before physical planning

## Context

The Stockfish transport validates response syntax. The existing Chess Core
validator accepts observed board transitions. Neither path connects an engine
proposal to physical task planning.

## Decision

Decode standard UCI coordinates in Chess Core. Derive the candidate flags from
the authoritative board and reuse the existing movement and king-safety checks.
The integration layer serializes the board to FEN, asks the existing UCI session
for a move and calls TaskPlanner only with a validated move. Return the move
and tasks for later execution. The caller confirms and applies the logical move
after physical verification.

## Alternatives and consequences

Synthesizing an observation would conflate an engine proposal with sensor
evidence. A second set of chess rules would diverge from observation validation.
The new path keeps the board const and distinguishes a terminal engine response
from transport failure and a rejected engine move. TaskPlanner retains ownership
of capture ordering and its existing allocator semantics. Physical execution
and reconciliation are separate from this boundary.
