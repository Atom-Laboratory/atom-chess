# Testes do modulo acvision

Esta pasta concentra os testes automatizados do modulo de visao computacional.
O objetivo principal e validar o comportamento do `BoardDetector` com imagens 2D
reprodutiveis, sem depender de uma webcam conectada ao ambiente de teste.

## Estrutura

- `test_camera.cpp`: teste de integracao simples para captura de camera. Depende de hardware.
- `test_board_detector.cpp`: testes unitarios/reprodutiveis para deteccao de tabuleiro.
- `images/`: assets 2D usados pelos testes do detector.

## Imagens esperadas

Os testes do `BoardDetector` usam os seguintes arquivos:

- `images/chessboard.png`: imagem com um tabuleiro de xadrez 8x8 visivel.
- `images/no_board.png`: imagem 2D sem tabuleiro.

Esta pasta ja inclui imagens sinteticas deterministicas geradas com OpenCV. Elas
sao pequenas, versionaveis e podem ser substituidas por capturas reais 2D no
futuro, desde que mantenham os mesmos nomes. Se os arquivos forem removidos, o
teste tenta recria-los antes de carrega-los com `cv::imread`.

## Como rodar

A partir de `Software/acvision`:

```sh
mkdir -p build
cd build
cmake ..
make -j$(nproc)
ctest --output-on-failure
```

Para rodar apenas o teste do detector:

```sh
ctest -R test_board_detector --output-on-failure
```

## Por que imagens 2D

Testes com imagens 2D sao reprodutiveis, rapidos e independentes de camera,
iluminacao, foco, permissao de dispositivo e disponibilidade de hardware. A camera
continua util para validacao manual e testes de integracao, mas nao deve ser a base
dos testes unitarios do detector.
