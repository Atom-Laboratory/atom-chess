# ADR-003: TaskPlanner and PhysicalTask as the chess-to-motion boundary

## Status

Proposed for PR #152.

## Context

Chess Core represents a move in domain terms. Motion code needs a stable physical execution model that can express captures and special moves without duplicating chess legality or leaking low-level motor behavior into the Chess Core.

The previous MotionPlanner path also depended on a production CoordinateMapper mock, which made physical integration ambiguous.

## Decision

Introduce `TaskPlanner` as the semantic adapter from a previously validated `ac::chess::Move` to ordered `PhysicalTask` values.

`TaskPlanner`:
- receives the authoritative Board before the move;
- assumes the Move has already been validated;
- uses `CoordinateMapper` for physical board coordinates;
- uses `GraveyardAllocator` for captured-piece destinations;
- emits deterministic physical task ordering;
- never re-runs chess legality;
- never produces motor pulses.

### Task ordering

Normal move:
1. move source piece to destination.

Capture:
1. remove captured piece to Graveyard;
2. move attacker to destination.

En passant:
1. remove the captured pawn from `{from.row, to.col}`;
2. move the attacking pawn.

Castling:
1. move king;
2. move rook.

Promotion:
1. move pawn to destination;
2. emit `PromotionRequired`.

No automatic replacement of the promoted pawn is assumed until physical promotion storage/mechanics are defined.

## Consequences

Special-move physical behavior is explicit and testable.

`MotionPlanner` can focus on generating safe Cartesian trajectories for physical transfers.

The project can change promotion hardware later without changing chess legality.

Production code no longer depends on `CoordinateMapperMock`.

## Review checklist

- Capture ordering must protect the destination square before moving the attacker.
- En-passant must remove the pawn from the physical captured square.
- Castling must generate exactly two physical transfers.
- Promotion must remain explicit until hardware exists.
- Graveyard slots must only be consumed for real captures.
- No `MoveValidator` rules should be duplicated in TaskPlanner.

## Related

- #145
- #147
- #149
- #152
