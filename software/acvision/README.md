# acvision — visão C++/OpenCV

Biblioteca de captura, estimativa de cantos, classificação de ocupação/cor e
serialização FEN simplificada. [Auditoria e limitações](docs/audit.md).

| Componente | Entrada | Saída / limite |
|---|---|---|
| Camera | Índice de câmera ou URL | cv::Mat; conferir is_opened e retorno bool de capture_frame |
| BoardDetector | Imagem | optional de quatro cantos; não calcula estado de partida |
| PieceDetector | Matriz 8×8 de células BGR | EMPTY/WHITE/BLACK; não identifica tipo de peça |
| FenGenerator | Matriz 8×8 de CellState | P/p e campos fixos; não representa posição legal completa |

Não há transporte ROS, consulta UCI ou controle de motores nesta biblioteca.

## Build e testes

Fluxo verificado em Ubuntu 26.04/WSL, GCC 15.2 e OpenCV 4.10, com CMake e
GTest já instalados. Ajuste a raiz para seu checkout:

```bash
export ATOM_ROOT=/mnt/f/Users/EHD/Github/Atom/atom-chess
cmake -S "$ATOM_ROOT" -B "$HOME/atom-vision-build" -DBUILD_TESTING=ON
cmake --build "$HOME/atom-vision-build" --parallel 4
ctest --test-dir "$HOME/atom-vision-build" --output-on-failure
```

Executáveis ficam em bin: capture_gui e board_detection_demo requerem câmera
(índice 1 nos fontes atuais); simulator mostra células sintéticas em janela.
Essas aplicações foram compiladas, mas não tiveram validação visual nesta revisão.
O teste físico usa câmera 0 e é opt-in:

```bash
cmake -S "$ATOM_ROOT" -B "$HOME/atom-vision-camera-build" -DACVISION_BUILD_HARDWARE_TESTS=ON
cmake --build "$HOME/atom-vision-camera-build" --parallel 4
ctest --test-dir "$HOME/atom-vision-camera-build" -R test_camera --output-on-failure
```

Este último cenário exige hardware e não foi aprovado nesta máquina. Sem GTest
instalado, CMake usa FetchContent e precisa de rede. Não usar os presets legados
como fluxo validado: contêm sintaxe incompatível com JSON estrito.
Windows/MSVC não foi retestado; configurar OpenCV_DIR para o diretório que contém
OpenCVConfig.cmake e usar o toolchain correspondente à biblioteca instalada.

[ADR de testes](docs/adrs/V001-tests.md). Testes unitários sintéticos não medem
acurácia de visão em iluminação, oclusão ou perspectiva reais.