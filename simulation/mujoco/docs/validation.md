# Validação MuJoCo — 30/10/2026

## Atualização de cena upright-chess-v2

12 testes aprovados, incluindo render e novo teste de montagem vertical, 64 casas,
tabuleiro estático durante movimento e garra rígida em relação a arm2_link.
FK comparada com equações independentes após transformação Rx(+90°) e offset
de altura. Demo executada pelo launcher atualizado, sem excesso de limites no
cenário de referência e com os mesmos erros articulares finais anteriores.
Render offscreen 800×600 inspecionado: coluna vertical, tabuleiro e três malhas
da garra visíveis. Não é inspeção contra o F3D oficial; anexação da garra provisória.
Contatos e abertura/fechamento da garra não foram implementados.

Registros abaixo descrevem a primeira versão do backend; quatro malhas e 11
testes eram os valores daquela versão. A cena atual contém sete malhas e 12 testes.

Base: ros2_simulation/a8e3093, sem alteração do URDF ou das malhas originais.
Ambiente: Windows, Python 3.12.14, MuJoCo 3.17.0, NumPy 2.5.4, pytest 9.2.0.
Dependências instaladas em venv isolado; lock inclui versões transitivas do
ambiente verificado. Não houve instalação de framework de treinamento.

Reprodução local final: ambiente padrão simulation/mujoco/.venv instalado pelo
lock, instalação editable aprovada, Start-MuJoCo.ps1 -Mode demo executado do
checkout. O script compilou runs/prototype-v1, executou o movimento e gravou JSON
com os mesmos resultados. Ambientes, bundles e resultados gerados estão ignorados
no Git; fontes, lock, testes, documentação e ADR estão versionados.

## Executado

- Compilação real do bundle MJCF e quatro malhas STL, três juntas e atuadores.
- 11 casos pytest aprovados, incluindo teste gráfico com ATOM_TEST_RENDER=1.
- FK: 30 configurações aleatórias comparadas com equações independentes do URDF;
  translação e orientação arm2_frame com tolerância de 1e-12.
- Conversão de RPY não nulo comparada com Rz·Ry·Rx independente.
- Controle convencional: 4 s simulados, 200 intervalos de 20 ms, meta
  [0.3, 0.08, -0.4]. Erros finais da demonstração aproximadamente
  [1.33e-15 rad, 3.33e-16 m, 1.39e-15 rad]; limite de teste <0,001 por eixo.
  Nenhum excesso de limite nesse cenário. Não se trata de precisão física medida.
- Forças e velocidades não nulas durante o movimento: o teste usa mj_step,
  não apenas teletransporte de qpos para a meta.
- Reset por semente e sequência de estados repetíveis na mesma instalação;
  observações independentes; NaN/infinito, dimensão e limites inválidos rejeitados
  antes de avançar o relógio ou alterar a meta.
- Metas no limite mantêm estados finitos; excesso final fica abaixo de 0,005
  por eixo no cenário testado. Restrições suaves exigem monitorar excesso.
- Bundle movido para outro diretório funciona; alteração do XML falha no hash;
  build sobre diretório já existente é rejeitado.
- Render offscreen real, 800×600: malhas azuis visíveis. Teste compara render
  antes/depois de movimento e exige mudança em mais de 500 pixels a 320×240.

Problemas tratados antes da aprovação: nome world duplicava o corpo implícito
do MuJoCo (conversor passou a reutilizar worldbody); framebuffer padrão era
menor que a imagem (dimensões declaradas no MJCF). Nenhum foi omitido como se
a primeira tentativa tivesse passado.

## Limites

Exercício 1 executado posteriormente no mesmo ambiente: três metas isoladas,
cada uma com 200 passos e repetição integral após reset. replay_max_error=0 nos
três cenários; erros articulares finais abaixo de 1,4e-15 nas unidades de cada
eixo. Deslocamentos/rotações registrados coincidem com o roteiro exercise-01.md.
Isso verifica o exemplo público de API sem acrescentar algoritmo de aprendizado.

Viewer nativo foi iniciado e anunciou os atalhos; a ferramenta de captura de
janelas retornou timeout. Não declarar interação manual dos atalhos aprovada
por essa ferramenta. A imagem offscreen foi inspecionada diretamente e o teste
de movimento gráfico passou. Comparação visual com CAD oficial segue pendente.

Não executados: treinamento, benchmark de throughput, ROS↔MuJoCo, colisões,
preensão, câmera simulada, hardware e comparação dinâmica com o braço real.
Contatos são None, pois estão desativados. Forças do modelo sintético não são
previsões confiáveis de torque real. Demos/testes não aprovam sim-to-real.
