# S001 — Base cinemática ROS; física condicionada ao modelo

Data: 30/10/2026. Estado: aceito para infraestrutura cinemática; física adiada.

Contexto: já há URDF/RViz e ROS Lyrical; faltam inércias, colisões e calibração.

Decisão: preservar URDF, robot_state_publisher e RViz, adicionar somente controle
convencional de posição no protótipo. Não inventar parâmetros físicos para fazer
Gazebo carregar. Gazebo/ros_gz é a opção física principal futura por integração
ROS já presente no ambiente. Validar versões instaladas quando esse gate abrir.

Alternativas: MuJoCo/PyBullet poderiam servir a experimentos próprios, mas seriam
backends adicionais sem resolver as lacunas CAD; não introduzidos. RViz visualiza
estados, não integra física. O controlador não usa ros2_control e não simula
esforço, aceleração, contato ou colisões.

Consequência: validação de mensagens e movimento é possível agora; simulação
física e transferência ao braço não são entregas concluídas.

Referência consultada: [integração ROS/Gazebo](https://gazebosim.org/docs/latest/ros2_integration/).
