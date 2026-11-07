# Validação por incremento

## Controle convencional — 30/10/2026

Build colcon, Xacro e check_urdf aprovados. Quatro suítes CTest, contendo 13
casos pytest, aprovadas. colcon soma os wrappers e reporta 17 testes, sem erros,
falhas ou skips; não são 17 cenários independentes.

Comandos CLI também executados: publicação única da meta, leitura de JointState
e status, stop e reset (ambos success=True). Foi necessário explicitar o tipo
na chamada topic echo para evitar uma falha inicial de descoberta de tipo;
docs/control.md contém os comandos corrigidos. RViz inicializou OpenGL 4.5 no
launch de controle; isso não resolve a pendência de inspeção visual.

Controle testado em DDS real: recebimento da meta [0.3, 0.08, -0.4], posições
intermediárias/finais, mudança de translação e rotação TF, rejeição de comando
fora de limite sem alterar meta, parada durante movimento e reset para zero.
Núcleo: ordenação por nomes, limites/velocidade, não finitos, dt inválido,
duplicação, parada e reset. A primeira execução falhou em comparação array/lista
do teste; corrigida a asserção, suíte completa aprovada.

| Critério solicitado | Resultado |
|---|---|
| Carregar modelo | Verificado com Xacro/check_urdf e ROS |
| Iniciar ROS | Dois launches exercitados sem GUI |
| Visualizar montagem | Pendente de inspeção visual; ver limitação WSLg abaixo |
| Consultar estados | Verificado por subscription real |
| Comandos chegarem ao controlador | Verificado por status e resposta articular |
| Movimento e resultado | Verificado numericamente nos estados e TF; observação visual pendente |
| Reprodução | Build, testes e comandos em README e docs/control.md |

Não declarar simulação física completa: URDF sem inércias/colisões; CAD e TCP
não calibrados. Nenhum treinamento foi executado nesta revisão. Commits locais
agora autorizados pelo responsável; informações de Git abaixo são históricas.

## Primeiro incremento — registro histórico

Data: 27/10/2026. Branch: `ros2_simulation`, baseada em `e6c9b1e`.

## Executado e aprovado

- Descoberta de um pacote `atom_description` em `simulation/src`.
- Build/instalação com colcon, CMake e ament em área externa ao repositório.
- Expansão Xacro e `check_urdf`: árvore com raiz world, base_link,
  z_axis_link, arm1_link e arm2_link.
- Argumentos do launch resolvidos com `--show-args`.
- Duas suítes CTest aprovadas, contendo três casos pytest: árvore/recursos,
  instalação de configuração RViz e execução ROS sem janelas.
- Na execução sem janelas: estados de todas as juntas móveis; TF dinâmico e
  estático para todos os filhos; nomes pai/filho corretos; quaternions
  normalizados; uma única fonte de joint_states; encerramento dos processos.
- RViz e Joint State Publisher GUI iniciados no WSLg. Logs confirmam leitura
  da descrição pelos sliders e inicialização do renderizador OpenGL 4.5.

Ambiente: Ubuntu 26.04 WSL2, ROS 2 Lyrical, GCC 15.2, Python 3.14.
Build e testes foram repetidos em área persistente após observar que o diretório
temporário da primeira execução não permaneceu disponível entre sessões WSL.

## Problemas encontrados e tratados

- Teste com contexto ROS isolado exigiu executor explícito no mesmo contexto;
  corrigido antes do resultado final aprovado.
- Qt selecionado automaticamente não criou a janela de renderização GLX
  (`Invalid parentWindowHandle`). A execução com `QT_QPA_PLATFORM=xcb`
  inicializou o renderizador. O comando consta no README e não altera
  configurações globais do sistema.

## Limites da validação

A ferramenta de captura de aplicativos não conseguiu capturar a janela WSLg:
`FrameArrived timed out` e, na tentativa de recuperação, `window capture timed out`.
Não foi concluída inspeção visual da montagem no viewport. Abertura de janela e
logs sem erro de renderização não substituem essa inspeção.

Nenhuma junta foi comparada ao F3D, nenhum limite foi calibrado e nenhuma FK/IK,
colisão, física, MoveIt ou comando de hardware foi validado neste incremento.
Os testes estruturais aprovam o carregamento do protótipo existente, não sua
fidelidade mecânica. O próximo incremento depende da extração da montagem F3D.

## Alterações

Somente `simulation` foi alterado. As geometrias e valores cinemáticos existentes
foram preservados; o Xacro recebeu apenas um comentário de proveniência/limitação.
O repositório mecânico foi mantido inalterado. Não houve troca de branch,
instalação de dependências, commit ou push.
