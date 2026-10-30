# V001 — Separar validação sintética de captura física

Data: 30/10/2026. Estado: aceito; registra ajuste local previamente implementado.

Contexto: raiz descobria zero testes, teste de tabuleiro não estava na lista e
captura dependia de câmera ausente. Fixtures podiam ser escritas no fonte.

Decisão: include(CTest) na raiz e standalone, respeitar BUILD_TESTING, habilitar
tabuleiro, tornar câmera opt-in por ACVISION_BUILD_HARDWARE_TESTS e gerar fixtures
no build. Preferir GTest instalado, mantendo fallback v1.14.0 já usado.

Consequência: teste sem câmera é reproduzível; passar essas suítes não certifica
captura, precisão de visão ou partida legal. Não mascarar erro de câmera como
aprovação. Validação: build e 3 suítes CTest aprovados em 30/10/2026.
