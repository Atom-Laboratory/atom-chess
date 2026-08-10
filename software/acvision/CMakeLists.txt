# This File is The CMAKELISTS

cmake_minimum_required(VERSION 3.23)

project(acvision 
    VERSION 1.0.0 
    DESCRIPTION "A Library for Computer Vision applied to Chessboard Analysis"
    LANGUAGES CXX)

if(PROJECT_IS_TOP_LEVEL)
    include(CTest)
endif()

# ==========================================
# Configurações Globais (Modern C++)
# ==========================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(WIN32)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()
set(CMAKE_CXX_EXTENSIONS OFF) 

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# ==========================================
# Dependências
# ==========================================
find_package(OpenCV REQUIRED)

# ==========================================
# TARGET: acvision (Core Library)
# ==========================================
add_library(acvision SHARED
    src/camera/camera.cpp
    src/board_vision/board_vision.cpp
    src/piece_detector/piece_detector.cpp
    # src/fen_generator/fen_generator.cpp
    src/homography/homography.cpp
)

target_sources(acvision
    PUBLIC
        FILE_SET HEADERS
        BASE_DIRS include
        FILES 
            include/camera/camera.hpp
            include/board_vision/board_vision.hpp
            include/piece_detector/piece_detector.hpp
            # include/fen_generator/fen_generator.hpp
            include/homography/homography.hpp
            

)

target_include_directories(acvision 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(acvision
    PUBLIC 
        opencv_core
        opencv_imgproc
        opencv_highgui
        opencv_videoio
        opencv_calib3d
)

if(MSVC)
    target_compile_options(acvision PRIVATE /W4 /WX)
else()
    target_compile_options(acvision PRIVATE -Wall -Wextra -Wpedantic)
endif()

# ==========================================
# AUTOMATIC TARGET GENERATION (Apps Folder)
# ==========================================
set(APP_LIST
    # "capture_gui"
    "board_demo"
)

foreach(app ${APP_LIST})
    set(app_src "apps/${app}.cpp")
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${app_src})
        add_executable(${app} ${app_src})
        
        target_link_libraries(${app} PRIVATE acvision)
        set_target_properties(${app} PROPERTIES FOLDER "Applications")
        
        if(WIN32)
            add_custom_command(TARGET ${app} POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_if_different
                $<TARGET_RUNTIME_DLLS:${app}>
                $<TARGET_FILE_DIR:${app}>
                COMMAND_EXPAND_LISTS
                COMMENT "[ACVISION] Copying OpenCV runtime DLLs for ${app}..."
            )
        endif()
    endif()
endforeach()

# ==========================================
# AUTOMATIC TARGET GENERATION (Simulation Folder)
# ==========================================
set(SIM_LIST
    "simulator"
)

foreach(sim ${SIM_LIST})
    set(sim_src "simulation/${sim}.cpp")
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${sim_src})
        add_executable(${sim} ${sim_src})
        
        target_link_libraries(${sim} PRIVATE acvision)
        set_target_properties(${sim} PROPERTIES FOLDER "Applications")
        
        if(WIN32)
            add_custom_command(TARGET ${sim} POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_if_different
                $<TARGET_RUNTIME_DLLS:${sim}>
                $<TARGET_FILE_DIR:${sim}>
                COMMAND_EXPAND_LISTS
                COMMENT "[ACVISION] Copying OpenCV runtime DLLs for ${sim}..."
            )
        endif()
    endif()
endforeach()



# ==========================================
# AUTOMATED TESTS (tests Folder)
# ==========================================
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

    set(TEST_LIST
        test_piece_detector
        test_board_geometry
    )

    option(
        ACVISION_BUILD_HARDWARE_TESTS
        "Build tests that require a physical camera"
        OFF
    )

    if(ACVISION_BUILD_HARDWARE_TESTS)
        list(APPEND TEST_LIST test_camera)
    endif()

    foreach(test_name ${TEST_LIST})
        add_executable(${test_name} tests/${test_name}.cpp)
        target_link_libraries(${test_name} PRIVATE acvision GTest::gtest_main)
        add_test(NAME ${test_name} COMMAND ${test_name})
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
    endforeach()

    target_link_libraries(test_board_geometry PRIVATE opencv_imgcodecs)
    set_tests_properties(test_board_geometry PROPERTIES
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../.."
    )
endif()

# ==========================================
# Configuração de IDE
# ==========================================
set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT capture_gui)
