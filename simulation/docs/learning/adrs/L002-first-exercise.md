# L002 — Começar RL pela inspeção convencional das juntas

Data: 30/10/2026. Estado: aceito.

Contexto: o backend MuJoCo está disponível, mas o responsável quer desenvolver
pessoalmente o aprendizado. Um comando de continuar não revoga esse escopo.

Decisão: oferecer um exemplo pequeno baseado apenas em reset/advance/observe,
comandos isolados por junta, registro de unidades e comparação após reset.
Documentar previsões e alterações que o responsável fará, sem definir reward,
episódio, observação final ou algoritmo de RL antecipadamente.

Consequência: demonstração de engenharia executável e revisável; avanço de
pesquisa depende das respostas do responsável. O JSON de referência é resultado
de controle convencional no perfil sintético e não um conjunto de treinamento.
