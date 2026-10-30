# S003 — MuJoCo como backend principal para estudar controle e preparar RL

Data: 30/10/2026. Estado: aceito, autorizado pelo responsável nesta conversa.
Substitui a preferência futura por Gazebo em S001; preserva diagnóstico ROS.

Contexto: ROS/RViz não fornecem sozinhos o ambiente físico de treinamento.
O responsável quer aprender a construir RL e autorizou preparar MuJoCo, sem
transferir o desenvolvimento do agente para a automação. URDF não calibrado
continua sem massas/inércias, TCP e geometrias de colisão verificadas.

Decisão: pacote Python independente em simulation/mujoco, MuJoCo 3.17.0 fixado,
sem ROS no laço de física, sem frameworks de treinamento. Conversão do URDF
atual para bundle MJCF portátil, backend reset/advance/observe, viewer, demo
convencional e testes. ROS permanece como infraestrutura de integração futura.
Não adicionar Gazebo/PyBullet/Isaac como backends concorrentes nesta etapa.

Perfil explicitamente experimental, uncalibrated-zero-gravity-v1: massas e
inércias sintéticas declaradas, gravidade zero, contatos desativados, ganhos de
posição de software. Contrato lista todos os valores e unidades; manifest guarda
hash URDF, XML, STL, versão e perfil. Não tentar importar inércias inexistentes
nem transformar hipóteses em especificação do braço. O modelo compila e integra
dinâmica experimental; não é digital twin validado.

Alternativas: Gazebo favorece teste do sistema ROS, mas não é necessário para o
laço inicial de estudo. Isaac Lab adicionaria requisitos/complexidade sem modelo
físico calibrado. Nenhuma comparação quantitativa de desempenho foi realizada.
Escolha baseada na API direta, controle de passos e objetivo pedagógico.

Consequências: usuário pode começar os exercícios de ambiente sem depender de
TF/RViz. RL, reward, episódios e algoritmo permanecem decisões e implementação
do responsável (L001). Até calibração, resultados valem para o perfil sintético.
Parâmetros reais, importação de inércias e colisões exigem novo incremento e
validação; não basta ativar gravity/contact neste bundle.

Referências consultadas: [Python](https://mujoco.readthedocs.io/en/stable/python.html),
[modelagem](https://mujoco.readthedocs.io/en/stable/modeling.html).
