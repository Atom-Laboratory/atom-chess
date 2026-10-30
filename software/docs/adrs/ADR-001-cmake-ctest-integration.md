# ADR-001: CMake and CTest integration

## Status

Accepted for PR #106.

## Context

Tests were defined inside individual modules, but CTest was not consistently enabled from the repository root. Hardware and graphical dependencies also made the default test build unreliable on headless machines.

The chess module additionally integrates with an external Stockfish executable. That integration dependency must not suppress deterministic chess-domain unit tests when Stockfish is unavailable.

## Decision

Enable CTest from the repository root and when a module is configured on its own.

For acvision:
- build deterministic vision tests by default;
- keep camera/hardware tests opt-in;
- resolve fixture paths independently of the current working directory.

For acchess:
- register deterministic chess-domain tests whenever `BUILD_TESTING=ON`;
- use an installed GoogleTest package when available, with GoogleTest v1.14.0 as the pinned FetchContent fallback;
- register only the Stockfish UCI integration test conditionally when the Stockfish executable is available.

The SFML viewer remains enabled by default for developer builds and can be disabled with `ACCHESS_BUILD_VIEWER=OFF` for headless CI/builds.

GitHub Actions is intentionally out of scope for PR #106 and is tracked separately by #131 / PR #133.

## Consequences

`BUILD_TESTING=OFF` excludes test dependencies and targets.

Root and standalone builds expose deterministic tests through CTest without requiring camera hardware, a display, or Stockfish.

Stockfish absence is reported explicitly and only skips the external-engine integration test.

Future Chess Core tests (for example Board, comparator, FEN and move application tests introduced by PR #85) can be added to the deterministic CTest graph without inheriting the Stockfish dependency.

## Related

- #24
- #132
- PR #85
- PR #133
