# Gazebo — requisito de integração completa e lacunas reais

Atualização após capturas do responsável: limite CAD de uma junta da garra
confirmado visualmente em -45°..+10°, revoluta Z local. Rest está desabilitado.
Ver [evidências e identificação pendente](../../docs/mechanics/gripper-cad-evidence.md).
O nome/frame dessa junta e o vínculo dos dedos ainda não foram extraídos.

Orientação adicional do responsável: extrair os dados do próprio modelo CAD
disponível, sem depender de ele fornecer uma tabela pronta. Investigação iniciada:
Fusion360.exe localizado na instalação webdeploy e iniciado; chegou à janela
Home (Education License). Captura de janela retornou FrameArrived timed out e,
após recuperação, window capture timed out. Sem observação confiável da interface,
não houve abertura/inspeção validada do F3D nessa sessão. Inventário direto do
arquivo confirma container com streams binários/BREP, não tabela de juntas legível.
Nenhum eixo/limite de garra foi extraído ou afirmado como confirmado. Não modificar
o CAD original durante extração; próxima investigação deve usar cópia/importação
e exportar evidências da montagem via API ou inspeção visual confiável.

Data: 30/10/2026. Solicitado explicitamente pelo responsável após o protótipo
MuJoCo. MuJoCo continua ambiente de estudo/treinamento; Gazebo será a validação
da integração ROS com todas as articulações. Não é necessário para executar a
inferência no braço real. ROS/Gazebo nesta máquina usam Ubuntu no WSL; MuJoCo
e seus scripts atuais usam Windows nativo.

## Ambiente observado

WSL Ubuntu, ROS Lyrical. Executados gz sim --versions (10.4.0), ros2 pkg prefix
ros_gz_sim, gz_ros2_control e joint_trajectory_controller: pacotes presentes em
/opt/ros/lyrical. gripper_controllers não localizado. Houve aviso ao iniciar WSL
de falha da sessão systemd do usuário; os comandos de inventário executaram.
Não foi instalado pacote nem iniciado mundo físico nesta revisão.

## Bloqueio do modelo completo

URDF atual só tem 3 juntas móveis e visuais sem collision/inertial. J3 e abertura
da garra não existem no modelo, enquanto o contrato acmotion de main contém
J1/J2/J3/Z/gripper. Malhas dos dedos são corpos, não informam sozinhas os centros,
acoplamento e limites da transmissão. F3D é fonte oficial, mas as juntas não
foram extraídas de forma confiável. Os dados abaixo ainda precisam de fonte:

| Necessário | Evidência de conclusão |
|---|---|
| Cada junta e corpo pai/filho | Frame, eixo, zero, sinal e curso conferidos no CAD |
| Garra | Eixo do servo, acoplamento dos dedos, limites de abertura e contato |
| TCP e ferramenta | Transformação e configuração de preensão verificadas |
| Dinâmica | Massa, centro de massa, inércia, ganhos, atrito e limites identificados ou aproximações acordadas |
| Peças/tabuleiro físicos | Dimensões, massa e atrito rastreáveis, colisões e posições sem interpenetração |

Não gerar um modelo com todos os graus de liberdade apenas atribuindo juntas
arbitrárias às malhas. Isso poderia parecer completo enquanto ensinaria
movimentos incompatíveis com o mecanismo físico.

## Implementação após obter os dados

Um modelo mecânico compartilhado versionado fornecerá URDF para Gazebo/ROS e
MJCF para MuJoCo. Adicionar ros2_control/gz_ros2_control, controlador de trajetória
para J1/J2/J3/Z e controle da garra de acordo com o mecanismo identificado.
Usar interfaces ROS com tempo de simulação e reset determinístico; não reutilizar
diretamente o publicador cinemático como controlador físico.

Critérios: carregar todos os corpos; comandar cada eixo e garra separadamente;
observar estados/TF/TCP; limites e sinais corretos; pegar/levantar/transportar/
soltar peça com contato real, sem soldar/teletransportar peça como prova de
preensão; validar timeout/cancelamento e reset. Só então integrar adaptador de
acmotion. Não foi implementado um launch Gazebo nesta entrega por esse gate.

Referências: [ROS/Gazebo](https://gazebosim.org/docs/latest/ros2_integration/),
[JointTrajectoryController](https://control.ros.org/rolling/doc/ros2_controllers/joint_trajectory_controller/doc/userdoc.html).
A documentação rolling é referência de arquitetura, não teste do comportamento
da versão Lyrical instalada.
