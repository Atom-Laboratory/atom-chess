# Visualização diagnóstica do ATOM

Documentação deste módulo: [auditoria](docs/audit.md),
[controle convencional e interfaces](docs/control.md), [validação](docs/validation.md),
[preparação pessoal para RL](docs/learning/README.md).

Para comandar movimento após o build: `ros2 launch atom_description control_demo.launch.py`.
Esse launch usa o controlador cinemático como única fonte de estados. Não o execute
simultaneamente ao launch de sliders abaixo. Não é simulação física.

Esta primeira etapa carrega o protótipo já existente na branch `ros2_simulation`
com RViz e publicação de estados/TF. A referência mecânica oficial, confirmada
pelo responsável em 27/10/2026, é `SCARA Robot.f3d` no repositório `3DSCARAROBOT`.

**O modelo atual não está calibrado.** Seus três eixos móveis, limites, origens e
escala foram preservados do protótipo. Não representa J3, TCP ou garra e não deve
ser usado para validar alcance, colisões ou comandos ao hardware. Os sliders
permitem inspecionar o comportamento do arquivo; não comprovam a mecânica.
Consulte [as evidências e os bloqueios](docs/mechanical-evidence.md).

## Ambiente

Validado nesta máquina: WSL2 Ubuntu 26.04 e ROS 2 Lyrical. Abra um terminal Ubuntu
e carregue o ambiente. O código abaixo usa um workspace de build externo ao
repositório para não depender dos arquivos antigos em `simulation/install`.

```bash
source /opt/ros/lyrical/setup.bash
export ATOM_SIM_SOURCE=/mnt/f/Users/EHD/Github/Atom/atom-chess/simulation
export ATOM_SIM_WORK="$HOME/atom-simulation-ws"
mkdir -p "$ATOM_SIM_WORK"
cd "$ATOM_SIM_WORK"
colcon --log-base "$ATOM_SIM_WORK/log" list --base-paths "$ATOM_SIM_SOURCE/src"
colcon --log-base "$ATOM_SIM_WORK/log" build \
  --base-paths "$ATOM_SIM_SOURCE/src" --packages-select atom_description \
  --build-base "$ATOM_SIM_WORK/build" --install-base "$ATOM_SIM_WORK/install"
source "$ATOM_SIM_WORK/install/setup.bash"
QT_QPA_PLATFORM=xcb ros2 launch atom_description view_robot.launch.py
```

O workspace deve ser novo ou conter somente esta versão do pacote. Evite carregar
outros overlays com outro `atom_description`. A consulta `ros2 pkg prefix
atom_description` deve apontar para o install recém-compilado.

A estrutura de pacote único em `src/` foi mantida: não há pacote aninhado ou
`atom_control` nesta branch. Se novos pacotes forem necessários, reorganizar o
workspace nesse momento, sem criar manifests pai/filho concorrentes.

## Modos de execução

```bash
# Sem janelas: publica a pose inicial e suas transformações.
ros2 launch atom_description view_robot.launch.py gui:=false rviz:=false

# RViz sem sliders.
QT_QPA_PLATFORM=xcb ros2 launch atom_description view_robot.launch.py gui:=false

# Consultas em outro terminal com o mesmo ambiente carregado.
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo world arm2_link
```

Existe uma única fonte de `/joint_states`: GUI ou publisher sem GUI, conforme o
argumento. `use_sim_time` é falso por padrão; ativá-lo exige `/clock` externo.
Nenhum controlador ou transporte físico é iniciado por este launch.

O prefixo `QT_QPA_PLATFORM=xcb` seleciona X11 somente para essa execução. Nesta
máquina, a seleção automática de Qt/Wayland causou `Invalid parentWindowHandle`
no renderizador GLX do RViz; XCB permitiu inicializar a janela e OpenGL. Em um
ambiente que não apresente esse problema, o prefixo pode ser omitido.

Se RViz/Qt não abrir, verifique WSLg e `DISPLAY`/`WAYLAND_DISPLAY`. O modo sem
janelas permite testar ROS independentemente da interface gráfica. O arquivo
legado `docker.txt` usa Humble e não é o procedimento validado para esta etapa.

## Verificação

Com as variáveis e o ambiente acima carregados:

```bash
colcon --log-base "$ATOM_SIM_WORK/log" test \
  --base-paths "$ATOM_SIM_SOURCE/src" \
  --build-base "$ATOM_SIM_WORK/build" --install-base "$ATOM_SIM_WORK/install" \
  --packages-select atom_description --event-handlers console_direct+
colcon test-result --test-result-base "$ATOM_SIM_WORK/build" --verbose
```

Os testes verificam expansão Xacro, estrutura da árvore, recursos de malha,
limites estruturalmente consistentes e um launch real sem GUI. O teste de launch
observa `/joint_states`, `/tf` e `/tf_static`. Eles não aprovam dimensões, eixos
ou limites do hardware.

Para inspecionar o URDF expandido, gere-o na área de build:

```bash
xacro "$ATOM_SIM_SOURCE/src/urdf/atom.urdf.xacro" > "$ATOM_SIM_WORK/atom.urdf"
check_urdf "$ATOM_SIM_WORK/atom.urdf"
```

## Próximo incremento

Abrir a revisão oficial F3D e recuperar a estrutura rígida, referências dos
eixos, zeros, distâncias entre centros e TCP. Comparar suas geometrias com as
sete malhas existentes. Registrar as evidências antes de mudar transformações
ou habilitar o contrato completo J1/J2/J3/Z/garra.
