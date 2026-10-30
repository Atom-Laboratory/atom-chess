# ATOM_CONTROL CMAKELISTS.TXT
cmake_minimum_required(VERSION 3.10)
project(atom_control)

find_package(ament_cmake REQUIRED)

find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(control_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(motion REQUIRED)

add_executable(scara_commander
  src/scara_commander.cpp
)

target_link_libraries(scara_commander
  rclcpp::rclcpp
  rclcpp_action::rclcpp_action
  ${control_msgs_TARGETS}
  ${trajectory_msgs_TARGETS}
  ${std_msgs_TARGETS}
  motion::motion
)

install(
  TARGETS scara_commander
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()