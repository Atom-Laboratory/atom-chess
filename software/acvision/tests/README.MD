# Testes do módulo `acvision`

Esta pasta contém os testes automatizados e de integração do módulo de visão
computacional. A suíte padrão usa entradas determinísticas e não depende de
hardware.

## Suíte padrão

- `test_piece_detector.cpp`: valida a construção do `OccupancyGrid`.
- `test_board_detector.cpp`: valida a detecção com e sem um tabuleiro.
- `test_board_geometry.cpp`: valida os cantos detectados na imagem de referência.
- `images/`: imagens 2D versionadas usadas pelos testes de tabuleiro.

O CMake procura primeiro uma instalação existente do GoogleTest. Quando ela não
está disponível, a versão `v1.14.0` é obtida com `FetchContent`.

## Executar a partir da raiz do repositório

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Para configurar sem testes:

```sh
cmake -S . -B build -DBUILD_TESTING=OFF
```

O módulo também pode ser configurado isoladamente:

```sh
cmake -S software/acvision -B build/acvision
cmake --build build/acvision
ctest --test-dir build/acvision --output-on-failure
```

## Teste com câmera física

`test_camera.cpp` é um teste de integração e requer uma câmera disponível no
dispositivo `0`. Por isso, ele não faz parte da suíte padrão executada pelo CI.

Para habilitá-lo explicitamente:

```sh
cmake -S . -B build -DACVISION_BUILD_HARDWARE_TESTS=ON
cmake --build build
ctest --test-dir build --output-on-failure
```
