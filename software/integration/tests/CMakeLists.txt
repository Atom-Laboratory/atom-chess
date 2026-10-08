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