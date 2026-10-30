# S002 — Interface mínima de controle convencional

Data: 30/10/2026. Estado: aceito.

Contexto: sliders e publicação estática não provam entrega de comandos ao
controlador; usuário precisa estudar movimento antes de implementar RL.

Decisão: um servo cinemático independente, sem bibliotecas de treinamento,
recebe posições nomeadas, valida o comando integralmente e limita deslocamento
por velocidade herdada do URDF. JointState em tópico dedicado é reutilizado para
metas por simplicidade; não representa feedback nesse tópico. Serviços Trigger
fazem reset e hold. Status JSON expõe falhas e valores não modelados.

Alternativas adiadas: FollowJointTrajectory/ros2_control exigem contrato temporal
e backend que ainda não existem; não simular compatibilidade. Sem ações de torque
ou ganhos físicos inventados. Sem reaproveitar pacote RL que acoplaria dependências
e escolhas de pesquisa ao transporte ROS.

Consequências: um único publicador de estados por launch, modo de controle
separado do modo sliders. A última meta válida permanece após rejeição; stop é
explícito. Sem aceleração, colisão ou realtime; migração futura deve preservar
validação e documentar novo contrato. Testes DDS demonstram transporte e TF,
sem substituir inspeção visual ou calibração.
