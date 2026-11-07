# Phase A validation record

Date: 2026-11-05. Audited source HEAD: `bd435cf3689d284afcc5fab7689359f93f188aa7`.

## Executed

- `git fetch origin`: exit 0; source branch ahead 32, behind 0 at inspection.
- Installed SB3 constructor inspected: version 2.9.2; explicit/default PPO
  settings documented in the audit. Installed NatureCNN source also inspected.
- From repository root:

  ```powershell
  & simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_visual_grasp_env.py -q -p no:cacheprovider
  ```

  Result: **3 passed in 11.56 s**. Covers pixel shape, invalid actions, deterministic
  reset, scripted-lift solvability, fixed camera lookat and fully open grasp reset.
  This is a legacy regression check, not proof of the proposed new architecture.

## Not executed / not established

No C++ rebuild, lateral camera dataset, homography accuracy benchmark, visual
overlay generation, perception adapter test, new-environment leakage test,
conventional pick/place benchmark, new PPO training or hardware trial.
New automated tests are specified in the roadmap and must accompany each code
increment; this change contains documentation only.

Root CMake cache points at a historical source location. OpenCV configured there
exists on disk, but that does not establish a reproducible current C++ build.
Build acvision in a fresh directory in Phase B.

Existing training artifacts were read only. No claims about process liveness are
made from progress.json. No prior experiment or checkpoint was modified.

## Change scope

Only `docs/camera-rl/` and P031 belong to this increment. Pre-existing tracked
changes and untracked CAD/monitor/learning work remain excluded. No push.
