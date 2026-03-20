cmake_minimum_required(VERSION 3.16)

project(acvision VERSION 1.0.0 LANGUAGES CXX)

# Standard C++ Configuration
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

# Output Directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Dependency: OpenCV
# Inject path for the local environment
set(OpenCV_DIR "D:/opencv/build/x64/vc16/lib")
find_package(OpenCV REQUIRED)

# ==========================================
# TARGET: acvision (Shared Library)
# ==========================================
add_library(acvision SHARED
    src/camera/camera.cpp
)

target_include_directories(acvision 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        ${OpenCV_INCLUDE_DIRS}
)
target_link_libraries(acvision
    PUBLIC 
        ${OpenCV_LIBS}
)

# ==========================================
# AUTOMATIC TARGET GENERATION (Apps Folder)
# ==========================================
file(GLOB APP_SOURCES "apps/*.cpp")

foreach(source_file ${APP_SOURCES})
    # Extrai o nome do arquivo sem a extensão (ex: capture_gui)
    get_filename_component(app_name ${source_file} NAME_WE)
    
    # Cria um executável para cada arquivo encontrado
    add_executable(${app_name} ${source_file})
    
    # Linka com a sua biblioteca e OpenCV
    target_link_libraries(${app_name} PRIVATE acvision)
    
    message(STATUS "[ACVISION] Added executable target: ${app_name}")
endforeach()

target_link_libraries(capture_gui
    PRIVATE 
        acvision
)

# Optional: Set capture_gui as the default startup project in VS Code
set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT capture_gui)