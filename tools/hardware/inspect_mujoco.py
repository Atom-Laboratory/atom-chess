#!/usr/bin/env python3
"""Load an existing ATOM MuJoCo bundle and print its mechanical identifiers."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def names(model, mujoco, object_type, count):
    return [mujoco.mj_id2name(model, object_type, index) for index in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    manifest_path = bundle / "manifest.json"
    model_path = bundle / "model.xml"
    if not manifest_path.is_file() or not model_path.is_file():
        parser.error("bundle must contain manifest.json and model.xml")
    try:
        import mujoco
    except ImportError:
        print("ERROR: MuJoCo Python package is not installed in this interpreter.", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hashes = dict(manifest.get("assets_sha256", {}))
    expected_hashes["model.xml"] = manifest.get("model_sha256")
    for filename, expected in expected_hashes.items():
        path = (bundle / filename).resolve()
        try:
            path.relative_to(bundle)
        except ValueError:
            print(f"ERROR: unsafe bundle path: {filename}", file=sys.stderr)
            return 3
        if not isinstance(expected, str) or not path.is_file():
            print(f"ERROR: missing hash or file: {filename}", file=sys.stderr)
            return 3
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            print(f"ERROR: bundle hash mismatch: {filename}", file=sys.stderr)
            return 3
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    output = {
        "bundle": str(bundle),
        "manifest_schema": manifest.get("schema"),
        "profile": manifest.get("profile", {}).get("name"),
        "tcp_calibrated": manifest.get("tcp_calibrated"),
        "manifest_joints": manifest.get("joints", []),
        "model": {
            "nq": model.nq,
            "nv": model.nv,
            "joints": names(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT, model.njnt),
            "actuators": names(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, model.nu),
            "bodies": names(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, model.nbody),
            "sites": names(model, mujoco, mujoco.mjtObj.mjOBJ_SITE, model.nsite),
        },
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
