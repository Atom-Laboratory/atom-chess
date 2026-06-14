cmake_minimum_required(VERSION 3.23)

project(AtomChessWorkspace
    VERSION 0.1
    DESCRIPTION "ATOM Lab - Atom Chess Project"
    LANGUAGES CXX 
)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Processa o módulo principal
add_subdirectory(Software/acvision)

# Processa os benchmarks de hardware
# O segundo parâmetro 'build/benchmarks' é obrigatório no CMake quando
# referenciamos um diretório fora da árvore padrão de fontes.
add_subdirectory(Hardware/Benchmarks hw_bm)