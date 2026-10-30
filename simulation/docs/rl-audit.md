# Auditoria para aprendizado de movimento — 27/10/2026

> Registro histórico do escopo anterior. As prioridades de implementar/treinar
> RL abaixo foram substituídas em 30/10/2026 pelo [ADR L001](learning/adrs/L001-scope.md).
> Auditoria atual: [ROS](audit.md), [visão](../../Software/acvision/docs/audit.md).

Base efetiva: ros2_simulation, e6c9b1e; preservadas alterações locais do primeiro
incremento. O diretório versionado do software é `Software` (S maiúsculo).

## Linha de base executada antes das alterações deste ciclo

- CMake raiz configurou e compilou a biblioteca acvision, duas aplicações,
  simulador de imagens e testes no Ubuntu 26.04/OpenCV 4.10/GCC 15.2.
- CTest raiz: zero testes descobertos. CTest no subdiretório: peças e FEN
  passaram; captura de câmera falhou por ausência de /dev/video0.
- Descrição ROS: build, check_urdf e três casos pytest aprovados.
- Os CAD não foram modificados. F3D continua sendo a fonte oficial confirmada.
  O diretório mecânico fornecido novamente contém o STEP original de 2021;
  sua equivalência ao F3D não foi estabelecida.

## Implementação real e lacunas

| Componente | Estado observado |
|---|---|
| Câmera | Captura OpenCV; dependente de dispositivo; teste físico sem câmera falha |
| Tabuleiro | Detecção de grade 7×7 e fallback quadrilateral; extrapolação usa meio passo em vez de um passo até a borda externa |
| Peças | Heurística de bordas/brilho; produz EMPTY/WHITE/BLACK, não tipos de peça |
| FEN | Serializa todas as ocupações como peões e campos fixos; não é estado oficial completo de xadrez |
| Núcleo de xadrez/UCI | Ausente nesta branch; não existe Stockfish integrado para preservar aqui |
| Planejador/controle | Ausentes nesta branch; não importar outra branch sem decisão explícita |
| URDF | Protótipo de 3 juntas; parâmetros sem calibração; J3/TCP/garra ausentes |
| Entradas | capture_gui, board_detection_demo, simulator (imagem 2D); launch ROS separado |
| RL | Ausente antes deste incremento |

## Prioridades e decisões

1. Corrigir descoberta de CTest, tornar câmera opt-in e habilitar teste de
   tabuleiro já existente. Preferir GTest instalado. Preservar algoritmo de visão
   funcional, corrigindo defeitos geométricos somente com teste específico.
2. Criar pacote Python de aprendizado independente do ROS/C++ e hardware.
3. Consumir transformações/limites diretamente do URDF; rejeitar descrição
   inválida. A cinemática será validada contra equações independentes e TF ROS.
4. Treinar um servo articular condicionado à meta fornecida pelo planejador,
   medindo a pose de arm2_link (não chamar esse frame de TCP).
5. Registrar checkpoints, configuração, hash do modelo, sementes, episódios e
   avaliações pareadas em alvos separados. Comparar SAC com controle convencional.
6. Integração ROS por reprodução validada de trajetórias em joint_states, sem
   manter treinamento no loop de visão nem fornecer transporte ao hardware.

Não há parâmetros suficientes para dinâmica fiel, preensão, colisões de corpos
ou sim-to-real. Esses campos serão marcados como não modelados, nunca como zero
colisões comprovadas. Sem confirmação da geometria, resultados são sobre o
protótipo URDF e não sobre o braço físico.
