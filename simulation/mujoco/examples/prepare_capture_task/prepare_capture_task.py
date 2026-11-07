"""Create an exclusive two-piece ATOM capture-task fixture.

This script prepares MuJoCo assets and a capture-task description. It does NOT
implement capture execution in camera_manipulation_env.py or train_camera_manipulation.py.
The Graveyard destination uses an existing slot from the matching bundle.
"""

import argparse
from atom_mujoco.virtual_camera import DEFAULT_REFERENCE_LAYOUT
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from atom_mujoco.backend import Simulation
import numpy as np


def square_xy(square: str, center: np.ndarray, pitch: float) -> np.ndarray:
    if (
        len(square) != 2
        or square[0] not in "abcdefgh"
        or square[1] not in "12345678"
    ):
        raise ValueError(f"Invalid algebraic square: {square!r}")

    return center[:2] + np.array(
        [
            (ord(square[0]) - ord("a") - 3.5) * pitch,
            (int(square[1]) - 4.5) * pitch,
        ],
        dtype=float,
    )


def set_body_square(body: ET.Element, square: str, center: np.ndarray, pitch: float):
    pos_text = body.get("pos")
    if not pos_text:
        raise ValueError(f"Piece body {body.get('name')!r} has no explicit pos")

    position = np.array([float(value) for value in pos_text.split()], dtype=float)
    if position.shape != (3,):
        raise ValueError(f"Piece body {body.get('name')!r} must have a 3D pos")

    position[:2] = square_xy(square, center, pitch)
    body.set("pos", " ".join(format(float(value), ".9g") for value in position))


def prepare(
    bundle,
    reference_scene,
    layout,
    output,
    *,
    attacker_piece,
    attacker_source,
    attacker_target,
    captured_piece,
    captured_source,
    graveyard_slot,
    graveyard_position,
    obstacles=(),
):
    bundle = Path(bundle)
    reference_scene = Path(reference_scene)
    layout = Path(layout)
    output = Path(output)

    if attacker_piece == captured_piece:
        raise ValueError("Attacker and captured piece must have different identities")
    if attacker_source == attacker_target:
        raise ValueError("Attacker source and target must be different squares")
    if captured_source != attacker_target:
        raise ValueError(
            "For a standard capture, captured_source must equal attacker_target"
        )

    # Validate all board-square strings before touching the output directory.
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    pieces_by_name = {
        item["name"]: item
        for item in manifest.get("pieces", [])
        if "name" in item
    }
    missing = [
        name
        for name in (attacker_piece, captured_piece)
        if name not in pieces_by_name
    ]
    if missing:
        available = ", ".join(sorted(pieces_by_name))
        raise ValueError(
            f"Piece(s) not found in manifest: {missing}. "
            f"Available pieces: {available}"
        )

    scene = manifest["scene"]
    pitch = float(scene["square_size_m"])
    center = np.asarray(scene["board_center_m"], dtype=float)
    if center.shape != (3,):
        raise ValueError("manifest scene.board_center_m must contain 3 values")

    square_xy(attacker_source, center, pitch)
    square_xy(attacker_target, center, pitch)
    square_xy(captured_source, center, pitch)

    slots = scene.get("graveyard_slots", {})
    assigned_slot = pieces_by_name[captured_piece].get("graveyard_slot")
    graveyard_slot = graveyard_slot or assigned_slot
    if graveyard_slot not in slots:
        raise ValueError(f"Unknown Graveyard slot: {graveyard_slot!r}")
    if assigned_slot in slots and graveyard_slot != assigned_slot:
        raise ValueError(f"Captured piece is assigned to {assigned_slot!r}")
    slot_position = np.asarray(slots[graveyard_slot], dtype=float)
    if graveyard_position is not None and not np.allclose(
        graveyard_position, slot_position, rtol=0, atol=1e-9
    ):
        raise ValueError("Explicit position must match the bundle's Graveyard slot")
    graveyard_position = slot_position

    tree = ET.parse(reference_scene)
    root = tree.getroot()
    world = root.find("worldbody")
    if world is None:
        raise ValueError("Reference scene has no worldbody")

    if world.find(f".//site[@name='graveyard_center_{graveyard_slot}']") is None:
        raise ValueError("Reference scene lacks the configured Graveyard slot")
    if root.find("./asset/texture[@name='reference_0']") is None:
        raise ValueError("Expected marker scene from validate_board_reference.py")

    retained_names = {attacker_piece, captured_piece}
    occupied = {attacker_source, captured_source}
    neighbors = []
    for spec in obstacles:
        name, separator, square = spec.partition("@")
        if (not separator or name not in pieces_by_name
                or name in retained_names or square in occupied):
            raise ValueError(f"Invalid or duplicate obstacle: {spec}")
        square_xy(square, center, pitch)
        retained_names.add(name)
        occupied.add(square)
        neighbors.append((name, square, "neighbor"))
    found_bodies = {}
    for body in list(world.findall("body")):
        if body.find("freejoint") is not None:
            name = body.get("name")
            if name in retained_names:
                found_bodies[name] = body
            else:
                world.remove(body)

    missing_bodies = sorted(retained_names - set(found_bodies))
    if missing_bodies:
        raise ValueError(
            f"Piece body/bodies not found as direct worldbody children: {missing_bodies}"
        )

    set_body_square(found_bodies[attacker_piece], attacker_source, center, pitch)
    set_body_square(found_bodies[captured_piece], captured_source, center, pitch)

    for name, square, _ in neighbors:
        set_body_square(found_bodies[name], square, center, pitch)

    # Create output only after input validation. Existing experiments are never overwritten.
    output.mkdir(parents=True, exist_ok=False)

    assets = {}
    for node in root.findall("./asset/*"):
        asset_file = node.get("file")
        if not asset_file:
            continue

        source_path = Path(asset_file)
        if not source_path.is_absolute():
            source_path = reference_scene.parent / source_path
        if not source_path.is_file():
            raise FileNotFoundError(f"Referenced MuJoCo asset not found: {source_path}")

        destination = output / source_path.name
        if destination.exists() and destination.read_bytes() != source_path.read_bytes():
            raise ValueError(f"Asset filename collision: {source_path.name}")
        if not destination.exists():
            shutil.copyfile(source_path, destination)

        node.set("file", source_path.name)
        assets[source_path.name] = hashlib.sha256(destination.read_bytes()).hexdigest()

    model_path = output / "model.xml"
    tree.write(model_path, encoding="utf-8", xml_declaration=True)

    # Preserve every retained piece and its fixture role.
    selected_manifest_pieces = []
    for name, initial_square, role in (
        (attacker_piece, attacker_source, "attacker"),
        (captured_piece, captured_source, "captured"),
        *neighbors,
    ):
        item = dict(pieces_by_name[name])
        item["initial_square"] = initial_square
        item["capture_role"] = role
        selected_manifest_pieces.append(item)

    derived_manifest = dict(manifest)
    derived_manifest["pieces"] = selected_manifest_pieces
    derived_manifest["fixture_kind"] = "two_piece_capture"
    derived_manifest["assets_sha256"] = assets
    derived_manifest["model_sha256"] = hashlib.sha256(
        model_path.read_bytes()
    ).hexdigest()
    (output / "manifest.json").write_text(
        json.dumps(derived_manifest, indent=2), encoding="utf-8"
    )
    shutil.copyfile(layout, output / "reference-layout.json")

    capture_task = {
        "schema": 1,
        "task_type": "capture",
        "status": "fixture_prepared",
        "attacker": {
            "piece": attacker_piece,
            "source": attacker_source,
            "target": attacker_target,
        },
        "captured": {
            "piece": captured_piece,
            "source": captured_source,
            "target": {
                "type": "graveyard_slot",
                "slot": graveyard_slot,
                "position_world_m": graveyard_position.tolist(),
            },
        },
        "operations": [
            {
                "sequence": 1,
                "piece": captured_piece,
                "source": captured_source,
                "destination": {
                    "type": "graveyard_slot",
                    "slot": graveyard_slot,
                    "position_world_m": graveyard_position.tolist(),
                },
            },
            {
                "sequence": 2,
                "piece": attacker_piece,
                "source": attacker_source,
                "destination": attacker_target,
            },
        ],
        "notes": [
            "The scene starts with both pieces on the board.",
            "The Graveyard support is inherited from the reference scene.",
            "The existing one-piece camera environment does not automatically execute these operations.",
            "Use playground_request.json with the supervised Playground.",
        ],
    }
    capture_task_path = output / "capture_task.json"
    capture_task_path.write_text(
        json.dumps(capture_task, indent=2), encoding="utf-8"
    )

    request_path = output / "playground_request.json"
    request = {
        "schema": 2,
        "operation": "PLAN",
        "transfers": [
            {"source": captured_source, "target": f"graveyard:{graveyard_slot}"},
            {"source": attacker_source, "target": attacker_target},
        ],
    }
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")

    Simulation(output)
    print(f"Validated capture fixture: {output}")
    print(f"Playground request: {request_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--reference-scene", type=Path, required=True)
    parser.add_argument("--layout", type=Path, default=DEFAULT_REFERENCE_LAYOUT)
    parser.add_argument("--output", type=Path, required=True)

    parser.add_argument("--attacker-piece", required=True)
    parser.add_argument("--attacker-source", required=True)
    parser.add_argument("--attacker-target", required=True)

    parser.add_argument("--captured-piece", required=True)
    parser.add_argument("--captured-source", required=True)

    parser.add_argument("--graveyard-slot", help="Defaults to the captured piece’s assigned slot")
    parser.add_argument(
        "--graveyard-position",
        type=float,
        nargs=3,
        metavar=("X_M", "Y_M", "Z_M"),
        help="Optional check against the existing slot position, in world metres",
    )

    parser.add_argument("--obstacle", action="append", default=[], help="Physical piece@initial_square, repeatable")
    args = parser.parse_args()
    prepare(
        args.bundle,
        args.reference_scene,
        args.layout,
        args.output,
        attacker_piece=args.attacker_piece,
        attacker_source=args.attacker_source,
        attacker_target=args.attacker_target,
        captured_piece=args.captured_piece,
        captured_source=args.captured_source,
        graveyard_slot=args.graveyard_slot,
        graveyard_position=args.graveyard_position,
        obstacles=args.obstacle,
    )


if __name__ == "__main__":
    main()
