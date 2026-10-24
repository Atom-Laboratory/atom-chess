#!/bin/bash
# Script auxiliar para carregar o ambiente do atom-chess

if [ -f "install/setup.bash" ]; then
    source install/setup.bash
    echo "Ambiente local carregado com sucesso!"
else
    echo "Erro: install/setup.bash nao encontrado. Compile o projeto primeiro com colcon build."
fi
