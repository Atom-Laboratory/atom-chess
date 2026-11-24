# Persistent acvision RGB runtime

This C ABI calls the existing native perception pipeline from Python without
starting a process for each frame. native_runtime.h defines the versioned ABI.
Each worker owns an independent context. Input is contiguous uint8 RGB.
Output includes geometry, candidate labels and 800x800 rectified RGB.

Build from the repository root.

~~~powershell
cmake -S . -B build/p038-core -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=OFF -DACCHESS_BUILD_VIEWER=OFF -DACVISION_NATIVE_RUNTIME=ON -DACMOTION_NATIVE_RUNTIME=ON
cmake --build build/p038-core --config Release --target acvision_runtime perception_image
~~~

Configure an RGB fixture and layout using the
[MuJoCo examples README](../../../simulation/mujoco/examples/README.md), then run:

~~~powershell
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_native_runtime.py -q -p no:cacheprovider
~~~

Expected checks cover native CLI parity, invalid buffers, missing references,
independent contexts, immutable observations and actor-input isolation.
See [P037](../../../docs/camera-rl/P037-native-camera-policy.md) for the contract.
