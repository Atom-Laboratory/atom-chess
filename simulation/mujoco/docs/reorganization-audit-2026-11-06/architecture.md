# Proposed experiment organization

Status is audit and mapping proposal, before artifact migration.

## Ownership

~~~text
simulation/mujoco/
  examples/<example>/
    README.md
    run.py
    runs/<run-id>/
  playground/
    README.md
    run.py
    configs/
    sessions/<session-id>/
  training/
    README.md
    grasp-lift/
      README.md
      run.py
      runs/<run-id>/
    camera-manipulation/
      README.md
      run.py
      runs/<run-id>/
  assets/
    bundles/<bundle-id>/
  docs/reorganization-audit-2026-11-06/
    README.md
    inventory.json
    architecture.md
~~~

Each training run retains its configuration, policy, optimizer state, reports,
episode logs and lineage together. Evaluations belong below their originating
run or carry an explicit checkpoint hash and parent-run reference. Splitting
a policy from its run metadata would break the current resume implementations.

Shared assets/bundles contains only reusable model bundles with their manifests
and meshes. Example-specific fixtures remain within the example's run.

## Existing entry points

The fifteen directory entry points currently delegate to scripts beside them.
The Playground implementation is examples/simulation_playground.py, backed by
src/atom_mujoco/playground.py, teleoperation.py, task_plan.py, physical_state.py,
scene_feedback.py, trajectory_execution.py and module_monitor.py. It offers
board and Graveyard selection, manual controls, request-file execution,
trajectory inspection, camera preview and a module activity display.

The dedicated Playground entry point should delegate to this implementation
during migration. Its UI currently writes reports beside its input bundle.
Those output paths must instead use a session directory.

Training scripts are train_visual_grasp.py and train_camera_manipulation.py.
replay_visual_grasp.py is the legacy evaluation/replay entry point. P038 evaluates
through train_camera_manipulation.py --mode evaluate. arena_preview.py is a
training visualization. These remain linked from the examples catalog while
their canonical entry points move into training.

## Path dependencies

Start-MuJoCo.ps1 generates bundles and demo reports under the shared runs root.
Start-RLTraining.ps1 uses that same root for legacy training and its base bundle.
Both resolve the module relative to the script. The RL launcher changes to the
repository root before invoking Python.

The current directory wrappers preserve the original script __file__ through
runpy. They preserve existing source-signature calculations, but relative user
arguments still depend on the terminal working directory.

P038 generated environment.json files contain absolute bundle, library and
layout paths. Its resume signature covers configuration, bundle files, native
libraries and Python sources, including the original training entry point.
Legacy resume verifies environment version, task stage, horizon, model hash,
checkpoint hash and report environment. Merely copying a checkpoint is
insufficient for either workflow.

Historical records must remain immutable. Migration should preserve complete
runs and provide explicit old-to-new path mappings. Before deleting the old
runs root, every retained absolute reference must be supported by a tested
resolver or a compatibility alias. Unresolved artifacts stay in place.

## Wrist and training audit

The interactive-wrist-v1 model has six actuator command entries. Two correspond
to coupled fingers, so six entries do not imply six independent robot degrees
of freedom. The wrist uses a bounded 0 to 2*pi range.

The manual viewer accepts the wrist model. Playground explicitly rejects it.
NativeMotion allocates five output positions and validates two five-position
poses. The exported trajectory validator requires its fixed five-joint list.
P038 declares four actions and five commanded joints in camera_policy.py.
Legacy grasp training also expects four actions. Capture scripts use
five-position observation poses.

No existing policy is established as wrist-capable. Retaining a checkpoint is
distinct from qualifying resume. A five-actuator checkpoint can be considered
for its original environment only after all recorded checks pass. A policy
that learns wrist control requires an explicitly versioned action and
observation contract and a new compatible policy, or validated weight transfer.
Long training remains pending that separate analysis.

## Migration sequence

1. Review the per-entry content evidence and dependency inventory.
2. Resolve uncertain origin and multi-stage runs, preserving their lineage.
3. Introduce canonical entry points and output ownership with regression tests.
4. Copy each approved complete artifact set to a nonexistent destination.
5. Verify every file size and SHA-256 against the audit inventory.
6. Validate model loading, resume checks and references at the new location.
7. Retire each old physical location only after compatibility is verified.

No artifact has been moved by the audit command.
