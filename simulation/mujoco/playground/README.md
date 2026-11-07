# Interactive Playground

Run from the repository root after installing the MuJoCo environment.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py simulation/mujoco/playground/run.py --bundle simulation/mujoco/assets/bundles/playground-fingertip-only-v1
~~~

The interface includes board and Graveyard selection, manual controls, trajectory
inspection, native requests, camera preview and module activity monitoring.
New interactive reports are written to playground/sessions/<unique-id>/.
Use --session-dir to choose an explicit session directory.
Headless execution retains its explicit --output argument.

The input bundle above is preserved at its historical location during migration.
The five-actuator Playground currently rejects wrist-enabled bundles. The
manual wrist viewer is documented in the module README.

Verify the entry point with --help. Run regression tests with
python -m pytest simulation/mujoco/tests/test_playground.py -q.
GUI opening and interactive session persistence still require migration validation.
