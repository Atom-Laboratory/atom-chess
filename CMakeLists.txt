cmake_minimum_required(VERSION 3.23)

project(ATOMChess)

# Enable CTest once at repository level so tests registered by subprojects
# are discoverable from a single root build. Standalone module builds also
# enable CTest locally in their own CMakeLists.txt files.
include(CTest)

# Linux SBC-hosted software modules participating in the repository-level build.
# Low-level ESP32 firmware remains a separate embedded target and is intentionally
# not part of this CMake graph.
add_subdirectory(software/acvision)
add_subdirectory(software/acchess)
add_subdirectory(software/acmotion)
