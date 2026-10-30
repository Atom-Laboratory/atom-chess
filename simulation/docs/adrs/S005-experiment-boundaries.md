# S005 — MuJoCo direto, parâmetros explícitos e episódios sem agente

Data: 2026-10-30. Estado: aceito. Complementa S003/S004 e L001.

## Contexto

O responsável quer desenvolver pessoalmente o aprendizado. Main está integrada,
mas seu contrato acmotion (J1/J2/J3/Z/garra) excede os três eixos do protótipo.
Não há TCP, inércias medidas, transmissão ou colisões do robô validadas.

## Decisão

MuJoCo + NumPy pela API Python permanecem a base local CPU. ROS não participa
de cada passo. Não adicionar Gazebo como segundo simulador principal nem instalar
frameworks de treinamento antecipadamente. Gazebo/ROS legados permanecem no Git.

build_bundle aceita JSON com overrides explícitos das massas/inércias sintéticas,
ganhos, damping/armature e temporização. Não habilita gravidade/contato via esse
atalho: primeiro devem existir geometrias de colisão e dinâmica revisadas.
Cada bundle novo contém configuração completa e hashes; não alterar bundles antigos.

Offset opcional experimental_tool em arm2_link permite estudar FK de um ponto
fora da origem da junta. Não há valor padrão inventado, nem calibração implícita.
frame_pose retorna posição em metros e matriz de rotação no mundo da cena.
Sem offset, tool_pose é None. O campo tcp_calibrated permanece false.

Episode exige Task fornecida pelo pesquisador e max_steps explícito. Task define
reset/metas, observação, conversão da ação e recompensa/término. A infraestrutura
cuida de seeds separados, avanço, truncamento e rejeição de ações inválidas.
Falha após avanço exige reset. Não existe recompensa padrão nem política.
Não é Gymnasium Env: faltam espaços escolhidos pelo responsável. Um adaptador
Gymnasium será pequeno após essa escolha, devendo passar pelo check_env oficial.

Registros locais JSON incluem commit, dirty/untracked, versões, manifest, tempo
de parede/simulado e resultados. Demos convencionais registram task/algorithm/seed
como null e reset determinístico; não simulam métricas de treinamento. Escrita
exclusiva evita sobrescrever resultados. Configuração de tarefa/algoritmo e
checkpoints serão acrescentados pelo pesquisador quando existirem.

## Alternativas e consequências

ROS em todo step acrescentaria integração sem resolver calibração; fica para
uma ponte opcional futura. Gymnasium agora imporia espaços/recompensa provisórios
ou uma dependência sem uso; adiado. PyTorch e SB3 são candidatos documentados,
não instalados. JSON basta para os pequenos exercícios, sem serviço pago.

Teste sintético esfera/plano valida contato do motor MuJoCo instalado e força
normal. Não valida colisões do braço: contacts continua None. Manipulação,
abertura da garra, J3 e transferência para hardware seguem bloqueadas por dados.

Validação: 23 casos pytest com render aprovados, incluindo offsets por composição
rígida, parâmetros inválidos, episódios/reset/replay, término/truncamento, erro de
recompensa e registros sem sobrescrita. Nenhum agente ou treinamento executado.
