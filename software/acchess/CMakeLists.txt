cmake_minimum_required(VERSION 3.23)

project(acchess 
    VERSION 1.0.0 
    DESCRIPTION "A Library for Chess"
    LANGUAGES CXX)

if(PROJECT_IS_TOP_LEVEL)
    include(CTest)
endif()

# ==========================================
# Configurações Globais
# ==========================================
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# ==========================================
# Chess Engine Dependencies (Stockfish)
# ==========================================
# Search for the Stockfish executable in the user's system
find_program(STOCKFISH_EXECUTABLE NAMES stockfish PATHS /usr/games /usr/bin)
if(NOT STOCKFISH_EXECUTABLE)
    message(WARNING "Stockfish executable not found! Make sure it is installed via apt.")
endif()

option(ACCHESS_BUILD_VIEWER "Build the SFML viewer and demo application" ON)

if(ACCHESS_BUILD_VIEWER)
    set(SFML_STATIC_LIBRARIES TRUE)
    include(FetchContent)

    FetchContent_Declare(
        SFML
        GIT_REPOSITORY https://github.com/SFML/SFML.git
        GIT_TAG        3.0.0
    )
    FetchContent_MakeAvailable(SFML)
endif()

# ==========================================
# TARGET: acchess (Core Library)
# ==========================================
add_library(acchess STATIC
    src/board/board.cpp
    src/board/move.cpp
    src/board/piece.cpp
    src/board/square.cpp
    src/utils/path.cpp
    src/engine/stockfish_uci.cpp
)

target_sources(acchess
    PUBLIC
        FILE_SET HEADERS
        BASE_DIRS include
        FILES 
            include/board/board.hpp
            include/board/move.hpp
            include/board/piece.hpp
            include/board/square.hpp
            include/utils/path.hpp
            include/engine/stockfish_uci.hpp
)

target_include_directories(acchess 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

if(ACCHESS_BUILD_VIEWER)
    target_sources(acchess
        PRIVATE
            src/viewer/renderer.cpp
        PUBLIC
            FILE_SET HEADERS
            BASE_DIRS include
            FILES include/viewer/renderer.hpp
    )
    target_link_libraries(acchess PUBLIC SFML::Graphics SFML::Window SFML::System)

    add_executable(chess.demo apps/chess.demo.cpp)
    target_link_libraries(chess.demo PRIVATE acchess)
    set_target_properties(chess.demo PROPERTIES FOLDER "Applications")

    add_custom_command(TARGET chess.demo POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
            ${CMAKE_CURRENT_SOURCE_DIR}/assets
            $<TARGET_FILE_DIR:chess.demo>/assets
    )
endif()

# ==========================================
# AUTOMATED TESTS
# ==========================================
if(BUILD_TESTING)
    include(FetchContent)

    # Prefer a system GoogleTest installation. Fetch the pinned fallback only
    # when the package is unavailable to keep local/offline builds predictable.
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

    # Chess-domain unit tests are deterministic and must not depend on an
    # external Stockfish binary. EXISTS keeps this branch compatible with
    # main while PR #85 introduces additional tests incrementally.
    set(ACCHESS_UNIT_TESTS
        test_board
        test_board_comparator
        test_fen_generator
        test_move_applier
    )

    foreach(test_name IN LISTS ACCHESS_UNIT_TESTS)
        set(test_src "${CMAKE_CURRENT_SOURCE_DIR}/tests/${test_name}.cpp")
        if(EXISTS "${test_src}")
            add_executable(${test_name} "${test_src}")
            target_link_libraries(${test_name} PRIVATE acchess GTest::gtest_main)
            add_test(NAME ${test_name} COMMAND ${test_name})
            set_target_properties(${test_name} PROPERTIES FOLDER "Tests")
        endif()
    endforeach()

    # Stockfish is an external integration dependency. Only the UCI integration
    # test is conditional on the executable being available.
    if(STOCKFISH_EXECUTABLE)
        add_executable(test_stockfish_uci tests/test_stockfish_uci.cpp)
        target_link_libraries(test_stockfish_uci PRIVATE acchess GTest::gtest_main)
        target_compile_definitions(test_stockfish_uci PRIVATE
            STOCKFISH_EXECUTABLE_PATH="${STOCKFISH_EXECUTABLE}"
        )
        add_test(NAME test_stockfish_uci COMMAND test_stockfish_uci)
        set_target_properties(test_stockfish_uci PROPERTIES FOLDER "Tests")
    else()
        message(STATUS "Stockfish not found: test_stockfish_uci will not be registered.")
    endif()
endif()
