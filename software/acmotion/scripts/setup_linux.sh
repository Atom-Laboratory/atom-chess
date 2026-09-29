#!/usr/bin/env bash
set -euo pipefail

echo "[acmotion] Installing Linux development dependencies..."

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required for package installation." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y \
  build-essential \
  clang \
  clang-tidy \
  cmake \
  ninja-build \
  cppcheck \
  git \
  python3 \
  python3-serial \
  libopencv-dev \
  stockfish \
  libx11-dev \
  libxrandr-dev \
  libxcursor-dev \
  libxi-dev \
  libudev-dev \
  libgl1-mesa-dev \
  libfreetype6-dev \
  libogg-dev \
  libvorbis-dev \
  libflac-dev

echo
echo "[acmotion] Tool versions:"
cmake --version | head -n1
ninja --version
"${CXX:-g++}" --version | head -n1
python3 --version

echo
echo "[acmotion] Setup complete."
echo "Run: bash software/acmotion/scripts/build_and_test.sh"
