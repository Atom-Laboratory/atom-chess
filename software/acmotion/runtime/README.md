# Native MotionPlanner and IK adapter

motion_runtime.cpp exposes the existing C++ MotionPlanner::planTask and
InverseKinematics to the P038 Python environment. World endpoints use
millimetres at this ABI. The Python adapter derives robot mapping and limits
from static MuJoCo geometry and verifies the IK result against FK.

Build from the repository root after configuring the native targets.

~~~powershell
cmake --build build/p038-core --config Release --target motion_runtime
~~~

Follow the [MuJoCo README](../../../simulation/mujoco/README.md) to prepare a
one-piece P038 fixture. Set P038_CONFIG to its environment.json, then run:

~~~powershell
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_camera_manipulation.py -q -p no:cacheprovider
~~~

The current simulation profile has five actuators and omits the physical wrist
rotation. Its C++ solver's auxiliary J3 value has no simulated actuator.
Adding the wrist requires a new explicit geometry/control contract.
