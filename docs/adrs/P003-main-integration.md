# P003 — Integrate main while preserving simulation

Date: 2026-10-30. Status: accepted. Complements P001/P002.

## Context

The owner explicitly requested main integration and MuJoCo as the primary simulator.
Initial simulation HEAD: 948f16a; origin/main: f72c893. Fetch confirmed references.
Preexisting untracked simulation/learning was preserved outside commits.

## Decision

Use a normal two-parent merge (8fbc7aa), without rebase or force push. Root CMake
includes main's four software modules; acvision uses main's current CMake and
migrated chess-domain tests. README retains simulation navigation and main's
project/license description. The moved Dockerfile is retained as legacy.
Operational ROS sources remain simulation/src; nested packages inherited from
main are not the validated entry point. No simulation sources were discarded.

Treat motion as an ordinary CMake target in root builds, even when ROS is sourced.
Restrict ament discovery/export to standalone builds: automatic export previously
failed because acchess was missing from the export set. Standalone motion ROS
packaging remains pending and unverified.

## Verification and consequences

After merge: 15 C++ CTest suites, 13 ROS pytest cases in four suites, and the
original 13 MuJoCo tests passed. After the CMake correction, root C++ tests passed
with ROS sourced. Stockfish was absent; its UCI test was not registered. Firmware
and hardware were not tested. These results do not establish an autonomous game.
Windows case-collision deletions were rematerialized from HEAD after merge;
preexisting user work was preserved. Legacy logs/whitespace were not mass-reformatted.
