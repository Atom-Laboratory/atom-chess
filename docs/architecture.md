# Arquitetura real e fronteiras

## Em execução nesta branch

`CMakeLists.txt` compila `Software/acvision`: captura OpenCV → estimativa de
cantos; separadamente, células fornecidas pelo chamador → ocupação/cor → FEN
simplificada. As aplicações são demonstrações; não há pipeline completo de
reconstrução da partida. `simulation/src` é um único pacote ament_cmake,
`atom_description`: URDF → robot_state_publisher → TF → RViz, com estados
articulares fornecidos por um único publicador por execução. Em control_demo,
o servo convencional recebe metas nomeadas e publica estados; em view_robot,
os estados vêm dos sliders ou do publicador padrão. Os modos são exclusivos.

Não existe comunicação entre acvision e ROS nesta revisão. `Frame Capture.cpp`
é um experimento legado fora do CMake. `Hardware`/`hardware` contém referências
e CAD, não drivers executáveis. Há caminhos versionados que diferem apenas em
maiúsculas; Windows não os representa independentemente. Não normalizar esses
caminhos sem revisão em filesystem sensível a caixa.

O backend principal para experimentos de controle é agora `simulation/mujoco`:
converte o URDF em MJCF/manifest/STL, executa física experimental em passos
explícitos e oferece reset/advance/observe, visualização e logs. Não depende de
ROS ou do código anterior de RL. A ligação desse backend com o controle ROS é
futura; os dois modos não trocam estados automaticamente. Contatos e gravidade
estão desativados no perfil sintético atual, com massas/inércias declaradas.

## Arquitetura pretendida, ainda não integrada

Visão estima observações; núcleo de xadrez mantém estado legal e consulta
Stockfish; planejamento de tarefas decompõe o lance; planejamento de movimento
produz metas; controle executa comandos através de um backend de simulação ou,
futuramente, hardware. RL poderá substituir uma estratégia de controle de tarefa
definida, nunca a análise de xadrez nem os mecanismos de validação de comandos.

`main` local (`f72c893`) contém módulos adicionais em `software/`, incluindo
acchess. Isso não prova integração nesta branch. Uma reconciliação requer diff,
testes e decisão específica; não houve merge automático.

## Vocabulário

- URDF: árvore de links e juntas; não garante fidelidade física.
- TF: transformações entre referenciais; `arm2_link` não é um TCP calibrado.
- TCP: ponto de trabalho da ferramenta, ainda desconhecido.
- Controlador cinemático: atualiza posições segundo regras de software, sem dinâmica.
- Backend físico: integra forças, massas e contatos; ainda bloqueado.
- Observação de visão: estimativa, não estado legal confirmado de uma partida.
