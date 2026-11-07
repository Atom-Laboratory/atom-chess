# Controle convencional do protótipo

Este módulo está no pacote atom_description por enquanto: script independente
em src/scripts/kinematic_controller.py, sem dependência do experimento RL. A
separação em outro pacote deve ocorrer quando houver backend físico ou hardware.

## Executar

Compile e carregue o workspace conforme o [README](../README.md). Execute somente
um launch por domínio ROS; não mantenha view_robot e control_demo simultâneos.

```bash
QT_QPA_PLATFORM=xcb ros2 launch atom_description control_demo.launch.py
# Para testar sem janela: acrescente rviz:=false.
```

Em outro terminal com o mesmo overlay:

```bash
ros2 topic pub --once /atom_sim/command sensor_msgs/msg/JointState \
  "{name: [joint_base_to_link1, joint_z_axis_arm1, joint_arm1_link_arm2_link], position: [0.3, 0.08, -0.4]}"
ros2 topic echo /joint_states sensor_msgs/msg/JointState --once
ros2 topic echo /atom_sim/status std_msgs/msg/String --once
ros2 run tf2_ros tf2_echo world arm2_link
ros2 service call /atom_sim/stop std_srvs/srv/Trigger '{}'
ros2 service call /atom_sim/reset std_srvs/srv/Trigger '{}'
```

O cenário acima corresponde à meta usada no teste de integração. Os comandos
CLI são a forma manual do mesmo contrato exercitado pelo teste rclpy.

## Contratos

| Interface | Tipo / semântica |
|---|---|
| /atom_sim/command | sensor_msgs/JointState: todos os nomes exatamente uma vez, posições finitas dentro dos limites URDF; ordem arbitrária; velocity/effort vazios |
| /joint_states | sensor_msgs/JointState: posição e velocidade simuladas, stamp ROS; effort vazio |
| /atom_sim/status | std_msgs/String contendo JSON: profile, command_sequence, event, elapsed_s, names, position, target, error, collisions, effort |
| /atom_sim/reset | std_srvs/Trigger: reinicia posições em zero limitado ao intervalo URDF e tempo de experimento; não é homing |
| /atom_sim/stop | std_srvs/Trigger: fixa meta na posição atual; não é parada de emergência de hardware |
| /tf, /tf_static | Transformações publicadas por robot_state_publisher; arm2_link continua sem TCP |

Comando válido substitui a meta anterior. Inválido é rejeitado integralmente e
mantém a meta anterior (não implica parada); status informa o motivo. Header de
comando não agenda execução, não há fila de trajetórias ou garantia de tempo real.
Use um cliente de comando por experimento. QoS confiável/volátil, depth 10.

Controle a 20 Hz: aproxima cada posição da meta com deslocamento máximo
velocity_URDF × dt. dt é tempo monotônico decorrido limitado a 0,05 s; atraso não
causa salto de recuperação. elapsed_s soma os dt efetivamente executados e pode
ser menor que tempo de parede sob carga. Timestamps usam relógio ROS normal;
este launch não usa /clock. Não há aceleração, esforço, contato ou dinâmica.
Limites de software herdados não são limites físicos certificados.

Para registrar um experimento, rosbag2 pode gravar /atom_sim/command,
/joint_states, /atom_sim/status, /tf e /tf_static quando instalado. Esse fluxo de
gravação não foi validado nesta entrega; a telemetria é exercitada pelo teste.
`collisions: null` e `effort: null` significam não modelados, nunca zero medido.

## Validação

Os testes de núcleo verificam rejeição atômica, nomes duplicados, NaN/infinito,
limites, velocidade, dt, parada e reset. O teste com ROS real envia meta, observa
estado intermediário e final, confirma TF alterado, rejeita meta inválida e chama
stop/reset. Nenhum teste chama agente, recompensa ou treinamento.

Visualização humana da montagem e dinâmica continuam critérios separados.
[ADR S002](adrs/S002-control.md).
