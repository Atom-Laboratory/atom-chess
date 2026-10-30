# Auditoria de acvision — 30/10/2026

Base: ros2_simulation/e6c9b1e mais ajustes locais de CMake anteriores à revisão.

| Área | Evidência e estado |
|---|---|
| Biblioteca e apps | Compilação C++17 com GCC 15.2/OpenCV 4.10 aprovada em WSL Ubuntu 26.04 |
| Testes sintéticos | 3 suítes CTest, 6 casos GTest: tabuleiro, ocupação/cor e FEN; todos aprovados |
| Captura física | Implementada, não aprovada sem câmera; teste de captura anterior falhou por dispositivo ausente |
| BoardDetector | Grade interna 7×7 e fallback por contornos; teste não valida precisão externa. Extrapolação usa meio passo; defeito pendente |
| PieceDetector | Heurística de bordas e brilho; não reconhece tipo de peça; precisão real não medida |
| FenGenerator | Ocupações viram P/p, turno e demais campos fixos; parcial, não núcleo de xadrez |
| Integração | Sem homografia completa até estado legal, Stockfish, planejador ou ROS |

Problemas adicionais por inspeção: captura de fonte URL usa `std::get<int>` ao
registrar falha, podendo lançar `bad_variant_access`; células minúsculas/canais
inesperados não têm contrato validado; demos escolhem câmera 1, testes câmera 0;
fallback quadrilateral não comprova ser um tabuleiro. Não corrigidos neste ciclo.

O CTest da raiz antes dos ajustes não descobria testes; agora os descobre.
Teste físico é opt-in, e fixtures geradas vão para o build. Não há medição de
cobertura ou validação Windows/MSVC nesta execução. `simulator` é imagem 2D,
não simulador robótico. Presets e documentação Windows anteriores não foram
considerados evidência de build funcionando.
