# Resultados preliminares de benchmark

Este diretório contém os resultados preliminares do benchmark do `BoardDetector`.

## Arquivos

- `benchmark_board_detector_result.txt`: saída principal do benchmark.
- `benchmark_board_detector_time_result.txt`: saída do benchmark com métricas de sistema via `/usr/bin/time -v`.

## Resumo

| Benchmark | Resolução | Latência média | FPS estimado | Memória máxima | Status |
|---|---:|---:|---:|---:|---|
| BoardDetector | 480x480 | ~20,67 ms | ~48,37 FPS | ~98,8 MB | OK |

## Observação

O teste `test_camera` não foi considerado como métrica principal porque depende de uma câmera física disponível em `/dev/video0`.

Nos testes realizados, o `BoardDetector` apresentou latência média entre aproximadamente 20,46 ms e 24,30 ms por frame, variando conforme a forma de execução e a sobrecarga da medição com `/usr/bin/time`.

O FPS estimado ficou entre aproximadamente 41 e 49 FPS. O pico de memória observado foi de 99.228 KB, aproximadamente 99,2 MB, com uso de CPU em torno de 264%.