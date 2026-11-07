# Verifiable roadmap

1. Completed: merge main f72c893 into simulation, preserving both histories and
   local work; 15 C++ suites and 13 ROS cases passed.
2. Completed: direct MuJoCo experiment infrastructure, configurable synthetic
   parameters/tool point, explicit Task/Episode and local provenance; 25 tests pass.
3. Next personal step: inspect joints, select the tool frame, specify observations,
   actions, reward, success/failure and metrics; implement and test Task.
4. Add Gymnasium only after spaces are selected; validate with its checker.
5. Compare conventional control with personally developed learning on held-out
   goals/seeds. Training requires explicit participation by the owner.
6. Extract authoritative CAD frames/zeros/limits/TCP/linkage, masses/inertias and
   actuator data; implement reviewed collision geometry and contact validation.
7. Validate gripper/J3 and physical pieces before grasping; validate feedback,
   homing, limits and independent stop behavior before hardware deployment.

MuJoCo is primary. Legacy Gazebo remains available as historical code, with no
current dependency justifying a second primary simulator. Full robot fidelity,
ROS bridge, standalone motion ROS packaging, Stockfish integration validation,
firmware and physical bench tests remain pending.
