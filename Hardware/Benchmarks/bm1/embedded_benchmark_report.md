# Estudo e Preparação de Benchmarks para Hardware Embarcado

## 1. Objetivo

O objetivo deste documento é analisar benchmarks e metodologias de avaliação para hardware embarcado, com foco em aplicações de visão computacional e inferência local aplicadas ao projeto **ATOM Chess**.

A task teve como base os seguintes artigos:

1. [Benchmarking vision kernels and neural network inference accelerators on embedded platforms](https://www.sciencedirect.com/science/article/abs/pii/S1383762120301697)
2. [YOLOBench: Benchmarking Efficient Object Detectors on Embedded Systems](https://arxiv.org/pdf/2307.13901)

Além da leitura dos artigos, também foi feita uma análise prática do módulo `acvision`, que é o módulo de visão computacional do projeto ATOM Chess. Como etapa inicial de validação, foi criado e executado um benchmark preliminar para o `BoardDetector`, usando uma imagem 2D reproduzível.

---

## 2. Contexto do ATOM Chess

O **ATOM Chess** é um projeto de xadrez robótico que combina visão computacional, lógica de jogo e controle robótico. Dentro desse sistema, o módulo `acvision` tem a responsabilidade de interpretar visualmente o tabuleiro e transformar a imagem capturada em uma representação lógica do jogo.

De forma simplificada, o fluxo esperado da visão computacional no projeto pode ser entendido como:

```text
Câmera
  ↓
Captura do frame
  ↓
BoardDetector
  ↓
PieceDetector
  ↓
FenGenerator
  ↓
Estado lógico do tabuleiro
  ↓
Motor de xadrez / controle robótico
```

O módulo `acvision` já possui uma estrutura interessante para um projeto de Iniciação Científica, pois utiliza:

- C++;
- CMake;
- OpenCV;
- GoogleTest;
- testes automatizados;
- imagens 2D reproduzíveis para validação;
- separação entre câmera, detecção de tabuleiro, detecção de peças e geração de FEN.

Essa estrutura é importante porque permite avaliar partes do sistema separadamente, sem depender sempre de uma câmera conectada ou de condições físicas específicas, como iluminação, foco e posição do tabuleiro.

---

## 3. Estudo dos Artigos

---

## 3.1 Artigo 1 — Benchmarking vision kernels and neural network inference accelerators on embedded platforms

O primeiro artigo analisa o desempenho de operações clássicas de visão computacional e de inferência de redes neurais em plataformas embarcadas. O foco principal está em comparar diferentes tipos de hardware, como CPU, GPU e FPGA, observando desempenho e eficiência energética.

### 3.1.1 Benchmarks identificados

O artigo trabalha principalmente com três grupos de benchmarks:

### a) Vision Kernels

São operações básicas ou intermediárias de visão computacional, normalmente utilizadas em pipelines maiores.

Exemplos de operações desse tipo:

- conversão de cor;
- filtros;
- threshold;
- operações morfológicas;
- transformações geométricas;
- detecção de cantos;
- redimensionamento;
- processamento de imagem em geral.

Esse tipo de benchmark é muito relevante para o ATOM Chess, porque o projeto já utiliza OpenCV e possui etapas como detecção de tabuleiro e análise de imagem.

### b) Vision Pipelines

São fluxos mais completos, formados por várias operações de visão computacional encadeadas.

Exemplo genérico:

```text
Imagem de entrada
  ↓
Pré-processamento
  ↓
Segmentação
  ↓
Detecção
  ↓
Análise da imagem
```

Esse tipo de benchmark é ainda mais próximo da realidade do ATOM Chess, porque o projeto não executa apenas uma operação isolada. Ele precisa processar uma imagem, encontrar o tabuleiro, identificar peças e gerar um estado lógico.

### c) Neural Network Inference

O artigo também avalia modelos de redes neurais convolucionais, como:

- MobileNet;
- SqueezeNet;
- ResNet;
- Inception.

Esse tipo de benchmark é importante para uma possível etapa futura do ATOM Chess, caso o projeto passe a usar modelos de deep learning para classificar peças ou reconhecer o estado das casas do tabuleiro.

---

### 3.1.2 Metodologia de avaliação

O artigo compara a execução das operações em diferentes arquiteturas de hardware, como:

- CPU ARM;
- GPU NVIDIA;
- FPGA Xilinx.

As bibliotecas e frameworks analisados incluem:

- OpenCV;
- NVIDIA VisionWorks;
- Xilinx xfOpenCV;
- OpenCV DNN;
- TensorRT;
- Xilinx DPU/DNNDK.

A metodologia do artigo é interessante porque não analisa apenas FPS. Ela também observa o custo energético e o impacto do tipo de hardware no desempenho.

---

### 3.1.3 Métricas analisadas

As principais métricas usadas no artigo são:

- latência;
- FPS;
- throughput;
- energia por frame;
- eficiência energética;
- accuracy para redes neurais;
- Energy-Delay Product, quando aplicável.

No contexto do ATOM Chess, essas métricas ajudam a responder perguntas como:

- O processamento roda rápido o suficiente?
- O hardware consegue executar o pipeline em tempo aceitável?
- O consumo de energia é viável para um sistema embarcado?
- O sistema pode sofrer gargalo térmico?
- O uso de memória cabe no hardware alvo?

---

### 3.1.4 Relevância para o ATOM Chess

Este artigo é bastante relevante para o projeto, principalmente porque o `acvision` atualmente está mais próximo de uma abordagem de visão clássica com OpenCV do que de uma abordagem baseada inteiramente em redes neurais.

A principal conclusão para o ATOM Chess é que, no curto prazo, faz sentido priorizar benchmarks de:

- operações OpenCV;
- detecção de tabuleiro;
- pipeline de visão completa;
- uso de CPU, RAM, FPS e latência.

A inferência neural pode entrar em uma etapa posterior, principalmente para classificação de peças ou casas do tabuleiro.

---

## 3.2 Artigo 2 — YOLOBench: Benchmarking Efficient Object Detectors on Embedded Systems

O segundo artigo apresenta o **YOLOBench**, um benchmark voltado para avaliar modelos YOLO em dispositivos embarcados. O foco principal é analisar o equilíbrio entre precisão e latência em diferentes hardwares.

---

### 3.2.1 Benchmarks identificados

O YOLOBench avalia centenas de variações de modelos da família YOLO, variando fatores como:

- arquitetura do modelo;
- largura;
- profundidade;
- resolução de entrada;
- dataset utilizado;
- hardware de execução.

O benchmark é voltado para detecção de objetos, ou seja, o modelo recebe uma imagem e tenta localizar objetos usando caixas delimitadoras.

---

### 3.2.2 Metodologia de avaliação

O artigo mede principalmente:

- precisão, usando mAP;
- latência de inferência;
- relação entre precisão e desempenho;
- análise de Pareto para encontrar modelos mais eficientes.

A análise de Pareto é importante porque nem sempre o modelo mais preciso é o melhor para hardware embarcado. Em muitos casos, um modelo um pouco menos preciso, mas muito mais rápido, pode ser a melhor escolha.

---

### 3.2.3 Hardwares utilizados

O artigo considera plataformas como:

- NVIDIA Jetson;
- Raspberry Pi;
- CPU Intel;
- placas com NPU.

Esses hardwares estão mais próximos de SBCs, como Raspberry Pi, Banana Pi e Orange Pi, do que de microcontroladores como ESP32-S3 e ESP32-CAM.

---

### 3.2.4 Métricas analisadas

As principais métricas são:

- mAP;
- latência;
- comparação entre modelos;
- eficiência do modelo por hardware.

Diferente do primeiro artigo, o YOLOBench não tem como foco principal consumo energético, temperatura ou uso de memória. Para o ATOM Chess, essas métricas precisariam ser adicionadas nos testes práticos do laboratório.

---

### 3.2.5 Relevância para o ATOM Chess

O YOLOBench é relevante caso o projeto decida usar detecção de objetos para identificar peças diretamente na imagem.

Por exemplo:

```text
Imagem do tabuleiro
  ↓
Modelo YOLO
  ↓
Detecção das peças
  ↓
Mapeamento das peças para casas
  ↓
Geração do estado do jogo
```

No entanto, essa abordagem pode ser pesada para alguns hardwares do projeto, principalmente ESP32-S3 e ESP32-CAM.

Para o curto prazo, a abordagem mais realista é continuar explorando visão clássica com OpenCV e, depois, avaliar modelos leves de inferência embarcada.

---

## 4. Comparação dos Benchmarks

| Benchmark | Objetivo | Tipo de carga | Métricas principais | Relevância para o ATOM Chess | Compatibilidade embarcada |
|---|---|---|---|---|---|
| Vision Kernels | Medir operações básicas de visão | OpenCV / processamento de imagem | FPS, latência, energia, throughput | Muito alta | Alta em SBCs, baixa em ESP32 |
| Vision Pipelines | Medir fluxos completos de visão | Pipeline de imagem | FPS, latência total, energia, EDP | Muito alta | Alta em SBCs, limitada em microcontroladores |
| CNN Inference | Medir inferência de redes neurais | Classificação de imagem | Latência, FPS, accuracy, energia | Média/alta | Boa em SBCs, limitada em ESP32 |
| YOLOBench | Avaliar detectores YOLO | Detecção de objetos | mAP, latência | Condicional | Boa em SBCs fortes, baixa em ESP32 |

---

## 5. Benchmarks mais adequados para o ATOM Chess

Com base nos artigos e na estrutura atual do projeto, os benchmarks mais adequados para o ATOM Chess são:

---

### 5.1 Benchmark do BoardDetector

### Objetivo

Avaliar o tempo necessário para detectar o tabuleiro em uma imagem.

### Tipo de carga

Visão computacional clássica com OpenCV.

### Métricas

- latência média;
- FPS estimado;
- latência mínima;
- latência máxima;
- uso de RAM;
- uso de CPU;
- temperatura, quando executado em hardware físico;
- energia, quando houver medidor externo.

### Vantagens

- Já existe no projeto;
- não depende de câmera;
- pode usar imagens 2D reproduzíveis;
- é diretamente ligado ao ATOM Chess;
- pode ser executado em diferentes hardwares.

### Limitações

- Ainda não mede o pipeline completo;
- pode ser sensível à resolução da imagem;
- não avalia reconhecimento de peças;
- não representa inferência neural.

### Relevância

Muito alta. Esse benchmark deve ser uma das primeiras bases de comparação do projeto.

---

### 5.2 Benchmark do PieceDetector

### Objetivo

Avaliar o desempenho da detecção de peças.

### Tipo de carga

Pode ser visão clássica ou, futuramente, inferência neural.

### Métricas

- latência;
- FPS;
- precisão da detecção;
- uso de CPU;
- uso de RAM;
- temperatura;
- energia.

### Vantagens

- Representa uma parte essencial do projeto;
- ajuda a medir a dificuldade real de identificar peças;
- pode ser evoluído para comparação entre OpenCV e deep learning.

### Limitações

- Depende da maturidade do módulo;
- pode exigir dataset real com peças;
- pode ser afetado por iluminação e ângulo.

### Relevância

Alta. É essencial para transformar a imagem do tabuleiro em estado lógico.

---

### 5.3 Benchmark do FenGenerator

### Objetivo

Avaliar o tempo de geração da notação FEN a partir do estado identificado do tabuleiro.

### Tipo de carga

Lógica computacional leve.

### Métricas

- tempo de execução;
- corretude da FEN;
- estabilidade;
- integração com etapas anteriores.

### Vantagens

- Baixo custo computacional;
- fácil de testar;
- importante para integração com motor de xadrez.

### Limitações

- Não costuma ser o gargalo principal;
- depende da qualidade das etapas anteriores.

### Relevância

Média/alta. É importante para o sistema, mas provavelmente não será o maior gargalo de desempenho.

---

### 5.4 Benchmark da pipeline completa

### Objetivo

Medir o desempenho do fluxo real de visão computacional do ATOM Chess.

### Pipeline sugerido

```text
Imagem
  ↓
BoardDetector
  ↓
PieceDetector
  ↓
FenGenerator
```

### Métricas

- latência total;
- FPS final;
- tempo por etapa;
- uso de RAM;
- uso de CPU;
- temperatura;
- consumo energético;
- taxa de erro.

### Vantagens

- Representa melhor o uso real do sistema;
- permite encontrar gargalos;
- ajuda a decidir qual hardware é mais adequado.

### Limitações

- Depende da maturidade dos módulos;
- exige dataset mais completo;
- pode ser mais difícil de reproduzir.

### Relevância

Muito alta. Esse deve ser o benchmark principal em uma próxima etapa.

---

## 6. Planejamento de execução nos hardwares

---

## 6.1 ESP32-S3

### Viabilidade

Baixa para OpenCV completo e YOLO. Média para TinyML ou pré-processamento simples.

### O que pode rodar

- captura simples;
- pré-processamento leve;
- modelos muito pequenos;
- inferência quantizada com ESP-DL ou TensorFlow Lite Micro.

### O que provavelmente não faz sentido

- OpenCV completo;
- YOLOBench;
- modelos grandes;
- pipeline completa do `acvision`.

### Dependências

- ESP-IDF;
- ESP-DL;
- TensorFlow Lite Micro, se necessário;
- toolchain da Espressif.

### Limitações

- pouca RAM;
- sem Linux;
- sem OpenCV completo;
- limitação térmica e energética;
- necessidade de modelos muito pequenos.

### Conclusão

O ESP32-S3 pode ser útil como dispositivo auxiliar de captura ou TinyML, mas não deve ser o hardware principal para o pipeline completo de visão.

---

## 6.2 ESP32-CAM

### Viabilidade

Baixa.

### O que pode rodar

- captura JPEG;
- streaming simples;
- envio da imagem para outro hardware processar;
- pré-processamento mínimo.

### O que provavelmente não faz sentido

- YOLO;
- OpenCV completo;
- pipeline completa do `acvision`;
- inferência neural pesada.

### Dependências

- ESP-IDF;
- driver de câmera;
- PSRAM habilitada;
- firmware específico.

### Limitações

- RAM muito limitada;
- processamento de imagem pesado é inviável;
- RGB/YUV pode consumir muitos recursos;
- baixa capacidade para deep learning.

### Conclusão

O ESP32-CAM é mais adequado como módulo de captura do que como unidade principal de processamento.

---

## 6.3 Raspberry Pi Zero 2 W

### Viabilidade

Média.

### O que pode rodar

- OpenCV leve;
- BoardDetector em resoluções reduzidas;
- pipeline parcial;
- modelos pequenos com TensorFlow Lite.

### Dependências

- Linux;
- CMake;
- OpenCV;
- compilador C++;
- TensorFlow Lite, se houver inferência neural.

### Limitações

- 512 MB de RAM;
- CPU limitada;
- pode sofrer throttling térmico;
- não possui NPU.

### Conclusão

É um bom alvo para validar uma versão mínima do pipeline, mas pode sofrer com modelos pesados ou resoluções altas.

---

## 6.4 Banana Pi M5

### Viabilidade

Alta para OpenCV e média para inferência leve.

### O que pode rodar

- BoardDetector;
- PieceDetector;
- pipeline completa em OpenCV;
- ONNX Runtime;
- TensorFlow Lite;
- modelos leves.

### Dependências

- Linux;
- OpenCV;
- CMake;
- compilador C++;
- bibliotecas de inferência, se necessário.

### Limitações

- pode depender de câmera USB;
- pode não ter NPU dedicada;
- ainda precisa de testes reais de temperatura e consumo.

### Conclusão

É um dos melhores candidatos para rodar o pipeline principal de visão computacional do ATOM Chess.

---

## 6.5 Orange Pi

### Viabilidade

Depende do modelo exato.

### O que pode rodar

- OpenCV;
- pipeline completa;
- TensorFlow Lite;
- ONNX Runtime;
- modelos com NPU, se disponível.

### Dependências

- Linux compatível;
- OpenCV;
- CMake;
- bibliotecas específicas da placa;
- SDK de NPU, caso o modelo tenha acelerador.

### Limitações

- a família Orange Pi possui muitos modelos diferentes;
- é necessário confirmar o modelo com o grupo de hardware;
- suporte de software pode variar bastante.

### Conclusão

Se for uma Orange Pi com NPU, pode ser um excelente alvo para inferência neural e modelos YOLO reduzidos. Caso contrário, deve ser tratada como uma SBC Linux comum.

---

## 7. Benchmark preliminar executado

Além da análise teórica, foi implementado e executado um benchmark preliminar para o `BoardDetector`.

---

### 7.1 Ambiente utilizado

- Sistema: Linux/WSL
- Compilador: GCC 13.3.0
- CMake: 3.28.3
- OpenCV: 4.6.0
- Diretório do módulo: `Software/acvision`

---

### 7.2 Comandos principais executados

```bash
cd ~/ATOM/atom-chess/Software/acvision
rm -rf build
mkdir build
cd build
cmake ..
make -j$(nproc)
```

Também foram executados:

```bash
ctest -R test_board_detector --output-on-failure
ctest --output-on-failure
./bin/benchmark_board_detector
/usr/bin/time -v ./bin/benchmark_board_detector
```

---

### 7.3 Resultado dos testes automatizados

| Teste | Resultado | Observação |
|---|---|---|
| `test_board_detector` | Passou | Teste reproduzível com imagem 2D |
| `test_piece_detector` | Passou | Módulo validado |
| `test_fen_generator` | Passou | Módulo validado |
| `benchmark_board_detector` | Passou | Benchmark executado com sucesso |
| `test_camera` | Falhou | Falha esperada por ausência de câmera em `/dev/video0` |

A falha do `test_camera` não invalida os resultados principais, pois esse teste depende de hardware físico. No ambiente atual, o OpenCV não conseguiu abrir a câmera em `/dev/video0`, então a captura de frame falhou. Para benchmarks reproduzíveis, foi priorizado o uso de imagens 2D.

---

### 7.4 Resultado do benchmark do BoardDetector

O benchmark foi executado com a imagem:

```text
tests/images/chessboard.png
```

### Configuração

| Item | Valor |
|---|---:|
| Resolução da imagem | 480x480 |
| Warmup | 10 execuções |
| Execuções medidas | 1000 |

### Resultados obtidos

| Métrica | Resultado |
|---|---:|
| Latência média | 20,67 ms |
| Latência mínima | 16,52 ms |
| Latência máxima | 60,55 ms |
| FPS estimado | 48,37 FPS |
| Memória máxima | 98.880 KB / aproximadamente 98,8 MB |
| CPU | 263% |
| Status | Sucesso |

---

### 7.5 Interpretação dos resultados

O `BoardDetector` conseguiu processar uma imagem 480x480 com latência média próxima de 20 ms, o que equivale a aproximadamente 48 FPS no ambiente testado.

Esse resultado é positivo para uma primeira validação, pois mostra que a abordagem atual com OpenCV é viável em um ambiente Linux de desenvolvimento e provavelmente pode ser testada em SBCs como Banana Pi, Orange Pi e Raspberry Pi.

Por outro lado, o uso de aproximadamente 98,8 MB de memória indica que essa abordagem não é adequada diretamente para microcontroladores como ESP32-S3 ou ESP32-CAM sem simplificações importantes.

Também é importante observar que o uso de CPU foi de 263%, indicando uso de múltiplas threads. Em hardwares menores, como Raspberry Pi Zero 2 W, o desempenho pode ser menor.

---

## 8. Checklist de preparação do ambiente

---

### 8.1 Ambiente Linux / SBC

- [ ] Instalar compilador C++;
- [ ] instalar CMake;
- [ ] instalar OpenCV;
- [ ] instalar Ninja ou Make;
- [ ] clonar o repositório;
- [ ] compilar o módulo `Software/acvision`;
- [ ] rodar os testes unitários;
- [ ] rodar o benchmark do `BoardDetector`;
- [ ] medir FPS;
- [ ] medir latência;
- [ ] medir uso de RAM;
- [ ] medir uso de CPU;
- [ ] medir temperatura;
- [ ] medir consumo energético, se houver equipamento disponível.

---

### 8.2 Ambiente ESP32

- [ ] Instalar ESP-IDF;
- [ ] avaliar ESP-DL;
- [ ] avaliar TensorFlow Lite Micro;
- [ ] definir modelo tiny ou pipeline simplificado;
- [ ] verificar uso de PSRAM;
- [ ] medir heap disponível;
- [ ] medir tempo de execução;
- [ ] avaliar viabilidade de captura e envio de imagem.

---

### 8.3 Dataset

- [ ] Manter imagens sintéticas para testes unitários;
- [ ] criar dataset real com tabuleiro físico;
- [ ] coletar imagens com diferentes iluminações;
- [ ] coletar imagens com diferentes ângulos;
- [ ] coletar imagens com peças brancas e pretas;
- [ ] criar ground truth do estado do tabuleiro;
- [ ] separar imagens para teste, validação e benchmark.

---

## 9. Recomendações de arquitetura para próximas etapas

Com base na análise dos artigos, na estrutura atual do ATOM Chess e no benchmark preliminar executado, a recomendação é seguir uma arquitetura em camadas.

---

### 9.1 Curto prazo

Manter o foco em visão clássica com OpenCV.

Prioridades:

- melhorar o `BoardDetector`;
- criar benchmark do `PieceDetector`;
- criar benchmark da pipeline completa;
- testar resoluções diferentes;
- medir desempenho em SBCs reais.

Essa abordagem é a mais coerente com o estado atual do projeto.

---

### 9.2 Médio prazo

Adicionar inferência neural leve.

Possibilidades:

- classificador de casas;
- classificador de peças;
- MobileNetV2;
- MobileNetV3;
- SqueezeNet;
- EfficientNet Lite;
- TensorFlow Lite;
- ONNX Runtime.

O foco deve ser em modelos pequenos e quantizados.

---

### 9.3 Longo prazo

Avaliar detecção baseada em YOLO ou modelos similares.

Essa abordagem só deve ser priorizada se a visão clássica não for suficiente ou se o projeto precisar lidar com cenários mais variados, como:

- câmera muito inclinada;
- iluminação ruim;
- peças com formatos muito diferentes;
- tabuleiro pouco controlado;
- oclusões.

Nesse caso, recomenda-se testar:

- YOLO reduzido;
- YOLOv8n;
- modelos quantizados;
- inferência com NPU, caso a Orange Pi disponível tenha suporte.

---

## 10. Recomendações por hardware

| Hardware | Recomendação |
|---|---|
| ESP32-S3 | Usar apenas para captura, pré-processamento simples ou TinyML |
| ESP32-CAM | Usar principalmente como câmera ou módulo de captura |
| Raspberry Pi Zero 2 W | Testar pipeline OpenCV reduzida |
| Banana Pi M5 | Candidato forte para pipeline principal em OpenCV |
| Orange Pi | Confirmar modelo; se tiver NPU, usar para inferência neural |
| Outros dispositivos | Classificar como MCU, SBC CPU-only ou SBC com GPU/NPU |

---

## 11. Próximos benchmarks sugeridos

Para continuar a evolução do trabalho, os próximos benchmarks recomendados são:

1. **Benchmark por resolução**
   - 320x320;
   - 480x480;
   - 640x480;
   - 1280x720.

2. **Benchmark do PieceDetector**
   - medir latência;
   - medir precisão;
   - medir uso de memória.

3. **Benchmark da pipeline completa**
   - imagem;
   - BoardDetector;
   - PieceDetector;
   - FenGenerator.

4. **Benchmark em hardware real**
   - Raspberry Pi Zero 2 W;
   - Banana Pi M5;
   - Orange Pi.

5. **Benchmark com modelo neural leve**
   - TensorFlow Lite;
   - ONNX Runtime;
   - modelo quantizado.

---

## 12. Conclusão

A análise dos artigos mostrou que benchmarks para hardware embarcado devem considerar não apenas FPS, mas também latência, uso de memória, temperatura, consumo energético e throughput.

No contexto do ATOM Chess, a abordagem mais adequada no curto prazo é priorizar benchmarks de visão clássica com OpenCV, pois o projeto já possui uma estrutura modular em C++ com `BoardDetector`, `PieceDetector` e `FenGenerator`.

O benchmark preliminar executado no `BoardDetector` mostrou um resultado inicial positivo: aproximadamente 20,67 ms de latência média por frame e 48,37 FPS estimados em uma imagem 480x480. Isso indica que a abordagem é promissora para SBCs Linux, como Banana Pi, Orange Pi e possivelmente Raspberry Pi.

Por outro lado, os resultados também mostram que microcontroladores como ESP32-S3 e ESP32-CAM não devem ser tratados como alvo principal para o pipeline completo de visão, mas sim como possíveis módulos auxiliares de captura ou TinyML.

Assim, a recomendação final é seguir uma estratégia em camadas:

1. consolidar benchmarks OpenCV;
2. testar em SBCs reais;
3. criar dataset próprio do ATOM Chess;
4. avaliar inferência neural leve;
5. considerar YOLO reduzido apenas em hardwares mais capazes.

---

## 13. Critérios de conclusão

| Critério | Status |
|---|---|
| Artigos analisados | Concluído |
| Benchmarks identificados e documentados | Concluído |
| Relatório comparativo concluído | Concluído |
| Requisitos de execução levantados | Concluído |
| Compatibilidade com hardwares avaliada | Concluído |
| Benchmark preliminar executado | Concluído |
| Recomendações finais documentadas | Concluído |

---

## 14. Observação final

Este estudo não encerra a avaliação prática dos hardwares, mas prepara o caminho para ela. A partir daqui, o projeto já possui uma base inicial para comparar desempenho entre diferentes dispositivos e decidir qual arquitetura embarcada faz mais sentido para o ATOM Chess.