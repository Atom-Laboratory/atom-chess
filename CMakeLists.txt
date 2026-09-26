cmake_minimum_required(VERSION 3.23)

project(ATOMChess)

# Enable CTest once at repository level so tests registered by subprojects
# are discoverable from a single root build. Standalone module builds also
# enable CTest locally in their own CMakeLists.txt files.
include(CTest)

# Core modules currently participating in the repository-level build.
# acmotion is tracked separately because its ROS2/ament boundary still needs
# to be decoupled before it can join this headless CMake graph safely.
add_subdirectory(software/acvision)
add_subdirectory(software/acchess)
