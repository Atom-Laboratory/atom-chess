# /Hardware/Benchmarks/CMakeLists.txt

set(BENCHMARK_NAME "benchmark_board_detector")
set(BENCHMARK_SRC "bm1/benchmark_board_detector.cpp")

if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${BENCHMARK_SRC})
    add_executable(${BENCHMARK_NAME} ${BENCHMARK_SRC})

    target_link_libraries(${BENCHMARK_NAME} PRIVATE acvision)
    
    set_target_properties(${BENCHMARK_NAME} PROPERTIES FOLDER "Benchmarks")

    if(WIN32)
        add_custom_command(TARGET ${BENCHMARK_NAME} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_RUNTIME_DLLS:${BENCHMARK_NAME}>
            $<TARGET_FILE_DIR:${BENCHMARK_NAME}>
            COMMAND_EXPAND_LISTS
            COMMENT "[HARDWARE] Copying OpenCV DLLs for benchmark: ${BENCHMARK_NAME}"
        )
    endif()
endif()