# Auditoria ROS e simulação — 30/10/2026

Pacote único atom_description em src, sem pacotes filhos. URDF: world, base_link,
z_axis_link, arm1_link e arm2_link; duas revolutas e uma prismática. Sete STL no
diretório, quatro usados no URDF; garra não montada. Sem collision, inertial,
transmission ou ros2_control. O valor effort do URDF não é torque validado.

Verificado novamente antes deste incremento: colcon build, expansão Xacro,
check_urdf e 3 casos pytest em 2 suítes CTest aprovados. Launch real publica
JointState completo e TF dinâmico/estático, com um único publicador de estados.

RViz iniciou OpenGL com QT_QPA_PLATFORM=xcb no incremento anterior, mas não houve
inspeção visual confiável da montagem. Isso continua pendente; não equivale a
aprovar o critério de visualização. Antes deste incremento não havia controlador
com entrada de comandos, reset ou teste de movimento comandado.

Ambiente observado: WSL2 Ubuntu 26.04, ROS Lyrical, Python 3.14.4. Instalação
legada em simulation/install não é fonte de verdade. Docker/Compose não foram
executados; Compose referencia Dockerfile inexistente na raiz; devcontainer usa
Lyrical, instrução docker.txt usa Humble. Usar o fluxo WSL do README.

Física permanece bloqueada por dados mecânicos. A origem arm2_link varia com a
primeira revoluta e a prismática; a última revoluta muda sua orientação, não a
posição dessa origem. Não interpretar esse frame como ferramenta.
