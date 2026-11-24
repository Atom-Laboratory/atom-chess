# Architecture and integration boundaries

The root CMake now builds software/acvision, acchess, acmotion and integration
from merged main f72c893. Passing module tests do not establish a complete game
application. Vision observations, legal chess state, task planning and motion
execution have separate responsibilities.

The operational ROS description is simulation/src: URDF and joint states feed
robot_state_publisher/TF/RViz. Its kinematic controller is separate from physics.
Nested ROS packages inherited from main are legacy, not the validated launch path.

MuJoCo is the primary experiment simulator. URDF -> portable MJCF/assets/manifest
-> Simulation.reset/advance/observe/frame_pose -> optional Episode with a
researcher Task -> local JSON records. No ROS call is required per physics step.
A ROS bridge remains optional future work, requiring names/units/frames and one
command owner. There is no ROS/MuJoCo state synchronization today.

The model has 2R+Z, synthetic dynamics, disabled gravity/contacts, visual fixed
gripper/pieces and no calibrated TCP. An explicit experimental tool offset is
available for study. acmotion expects 3R+Z+gripper and cannot be mapped completely.
Future learned strategies must pass independent command validation before motion
execution. No hardware transport or automatic learned-policy deployment exists.

See the MuJoCo integration report and ADR P003/S005 for verified tests and gaps.
