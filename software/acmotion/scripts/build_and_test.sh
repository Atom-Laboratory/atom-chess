#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
BUILD_TYPE="${BUILD_TYPE:-Debug}"

echo "[acmotion] Repository: $ROOT_DIR"
echo "[acmotion] Build dir:   $BUILD_DIR"
echo "[acmotion] Build type:  $BUILD_TYPE"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -G Ninja \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DACCHESS_BUILD_VIEWER=OFF \
  -DACVISION_BUILD_HARDWARE_TESTS=OFF

cmake --build "$BUILD_DIR" --parallel

echo
echo "[acmotion] Running repository tests..."
ctest --test-dir "$BUILD_DIR" --output-on-failure

echo
echo "[acmotion] Running motion-focused tests..."
ctest --test-dir "$BUILD_DIR" --output-on-failure \
  -R "motion|task|graveyard|coordinate|inverse"

echo
echo "[acmotion] Build and tests completed successfully."
