add_library(acintegration
    src/board_move_adapter.cpp
    src/engine_turn_planner.cpp
    src/observation_interpreter.cpp
)

target_include_directories(acintegration PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(acintegration PUBLIC
    acchess
    acvision
    motion
)

target_compile_features(acintegration PUBLIC cxx_std_20)

if(BUILD_TESTING)
    add_subdirectory(tests)
endif()

add_executable(export_mujoco_trajectory src/export_mujoco_trajectory.cpp)
target_link_libraries(export_mujoco_trajectory PRIVATE motion)
