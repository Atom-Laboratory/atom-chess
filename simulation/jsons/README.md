# Physical task request example

test.json is a schema-2 PLAN request containing a short transfer sequence.
It is consumed through the existing Chess Core request-file action in the
interactive Playground.

Open the Playground from the repository root.

~~~powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
~~~

Choose Execute Chess Core request file and select simulation/jsons/test.json.
Inspect the resulting operation records for success or rejection.
This example exercises the Playground integration. Camera-guided RL uses the
separate [P038 task environment](../mujoco/README.md).
