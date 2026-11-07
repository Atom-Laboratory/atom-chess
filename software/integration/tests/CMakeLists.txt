cmake_minimum_required(VERSION 3.23)

include(FetchContent)

if(NOT TARGET GTest::gtest_main)
    find_package(GTest QUIET)
endif()

if(NOT TARGET GTest::gtest_main)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
    )
    # For Windows MSVC runtime compatibility
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
endif()

add_executable(test_observation_interpreter
    test_observation_interpreter.cpp
)

target_link_libraries(test_observation_interpreter PRIVATE
    acintegration
    GTest::gtest_main
)

add_test(NAME test_observation_interpreter COMMAND test_observation_interpreter)

add_executable(test_board_move_adapter test_board_move_adapter.cpp)
target_link_libraries(test_board_move_adapter PRIVATE acintegration GTest::gtest_main)
add_test(NAME test_board_move_adapter COMMAND test_board_move_adapter)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND STOCKFISH_EXECUTABLE)
    target_compile_definitions(test_board_move_adapter PRIVATE ATOM_TEST_STOCKFISH="${STOCKFISH_EXECUTABLE}")
endif()
