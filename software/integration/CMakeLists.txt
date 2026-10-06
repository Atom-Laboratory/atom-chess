add_library(acintegration
    src/observation_interpreter.cpp
)

target_include_directories(acintegration PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(acintegration PUBLIC
    acchess
    acvision
)

target_compile_features(acintegration PUBLIC cxx_std_20)

if(BUILD_TESTING)
    add_subdirectory(tests)
endif()