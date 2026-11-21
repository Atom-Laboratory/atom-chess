# Read-only canonical MuJoCo asset triage

Date: 2026-11-21. Action: Read-Only Triage. Depth: Fast. Articulations: Keep. Passive variant: Skip.

**Verdict: PASS for the limited static and parked canonical-model checks. Dynamic generic audit was unavailable due to tool incompatibility. This is not a complete physics, CAD, hardware, stable-hold or GPU-parity qualification.** No repository assets were edited and no commits were made by this audit.

## Frozen source

- Config: `F:/Users/EHD/Github/Atom/atom-chess/simulation/mujoco/examples/qualify_hybrid_approach/runs/solver-comparison-daeb5509116a43e5a1f770f39e44367d/elliptic10/environment.json`.
- Model: config bundle `model.xml`; SHA-256 `a88b0cdb6c2ac529d443f2bc695d4b94cf8306c2debd81838d06eda6f0790da7`.
- Exact config, manifest, probe and imported source hashes and collection commit: `canonical-probe.json`.
- Canonical probe uses the unchanged project environment: Python 3.12.14, MuJoCo 3.17.0. The official generic audit independently provisioned Python 3.13.13 / MuJoCo 4.0.1 through uv. Those engines were not equated.

## Confirmed measurements

| Property | Observation |
| --- | --- |
| Gravity / timestep | [0, 0, -9.81] m/s² / 0.002 s |
| Solver contact settings | elliptic cone; impratio 10; implicitfast; NoSlip disabled |
| Compiled structure | 11 bodies; 7 joints including pawn free joint; 185 geoms; 83 meshes |
| Active collision geometry | 109 geoms, including 66 gripper convex hulls |
| Independent planner collision pairs | 3,365 |
| Prohibited penetration at configured parked command | None among those checked pairs (negative distance below -1 µm) |
| Invalid dynamic-body inertia triangles | None |
| Pawn model mass / principal inertia | 0.020 kg / [4e-6, 4e-6, 2e-6] kg m² |
| Pawn model inertial position | [0, 0, 0.015] m |
| Finger pad box half sizes | [0.012, 0.006, 0.0015] m |
| Pad friction / contact dimension | [1.2, 0.01, 0.001] / condim 4 |
| Finger position gain / force caps | 150 N/m / [-8, 8] N |
| Pad inner gap at opening 0 | 42.09556 mm |
| Pad inner gap at opening -21 mm | 0.09556 mm |
| Finger coupling | Joint equality with polynomial [0, 1, 0, 0, 0]; two commands are mechanically coupled |
| Wrist | Bounded hinge, [0, 2π] rad; not unrestricted continuous rotation |
| Raw and compiled gripper hull vertex ranges | 16–599; each hull raw count equals its compiled count |
| Hulls above 64 vertices | 44/66; no explicit `maxhullvert` setting; no observed vertex-count truncation |

The pawn mass/inertia, friction, servo gains, pad proxies and coupled-slide model are experimental assumptions, not measured hardware properties. This read-only audit does not replace them with generic product estimates. A high hull vertex count is a GPU CCD memory/throughput risk to measure, not evidence that blindly decimating to 64 vertices preserves function or improves speed.

## Static checker and dynamic tool limitation

The Robotics skill's documented `--static_only` checker returned `passed: true`, with zero errors or warnings. Its mesh topology result listed the official pawn LOD visual (11,946 vertices and 23,882 triangles). See `static-audit.log`.

The generic scenario 6 command did **not** produce a valid articulation scorecard. Its asset-attachment mechanism warned that it was keeping its parent scene's default pyramidal/1 cone/impedance and Euler integrator instead of the model's elliptic/10 and implicitfast settings. It then raised `ValueError: Cannot delete element from an attached mjSpec`. The full warning and traceback are preserved in `scenario6.log`.

Consequently no generic dynamic result is used as evidence about this canonical fixture. The generic checker is designed around a reusable object asset, whereas this target is an assembled fixed-base robot, board, markers and free pawn. Whole-robot drop, stack and external-gripper tests would not be manipulation qualification for this system.

The first scenario CLI attempt also had an argument construction error, corrected before the recorded scenario6 execution. It was not a physical failure. Subsequent probes use artifact cwd. The audit-generated `MUJOCO_LOG.TXT` was positively identified by its 13:07:05 attach-conflict contents/timestamps and moved from repo root to `MUJOCO_LOG-audit-attach-conflicts.TXT`, preserving SHA-256 `b76740533233d38d986886e83fecb3d6d790ced24d1cff459288f554b6563b42`.

## Visual inspection and expected flags

- `canonical-final-six-view.png` shows the whole canonical robot/board state, with separately colored collision geometry, without a gross assembly frame or mm-to-m scale mismatch visible at this inspection resolution.
- `canonical-final-gripper-overlay.png` shows the gripper, pawn and pad/hull regions in visual, distinct-hull and overlay views. The upper arm and board provide cropped context; the target is the gripper. This is a diagnostic image, not surface-distance metrology or a CAD-accuracy certificate.
- Original collision hull alpha is zero, intentionally hidden in the interactive viewer; original visual groups differ from the asset skill's group-2 convention. Only the separate in-memory inspection model's groups and colors were remapped for these renders; source assets stayed unchanged.
- The large floor plane in collision views is expected support geometry, not collider bloat.
- Robot-robot dynamic contact is excluded by the existing robot masks (contype 1, conaffinity 6). The task planner separately checks selected self-collision pairs. A GPU environment must preserve that distinction and its independent safety filters; counting engine contacts alone does not reproduce the planner contract.
- Matching raw and compiled vertex counts does not prove exact mesh/convex-hull surface equality. Quantitative bidirectional surface-fit/cavity metrology was not completed in this fast triage.

## Scope of the current lift evidence

The loaded final snapshot comes from the retained deterministic seed-970000 lift-margin diagnostic. Its source `local-report.json` records a 44.764 mm rise, both pad contacts and `lift_success: true`, with the explicit elliptic/10 solver, load factor 2.5, selected-piece/moving-finger hull near-contact margin 0, all other margins 1 mm and commanded lift travel of 1.5 piece heights. The source state path/hash are in `canonical-probe.json`.

Reloading qpos/qvel/ctrl for the inspection render gives pawn base Z 0.062702 m and retains both contact geometries. Warmstart and complete integration state are absent from that saved snapshot, so reconstructed forces are **not** parity evidence.

The main workstream additionally reported three native physical regression passes on seeds 970100–970102. Those are isolated deterministic tests. Neither the snapshot nor those passes establish an extended stable-hold interval, crowded-board entry, RL policy performance, hardware readiness or GPU/CPU parity. The populated-board gripper insertion problem remains a separate unresolved gate.

## Reproduction

Run from this outside-repository artifact directory:

```powershell
$skill = 'C:/Users/maria/.gemini/config/plugins/robotics/skills/mujoco-audit/scripts/audit_scenarios.py'
$xml = 'F:/Users/EHD/Github/Atom/atom-chess/simulation/mujoco/examples/qualify_hybrid_approach/runs/solver-comparison-daeb5509116a43e5a1f770f39e44367d/elliptic10/bundle/model.xml'
& uv run $skill "--xml_path=$xml" --static_only
# Known generic tooling failure, retained for reproducibility:
& uv run $skill "--xml_path=$xml" '--out_dir=C:/Users/maria/.codex/artifacts/atom-mjwarp-20261121/model-audit/audit_out' --label=atom_isolated_gripper --scenarios=6
& 'F:/Users/EHD/Github/Atom/atom-chess/simulation/mujoco/.venv/Scripts/python.exe' -B ./scratch/canonical_probe.py
```

The probe has frozen default config/state paths and optional `--config` / `--state` overrides. Its source and imported repository source hashes are in the JSON. The source XML hash was checked again after probing and remained unchanged.
