# ADR-001: CMake and CTest integration

## Problem

Tests were defined inside individual modules, but CTest was not enabled at the
repository root. Hardware and graphical dependencies also made the default test
build unreliable on headless machines.

## Decision

Enable CTest from the root and when a module is configured on its own. Build the
deterministic vision tests by default, keep the camera test opt-in, and register
the Stockfish test only when Stockfish is installed. Use an installed GoogleTest
package when available, with v1.14.0 as the download fallback.

The SFML viewer remains enabled by default and can be disabled with
`ACCHESS_BUILD_VIEWER=OFF` for headless test builds.

## Consequences

`BUILD_TESTING=OFF` excludes test dependencies and targets. Root and standalone
builds expose their registered tests through CTest without requiring camera or
display hardware.
