#!/usr/bin/env python3
"""Read-only serial monitor for ATOM Chess motion-controller bring-up.

This tool intentionally never writes to the serial port. Use it to verify
firmware startup output and ACM1 responses while motor power is disabled.
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
except ImportError as exc:
    raise SystemExit(
        "pyserial is required. Install python3-serial or pip install pyserial."
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only serial monitor for the ATOM Chess ESP32-S3."
    )
    parser.add_argument("--device", required=True, help="e.g. /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help="serial read timeout in seconds",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(
        f"[serial-monitor] opening {args.device} at {args.baud} baud "
        "(read-only behavior: this script sends no protocol commands)",
        file=sys.stderr,
    )

    with serial.Serial(
        port=args.device,
        baudrate=args.baud,
        timeout=args.timeout,
    ) as port:
        while True:
            raw = port.readline()
            if not raw:
                continue

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            text_line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            print(f"{timestamp} {text_line}", flush=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[serial-monitor] stopped", file=sys.stderr)
