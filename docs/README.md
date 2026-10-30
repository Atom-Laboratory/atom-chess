# Documentação por módulo

Cada módulo mantém seu guia, relatório de auditoria, testes e decisões. A raiz
documenta somente as relações entre módulos. Referência desta revisão:
30/10/2026, branch `ros2_simulation`, base `e6c9b1e` com alterações locais herdadas.

## Guias para começar

Diagnóstico geral atual: [auditoria de engenharia A–G, BOM e lacunas](audit/2026-10-30/README.md).

- [Usar o Gazebo no Windows/WSL](../simulation/docs/user-guide-gazebo.md).
- [Começar RL com o MuJoCo do ATOM](../simulation/docs/learning/user-guide-rl.md).

## Documentação técnica por módulo

- **Visão:** [guia e contratos](../Software/acvision/README.md),
  [auditoria](../Software/acvision/docs/audit.md),
  [ADR V001 — testes independentes de câmera](../Software/acvision/docs/adrs/V001-tests.md).
- **Simulação:** [execução](../simulation/README.md),
  [auditoria](../simulation/docs/audit.md), [validação](../simulation/docs/validation.md),
  [contratos de controle](../simulation/docs/control.md),
  [ADR S001 — backend](../simulation/docs/adrs/S001-backend.md),
  [ADR S002 — controle](../simulation/docs/adrs/S002-control.md).
- **MuJoCo:** [guia](../simulation/mujoco/README.md),
  [contratos](../simulation/mujoco/docs/interfaces.md),
  [validação](../simulation/mujoco/docs/validation.md),
  [ADR S003 — escolha e hipóteses](../simulation/docs/adrs/S003-mujoco.md).
  [ADR S004 — cena vertical e garra visual](../simulation/docs/adrs/S004-upright-chess-scene.md).
- **Mecânica:** [registro de fontes](mechanics/README.md),
  [ADR M001 — referência CAD](mechanics/adrs/M001-cad.md).
- **RL futuro:** [trilha](../simulation/docs/learning/README.md),
  [da política ao acmotion](../simulation/docs/learning/deployment-acmotion.md),
  [Gazebo completo: requisitos e lacunas](../simulation/docs/gazebo-readiness.md),
  [ADR L003 — política e integração](../simulation/docs/learning/adrs/L003-policy-motion-and-full-simulation.md),
  [exercício 1](../simulation/mujoco/docs/exercise-01.md),
  [ADR L002 — estudo inicial](../simulation/docs/learning/adrs/L002-first-exercise.md),
  [ADR L001 — participação do responsável](../simulation/docs/learning/adrs/L001-scope.md).
- **Integração:** [arquitetura](architecture.md), [roadmap](roadmap.md),
  [ADR P001 — escopo de branch](adrs/P001-branch.md).

Ao contribuir: leia a auditoria do módulo, altere uma responsabilidade por vez,
execute seus testes, atualize o relatório e registre decisões no ADR correspondente.
Use `docs:`, `test:`, `fix:`, `build:` ou `feat:`. Não versionar builds, logs,
credenciais, ambientes Python ou resultados volumosos. Não usar `git add .` neste
checkout: ele já contém trabalho anterior que deve ser preservado.
