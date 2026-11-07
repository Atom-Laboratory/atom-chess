# Do treinamento ao acmotion e ao braço físico

## O que é o modelo treinado

O modelo geométrico/dinâmico (MJCF/URDF) descreve o robô simulado. Uma política
treinada é outro artefato: recebe observações e uma meta e produz comandos. O
treinamento ajusta seus parâmetros usando experiências; na execução, inferência
usa esses parâmetros sem continuar treinando. Os nomes, unidades, frequência,
normalização e versão do modelo físico fazem parte do contrato da política.
Um arquivo de pesos sozinho é insuficiente.

Não é necessário treinar uma rede para cada lance ou cada casa. Um controlador
condicionado à meta pode mover o braço para múltiplos alvos dentro do domínio
validado. Pegar, transportar e soltar também podem ser tarefas de uma política
única condicionada, ou habilidades distintas coordenadas por uma máquina de
estados. A escolha exige experimentos; não está decidida antecipadamente.
Primeiro validar alcance convencional e garra. Não há motivo para substituir
o planejamento geométrico de uma tarefa simples por aprendizado sem benefício
medido. Stockfish decide xadrez; a política de controle não decide lances.

## Interface real encontrada em main

Main f72c893 is now merged into ros2_simulation (8fbc7aa). These modules are
present and their headless tests pass; the policy/hardware bridge remains
unimplemented. Source files examined:
software/acmotion/include/motion/{motion_planner,joint_trajectory,
motion_execution,motion_transport,physical_task}.hpp e README do módulo.

```text
Lance validado
  → TaskPlanner → PhysicalTask
  → MotionPlanner → Pose (mm, toolYawRad, gripperPercent)
  → InverseKinematics → JointSegment
  → MotionExecution → MotionProtocol/IMotionTransport (ACM1)
  → ESP32-S3 → interpolação/perfis/STEP-DIR
```

JointTarget já representa joint1Rad, joint2Rad, joint3Rad, zMm e gripperPercent.
JointSegment acrescenta sequence e durationMs. MotionExecution sequencia envio,
ACK/DONE, timeout, cancelamento e eventos de limite/parada; não é servo rápido.
IMotionTransport envia/recebe linhas do protocolo; não é interface de política.
MotionPlanner já descreve oito fases convencionais: aproximar, descer, fechar,
levantar, transportar, descer, abrir e retrair. Elas não precisam ser aprendidas
se o planejamento convencional satisfizer a tarefa.

## Integração proposta, ainda não implementada

Criar uma estratégia de geração de segmentos ao lado do planejamento atual,
executada no computador/SBC. Recebe meta e observação validada; produz segmentos
com duração, posição e abertura. Um validador externo à política verifica
unidades, sinais, zeros, finitude, limites, variação e estado do controlador.
Somente segmentos aprovados seguem para MotionExecution e ACM1. Controle
convencional deve permanecer disponível para comparação e recuperação.

Não enviar torque de uma política ao protocolo atual de posições. Não executar
o loop de uma política a 50 Hz dentro de execute(), que aguarda ACK/DONE por
segmento. Primeiro medir latência e definir agendamento/preempção e telemetria.
ACK/DONE indicam estados do protocolo; não comprovam posição medida, sucesso
de preensão ou ausência de perda de passos. Política em malha fechada requer
feedback com idade máxima, estado articular e confirmação de peça/garra. Esse
contrato de observação real não foi comprovado nesta revisão.

Conversões obrigatórias: MuJoCo usa metros para a prismática; acmotion usa mm
em zMm e Pose. J1/J2/J3 usam radianos. gripperPercent é abertura 0..100, e não
diretamente ângulo de dedo/servo; mapear após calibração. Mundo da cena tem
transformação Rx(+90°)/offset e tabuleiro hipotético: não enviar coordenadas
globais da cena diretamente ao CoordinateMapper real.

O protótipo atual tem apenas 2 revolutas + 1 prismática e garra fixa. O contrato
real espera 3 revolutas + Z + abertura: não existe correspondência completa.
Não preencher J3 com zero arbitrário nem inventar abertura para forçar adaptação.

## Etapas para colocar a política no robô

1. Completar e conferir montagem: J1/J2/J3/Z, garra, ferramenta/TCP, sinais,
   limites, dimensões e colisões; depois massas/inércias e atuadores.
2. Controle convencional deve mover e pegar/soltar peças físicas no simulador;
   verificar quedas, escorregamento, contatos e reset sem sobreposições inválidas.
3. Responsável define e implementa ambiente/observações/ações/reward. Escolher
   tarefa e algoritmo; treinar com avaliação independente e baseline convencional.
4. Exportar política mais metadados/normalização/modelo, validar igualdade entre
   inferência de treinamento e runtime, medir custo na SBC e validar rejeições.
5. Testar o sistema completo no Gazebo via adaptador ROS, com atraso, erros,
   cancelamento e feedback. Uma política treinada no MuJoCo pode ser avaliada no
   Gazebo, mas a diferença de física pode degradar resultado; não há transferência
   automática garantida por usar ROS.
6. Calibrar bancada: homing, zeros, limites, transmissões, sentidos, garra, TCP,
   tabuleiro e latência. Comparar trajetórias simuladas/reais, variar parâmetros
   simulados quando justificável, iniciar ensaios supervisionados de baixa energia
   e só avançar com critérios objetivos de sucesso/parada.

O arquivo treinado fica no runtime de inferência da SBC, não precisa ir para o
ESP32. ESP32 mantém execução e proteções locais. Treinamento no microcontrolador
ou inferência nele seria outra decisão arquitetural, não parte desta proposta.
