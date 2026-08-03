cmake_minimum_required(VERSION 3.23)

project(acchess 
    VERSION 1.0.0 
    DESCRIPTION "A Library for Chess"
    LANGUAGES CXX)

# ==========================================
# Configurações Globais
# ==========================================
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

set(SFML_STATIC_LIBRARIES TRUE)
include(FetchContent)

FetchContent_Declare(
    SFML
    GIT_REPOSITORY https://github.com/SFML/SFML.git
    GIT_TAG        3.0.0
)
FetchContent_MakeAvailable(SFML)

add_library(acchess STATIC
    src/board/board.cpp
    src/board/move.cpp
    src/board/move_applier.cpp
    src/board/piece.cpp
    src/board/square.cpp
    src/viewer/renderer.cpp
    src/utils/path.cpp
    src/fen_generator/fen_generator.cpp
)

target_sources(acchess
    PUBLIC
        FILE_SET HEADERS
        BASE_DIRS include
        FILES 
            include/board/board.hpp
            include/board/move.hpp
            include/board/move_applier.hpp
            include/board/piece.hpp
            include/board/square.hpp
            include/viewer/renderer.hpp
            include/utils/path.hpp
)

target_include_directories(acchess 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(acchess PUBLIC SFML::Graphics SFML::Window SFML::System)

set(APP_LIST
    "chess.demo"
)

foreach(app ${APP_LIST})
    set(app_src "apps/${app}.cpp")
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${app_src})
        add_executable(${app} ${app_src})
        target_link_libraries(${app} PRIVATE acchess)
        set_target_properties(${app} PROPERTIES FOLDER "Applications")
    endif()
endforeach()

add_custom_command(TARGET chess.demo POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_CURRENT_SOURCE_DIR}/assets
        $<TARGET_FILE_DIR:chess.demo>/assets
)

add_executable(test_board tests/test_board.cpp)
add_executable(test_move_applier tests/test_move_applier.cpp)

target_link_libraries(test_board PRIVATE acchess GTest::gtest_main)
target_link_libraries(test_move_applier PRIVATE acchess GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(test_board)
gtest_discover_tests(test_move_applier)
