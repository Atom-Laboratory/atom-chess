cmake_minimum_required(VERSION 3.23)
project(motion LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(PROJECT_IS_TOP_LEVEL)
  include(CTest)
endif()

# ROS2/ament packaging is optional for the MVP. The reusable motion core must
# build on a plain Linux SBC without requiring a ROS2 installation.
find_package(ament_cmake QUIET)

add_library(${PROJECT_NAME} STATIC
  src/motion_planner.cpp
  src/coordinate_mapper.cpp
)

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

if(MSVC)
  target_compile_options(${PROJECT_NAME} PRIVATE /W4 /WX)
else()
  target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(BUILD_TESTING)
  include(FetchContent)

  if(NOT TARGET GTest::gtest_main)
    find_package(GTest QUIET)
  endif()

  if(NOT TARGET GTest::gtest_main)
    FetchContent_Declare(
      googletest
      GIT_REPOSITORY https://github.com/google/googletest.git
      GIT_TAG v1.14.0
      GIT_SHALLOW TRUE
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
  endif()

  add_executable(test_motion_planner tests/test_motion_planner.cpp)
  target_link_libraries(test_motion_planner PRIVATE motion GTest::gtest_main)
  add_test(NAME test_motion_planner COMMAND test_motion_planner)

  add_executable(test_coordinate_mapper tests/test_coordinate_mapper.cpp)
  target_link_libraries(test_coordinate_mapper PRIVATE motion GTest::gtest_main)
  add_test(NAME test_coordinate_mapper COMMAND test_coordinate_mapper)
endif()

# Keep ROS2 package export/install support when ament is available, but do not
# make ROS2 a prerequisite for the SBC-hosted MVP core.
if(ament_cmake_FOUND)
  ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
  ament_export_include_directories(include)

  install(
    DIRECTORY include/
    DESTINATION include
  )

  install(
    TARGETS ${PROJECT_NAME}
    EXPORT export_${PROJECT_NAME}
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
  )

  ament_package()
endif()
