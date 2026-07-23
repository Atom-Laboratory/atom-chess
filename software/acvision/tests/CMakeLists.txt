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

include(GoogleTest)

function(add_acvision_test test_name)
    add_executable(${test_name} ${test_name}.cpp)

    target_link_libraries(${test_name}
        PRIVATE
            acvision
            GTest::gtest_main
            ${ARGN}
    )

    set_target_properties(${test_name} PROPERTIES FOLDER "Tests")

    if(WIN32)
        add_custom_command(TARGET ${test_name} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                $<TARGET_RUNTIME_DLLS:${test_name}>
                $<TARGET_FILE_DIR:${test_name}>
            COMMAND_EXPAND_LISTS
            COMMENT "[ACVISION] Copying OpenCV DLLs for test: ${test_name}"
        )
    endif()

    gtest_discover_tests(${test_name})
endfunction()

add_acvision_test(test_piece_detector)
add_acvision_test(test_board_detector opencv_imgcodecs)
add_acvision_test(test_board_geometry opencv_imgcodecs)

foreach(board_test IN ITEMS test_board_detector test_board_geometry)
    target_compile_definitions(${board_test}
        PRIVATE
            TEST_IMAGES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/images"
    )
endforeach()

option(
    ACVISION_BUILD_HARDWARE_TESTS
    "Build tests that require a physical camera"
    OFF
)

if(ACVISION_BUILD_HARDWARE_TESTS)
    add_acvision_test(test_camera)
endif()
