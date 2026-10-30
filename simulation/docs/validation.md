# Validação do primeiro incremento

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
