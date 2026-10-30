# ATOM Chess

Guias do usuário: [Gazebo](simulation/docs/user-guide-gazebo.md) e
[primeiros passos em RL](simulation/docs/learning/user-guide-rl.md).

Projeto de robô para xadrez. Esta branch, `ros2_simulation`, contém a biblioteca
de visão `acvision` e a descrição ROS 2 do braço. Ainda não existe uma partida
autônoma integrada. O URDF é um protótipo sem calibração física.

## Começar pelo módulo

| Módulo | Documentação e relatório |
|---|---|
| Visão C++/OpenCV | [Guia](Software/acvision/README.md), [auditoria](Software/acvision/docs/audit.md) |
| ROS 2 e controle simulado | [Guia](simulation/README.md), [auditoria](simulation/docs/audit.md) |
| MuJoCo e preparação de experimentos | [Instalação, visualização e testes](simulation/mujoco/README.md) |
| Mecânica | [Fontes e lacunas](docs/mechanics/README.md) |
| Preparação para RL | [Trilha de estudo](simulation/docs/learning/README.md) |
| Projeto e integração | [Arquitetura](docs/architecture.md), [roadmap](docs/roadmap.md) |

[Índice completo por módulo](docs/README.md). Comece pelos comandos do módulo
que deseja executar; o build CMake da raiz não compila o pacote ROS.

O código de treinamento local em `simulation/learning` vem de uma etapa anterior,
está fora do escopo atual e não é dependência da simulação. O desenvolvimento de
RL será conduzido pelo responsável, com orientação e revisão em etapas.
