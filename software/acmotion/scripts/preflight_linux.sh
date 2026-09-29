#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-}"

echo "=== ATOM Chess acmotion Linux preflight ==="
echo "Kernel: $(uname -srmo)"
echo

for cmd in cmake ninja python3 git; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd -> $(command -v "$cmd")"
  else
    echo "[MISSING] $cmd"
  fi
done

echo
echo "Serial devices detected:"
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "  none detected"

echo
echo "Current user groups:"
id -nG

if [[ -n "$DEVICE" ]]; then
  echo
  echo "Selected device: $DEVICE"
  if [[ ! -e "$DEVICE" ]]; then
    echo "[ERROR] Device does not exist: $DEVICE" >&2
    exit 2
  fi
  stat -c 'owner=%U group=%G mode=%a path=%n' "$DEVICE"
  if [[ -r "$DEVICE" && -w "$DEVICE" ]]; then
    echo "[OK] Current user has read/write access."
  else
    echo "[WARN] Current user lacks read/write access."
    echo "On Debian/Ubuntu, verify membership in the device group (commonly dialout)."
  fi
fi

echo
echo "This script does not send any command to the robot."
