cmake_minimum_required(VERSION 3.23)
project(acintegration LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(${PROJECT_NAME} STATIC
    src/observation_interpreter.cpp
)

target_include_directories(${PROJECT_NAME}
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(${PROJECT_NAME}
    PUBLIC
        acchess
        acvision
)

target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_20)

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

    add_executable(
        test_observation_interpreter
        tests/test_observation_interpreter.cpp
    )
    target_link_libraries(
        test_observation_interpreter
        PRIVATE acintegration GTest::gtest_main
    )
    add_test(
        NAME test_observation_interpreter
        COMMAND test_observation_interpreter
    )
endif()
