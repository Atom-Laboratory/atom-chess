# CI/CD Quality Gate

## Scope

The repository CI is implemented in `.github/workflows/ci.yml` and runs for pull requests targeting `main`, pushes to `main`, and manual dispatches.

The pipeline is intentionally headless and does not require physical camera hardware. Hardware-dependent camera tests are excluded from the default CI gate and must remain available for explicit hardware validation.

## Required jobs

The following jobs are intended to be required before merging into `main`:

- `Build & Test (gcc)`
- `Build & Test (clang)`
- `Static Analysis`
- `Coverage`

The build matrix compiles with GCC and Clang using CMake/Ninja and promotes compiler warnings to errors.

Static analysis runs both `cppcheck` and `clang-tidy`. Any analysis error fails the workflow.

Coverage is collected with GCC/gcov/lcov. System headers, fetched dependencies, and test implementation files are excluded from the final LCOV artifact.

## Branch protection / repository rules

A workflow can report failing checks, but GitHub only prevents maintainers from merging a failing pull request when the repository branch protection or ruleset marks those checks as required.

After this workflow has completed successfully at least once, configure the `main` branch ruleset with:

1. Require a pull request before merging.
2. Require approvals from CODEOWNERS / maintainers as appropriate.
3. Require status checks to pass before merging.
4. Require the four CI jobs listed above.
5. Require branches to be up to date before merging.
6. Block force pushes and branch deletion for `main`.

This repository setting is intentionally not encoded as a workflow permission because GitHub Actions should not be able to weaken its own merge protection.

## Dependency policy

CI installs build tools and system packages from the Ubuntu runner repositories. Project dependencies fetched by CMake should be pinned to explicit versions/tags.

## Test policy

Deterministic unit and integration tests belong in the default CTest graph.

Tests that require physical hardware must be opt-in and must not make the normal pull-request gate nondeterministic.

Stockfish-dependent tests should be conditional on Stockfish availability, but chess-domain unit tests must not be hidden behind that condition.

## Failure policy

Compilation errors, compiler warnings promoted to errors, test failures, static-analysis findings configured as errors, and coverage-generation failures all fail the associated job. No CI job uses `continue-on-error`.
