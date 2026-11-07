# Legacy URDF goal-reaching exercise

This module is an earlier kinematic SAC exercise over the URDF prototype.
The current camera-guided MuJoCo/PPO workflow is documented in
[simulation/mujoco](../mujoco/README.md).

Use a separate Python environment for this module's pinned Gymnasium/SB3
dependencies. Run from the repository root.

~~~powershell
py -3.12 -m venv simulation/learning/venv
$legacyPy = '.\simulation\learning\venv\Scripts\python.exe'
& $legacyPy -m pip install -e 'simulation/learning[test,train]'
& $legacyPy -m pytest simulation/learning/tests -q -p no:cacheprovider
& $legacyPy -m atom_learning.cli --help
~~~

To exercise the training entry point in a new output directory:

~~~powershell
$run = Join-Path simulation/learning/runs ('legacy-' + [guid]::NewGuid().ToString('N'))
& $legacyPy -m atom_learning.cli train --config simulation/learning/config/prototype.json --output $run --steps 1024
~~~

Expected artifacts include model.urdf, config.json, manifest.json, final.zip,
actor.npz and reports. This is a historical goal-reaching example. It provides
no contact-based camera-guided chess manipulation qualification.
