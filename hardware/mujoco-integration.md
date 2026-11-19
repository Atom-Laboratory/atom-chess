# MuJoCo integration and hardware mapping

## Model ownership

The [MuJoCo module](../simulation/mujoco/README.md) owns the mechanical
simulation. Hardware inventory and assembly records reference its identifiers.

The simulation is an experimental model, not proof of physical geometry,
dynamics, reach, collision safety, motor capability, or calibration.

## Dependencies and launch

The current package requires Windows PowerShell, Python 3.12, MuJoCo 3.17.0, and
NumPy 2.x. Pytest is optional for tests. Installation instructions and the pinned
Windows environment are maintained by `simulation/mujoco/README.md` and
`simulation/mujoco/requirements-windows-py312.lock`.

After preparing `simulation/mujoco/.venv`, launch the Playground from the
repository root:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
```

The launcher starts `simulation/mujoco/playground/run.py` and builds its default
bundle under `simulation/mujoco/assets/bundles/playground-fingertip-only-v1` when
needed. The bundle contains `model.xml`, mesh assets and `manifest.json`. Use a
fresh directory under `simulation/mujoco/runs/` for custom builds. Keep the
manifest with the bundle to retain source, model, configuration and asset
identities.

| Workflow | Scope |
| --- | --- |
| [Chess Playground](../simulation/mujoco/playground/README.md) | Interactive chess tasks using the five-actuator bundle |
| Manual viewer (`-Mode view`) | Defaults to the separate wrist-enabled bundle |
| [Legacy v3 pixel training](../simulation/mujoco/training/grasp-lift/README.md) | Historical grasp and lift experiments with their own fixtures |
| [P038 camera manipulation](../simulation/mujoco/training/camera-manipulation/README.md) | Native vision and residual control with task-specific bundles |

## Model source and representation

The bundle generator reads `simulation/src/urdf/atom.urdf.xacro` as the current
robot-description source and supports a constrained URDF subset. It creates one
MuJoCo body per link, one joint for each non-fixed URDF joint, mesh geoms, and a
position actuator per controlled joint.

Current URDF-derived joints are:

| Simulation joint | Type | Parent → child | Hardware mapping |
| --- | --- | --- | --- |
| `joint_base_to_link1` | revolute | `base_link` → `z_axis_link` | unresolved |
| `joint_z_axis_arm1` | prismatic | `z_axis_link` → `arm1_link` | unresolved |
| `joint_arm1_link_arm2_link` | revolute | `arm1_link` → `arm2_link` | unresolved |

The interactive profile adds `finger_1` and `finger_2` prismatic joints and
position actuators. An equality constraint couples the simulated fingers. These
are a mesh-aligned gripper approximation, not evidence of two physical motors or
of the servo linkage.

Wrist-enabled bundles additionally expose the revolute joint `wrist_joint` and its
position actuator `wrist_position`. The assembly records this joint as unresolved.

The generated manifest is authoritative for a specific
bundle. Inspect it after every rebuild.

## Non-interactive inspection

Once a bundle exists and the MuJoCo environment is installed:

```powershell
& ./simulation/mujoco/.venv/Scripts/python.exe tools/hardware/inspect_mujoco.py `
  --bundle simulation/mujoco/assets/bundles/playground-fingertip-only-v1
```

The command verifies manifest/model presence and recorded model and asset hashes, loads
the MJCF without a viewer, and prints joints,
actuators, bodies, and sites. It does not render or assess physical correctness.

## Parameters useful for future mapping

The following can be extracted without claiming physical calibration:

- stable joint, actuator, body, geom, and site names;
- joint type, axis, software range, and URDF reference velocity;
- link hierarchy and mesh asset provenance;
- world/URDF frame transform;
- board-square and graveyard site locations;
- simulated tool/frame poses;
- timestep and experimental control profile;
- model, source, and asset hashes.

Before mapping any physical component, separately confirm motor labels, driver
variant and sense resistor, transmission ratio, direction, zero reference,
travel/angle limits, link dimensions, TCP offset, gripper linkage, masses, and
inertias. Record evidence in this workspace and change `mapping_status` from
`unresolved` only after explicit project-owner confirmation.
