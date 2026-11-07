cmake_minimum_required(VERSION 3.10)
project(atom_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
install(PROGRAMS scripts/kinematic_controller.py DESTINATION lib/${PROJECT_NAME})
install(
  DIRECTORY urdf meshes launch rviz
  DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(description test/test_description.py TIMEOUT 30)
  ament_add_pytest_test(headless_launch test/test_headless_launch.py TIMEOUT 45)
  ament_add_pytest_test(control_core test/test_control_core.py TIMEOUT 30)
  ament_add_pytest_test(control_launch test/test_control_launch.py TIMEOUT 60)
endif()

ament_package()
