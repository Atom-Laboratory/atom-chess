# P003 — Integrar main preservando a simulação

Data: 2026-10-30. Estado: aceito. Complementa P001/P002.

## Contexto

Pedido explícito para integrar main e manter MuJoCo como simulador principal.
Antes: ros2_simulation 948f16a; origin/main f72c893. Fetch confirmou ambas as
referências. Única alteração local anterior: simulation/learning/ não versionado.

## Decisão

Merge normal de main, sem rebase/force push, registrado em 8fbc7aa, com dois pais.
Conflitos: CMake da raiz passa a incluir os quatro módulos da main; acvision usa
seu CMake atual (os antigos testes FEN foram migrados para acchess); README
combina navegação de simulação e descrição/licenças da main; Dockerfile movido
para simulation é preservado como legado, não adotado para executar MuJoCo.
URDF operacional permanece simulation/src/urdf e o pacote ROS simulation/src.
O atom_description aninhado e atom_control herdados não são o caminho validado.
Não foram removidos dados, histórico ou o experimento local de aprendizado.

Build da raiz trata acmotion como target CMake comum mesmo com ROS carregado.
A descoberta/exportação ament fica restrita ao build standalone: o export
anterior tentava instalar motion sem exportar acchess e impedia a configuração.
Empacotamento ROS standalone de motion continua pendente; não foi validado.

## Validação e consequências

Após merge: C++ headless 15 suites CTest; ROS 13 casos pytest em quatro suites
CTest; MuJoCo 13 casos anteriores, incluindo render: aprovados. Após ajuste
acmotion: C++ 15 suites aprovadas com setup ROS carregado, sem desativar ament
globalmente. Stockfish ausente: teste UCI não registrado. Firmware não compilado.
Não equivale a uma partida integrada ou controle do hardware.

Arquivos hardware que diferiam apenas em caixa foram rematerializados conforme
HEAD após o merge no Windows; nenhuma exclusão local preexistente foi descartada.
Whitespace e logs gerados herdados de main não foram reformados em massa.
Revisão funcional/documental subsequente: relatório de integração no módulo MuJoCo.
