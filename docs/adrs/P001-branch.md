# P001 — Auditar e evoluir a branch efetiva

Data: 30/10/2026. Estado: aceito.

Contexto: o planejamento original examinou main; o checkout atual é
ros2_simulation, e6c9b1e. Há alterações anteriores locais em build, ROS e RL.

Decisão: preservar a branch e o trabalho anterior; documentar módulos existentes
e pretendidos separadamente; commits com listas explícitas de arquivos. Relatórios
ficam por módulo e o índice central aponta para eles. Não importar módulos de
main nem limpar caminhos duplicados/artefatos como efeito lateral.

Alternativa rejeitada: reconstruir o projeto com base na arquitetura de main,
pois alteraria o objeto da auditoria e dificultaria atribuir regressões.

Consequência: integração de xadrez permanece pendente. Código RL anterior fica
preservado localmente e fora dos commits desta entrega. Push apenas fast-forward,
após conferência do remoto; nunca force-push.
