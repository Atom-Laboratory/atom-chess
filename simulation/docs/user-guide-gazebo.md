# Guia do usuário — Gazebo no ATOM Chess

Revisão: 30/10/2026. Para quem está começando no Windows.

**Estado atual:** Gazebo e dependências ROS estão instalados e o servidor
executou um mundo de exemplo com sucesso. O ATOM completo com J1/J2/J3/Z,
garra articulada e peças agarráveis ainda não tem um launch Gazebo validado.
Este guia ensina a abrir e conhecer a ferramenta disponível; o controle atual
do braço e o início dos estudos de RL usam o MuJoCo.

## 1. Qual terminal abrir

Abra **PowerShell** pelo menu Iniciar. Execute:

```powershell
wsl -d Ubuntu
```

Agora o terminal está dentro do Ubuntu. Os comandos bash deste guia devem ser
executados aí, não diretamente no PowerShell. A janela gráfica do Gazebo aparece
na área de trabalho Windows por meio do WSLg; o processo está no Ubuntu.

| Ferramenta | Onde executar | Para quê |
|---|---|---|
| Gazebo + ROS 2 | Ubuntu/WSL | Física e integração ROS, quando o modelo completo estiver disponível |
| MuJoCo do projeto | PowerShell/Windows | Controle convencional e exercícios para desenvolver RL |
| RViz | Ubuntu/WSL | Inspecionar descrição/TF; não é simulador físico |
| Fusion | Windows | Inspecionar montagem e extrair dados mecânicos |

## 2. Preparar o terminal Ubuntu

```bash
source /opt/ros/lyrical/setup.bash
gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix gz_ros2_control
ros2 pkg prefix joint_trajectory_controller
```

Resultado verificado: Gazebo **10.4.0**, pacotes ROS em /opt/ros/lyrical.
Faça o `source` em cada terminal novo. Não carregar o venv Windows do MuJoCo
dentro do WSL. Se a instalação de outro desenvolvedor não tiver esses pacotes,
ele precisa configurar primeiro ROS Lyrical/Gazebo compatíveis; os comandos
acima são diagnóstico, não instalação. gripper_controllers não foi localizado
nesta máquina; o controlador final depende do mecanismo de garra identificado.

## 3. Primeiro teste, sem janela

```bash
gz sim -s -r --iterations 20 \
  /opt/ros/lyrical/opt/gz_sim_vendor/share/gz/gz-sim/worlds/shapes.sdf
```

Esse comando **foi executado e terminou com código 0**. Ele inicia somente o
servidor, avança 20 iterações do mundo de formas simples e encerra. É normal não
abrir janela e não imprimir nada. Isso verifica o mecanismo de simulação, não
o modelo do braço. O caminho corresponde à instalação desta máquina.

## 4. Abrir a interface gráfica

No mesmo Ubuntu preparado:

```bash
gz sim /opt/ros/lyrical/opt/gz_sim_vendor/share/gz/gz-sim/worlds/shapes.sdf
```

Você deve ver formas geométricas do exemplo. **Não é o ATOM**. Esse procedimento
segue o mundo incluído e o guia oficial; a interface gráfica Gazebo ainda não
teve inspeção visual aprovada nesta entrega. Se houver mais de uma versão,
consulte `gz sim --versions`; `gz sim --force-version 10 shapes.sdf` seleciona
Jetty conforme a documentação oficial, desde que o recurso seja resolvido.

Na janela:

1. Localize **Entity Tree**, a árvore dos objetos, e selecione uma forma.
2. Veja suas propriedades no **Component Inspector**. Inspecionar uma propriedade
   não significa que o robô real disponha desse sensor.
3. Use o controle **Play/Pause** para executar ou pausar a física. Compare o tempo
   simulado antes/depois; câmera da cena e movimento físico são coisas distintas.
4. O menu de plugins permite habilitar painéis ausentes. Evite transformar objetos
   manualmente para avaliar controle: isso altera o cenário, não envia uma meta
   ao controlador.
5. Feche a janela e encerre o comando com **Ctrl+C** se ele continuar no terminal.
   Não deixe múltiplas cópias do mesmo mundo para um teste.

Para orbit/zoom e ferramentas de seleção, acompanhe a [documentação ilustrada
da GUI Jetty](https://gazebosim.org/docs/jetty/gui/). Atalhos do MuJoCo Q/A etc.
pertencem ao nosso viewer MuJoCo, não controlam juntas no Gazebo.

## 5. Onde está o braço completo no Gazebo?

Ainda em preparação. Não há comando `ros2 launch ... gazebo...` do ATOM validado
para publicar aqui. `view_robot.launch.py` e `control_demo.launch.py` são os modos
de diagnóstico ROS existentes; não iniciam Gazebo. Abrir um URDF visual nele
também não cria automaticamente juntas físicas, controladores e preensão.

O próximo guia operacional do braço será ampliado quando estes itens passarem:

| Recurso | Critério antes de disponibilizar comando ao usuário |
|---|---|
| Modelo inteiro | J1/J2/J3/Z e garra identificados, frames/eixos/limites conferidos no CAD |
| Controle | Cada eixo responde ao controlador e publica feedback; sem duas fontes de JointState |
| Garra | Abre/fecha com vínculo correto dos dedos e calibração da abertura |
| Peças | Corpos dinâmicos, colisão, massa/atrito, reset reproduzível |
| Preensão | Levantar, transportar e soltar por contatos, sem teletransporte/solda como prova |
| acmotion | Adaptador testado, unidades e sinais corretos, timeout/cancelamento e feedback |

Já temos uma captura CAD da garra com -45°..+10° em torno do Z local. É dado útil,
mas não identifica sozinho todos os elos/passivos e o eixo motor. A extração será
feita do CAD existente. Consulte [estado mecânico](../../docs/mechanics/gripper-cad-evidence.md)
e [inventário detalhado do Gazebo](gazebo-readiness.md).

## 6. Problemas comuns

| Sintoma | Próxima ação |
|---|---|
| `gz: command not found` | Confirme que está no Ubuntu e execute o source do ROS; não digite esse comando no PowerShell |
| Nada abriu no teste de 20 iterações | Esperado: `-s` não abre GUI; use o comando da etapa 4 |
| GUI não abre | No Ubuntu consulte `printenv DISPLAY WAYLAND_DISPLAY`; confira WSLg. Registre erro completo do terminal; servidor pode funcionar mesmo com falha gráfica |
| “Package not found” | Verifique o nome e instalação; não indica erro no modelo do braço |
| Formas aparecem, braço não | Esperado para shapes.sdf; ainda falta o launch Gazebo do ATOM completo |
| JointState/TF não aparece ao abrir shapes | Não foi iniciada uma bridge ROS ou um robô; mundo Gazebo não implica tópicos ROS automaticamente |
| Robô visível mas parado em RViz | Expandir Status: Error e verificar TF; RViz é outro aplicativo e não é teste de Gazebo |

Não reinstale tudo por um erro de TF. Guarde comando, versão, nome do mundo e
mensagem de erro para reproduzir o problema.

## 7. Como isso se relaciona com RL

O simulador fornece física. O ambiente define tarefa, observações, ações e
recompensas. O agente aprende uma política; o viewer só mostra o processo.
Comece pelo [guia de RL](learning/user-guide-rl.md), que usa a infraestrutura
MuJoCo já verificada. A avaliação futura do sistema ROS no Gazebo complementa
o treinamento; não exige que todo treinamento tenha uma janela aberta.
