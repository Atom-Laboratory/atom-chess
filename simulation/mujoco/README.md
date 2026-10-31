# Current interactive profile: v4

The default launcher now enables experimental gravity, environment contacts and
moving fingers with a visible control panel. Follow the [v4 controls and developer guide](docs/interactive-controls.md).
Previous three-axis/zero-gravity notes below remain applicable to v3 diagnostic bundles.

[Current English operational guide](docs/mujoco-user-guide.md) | [Integration report](docs/integration-report.md)

# ATOM no MuJoCo — infraestrutura para desenvolver RL

Modelo, simulação, estados, reset e controle convencional estão disponíveis.
Você desenvolverá o ambiente de aprendizado e o agente nas próximas etapas.
Este pacote não tem recompensa, política neural ou loop de treinamento.

**Perfil experimental sem calibração:** cinemática/malhas herdadas do URDF;
massas, inércias e ganhos hipotéticos declarados no manifest. Gravidade zero,
contatos desativados e garra apenas visual. Serve para estudar o pipeline e o
controle do protótipo; não comprova comportamento do braço físico.

## Instalar no Windows — PowerShell

Python 3.12 e ambiente virtual. Não precisa iniciar Ubuntu, ROS ou RViz.
Na raiz do checkout:

```powershell
cd F:\Users\EHD\Github\Atom\atom-chess
py -3.12 -m venv simulation/mujoco/.venv
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy -m pip install -r simulation/mujoco/requirements-windows-py312.lock
& $atomPy -m pip install -e 'simulation/mujoco[test]'
& $atomPy -m pytest simulation/mujoco/tests -q
```

O lock registra o ambiente Windows/Python 3.12 verificado; o comando `py` exige
Python instalado com launcher. Nesta máquina a instalação foi executada com o
Python 3.12.14 do runtime disponível, em ambientes virtuais isolados. O pacote
também pode ser instalado via `python -m pip install -e '.[test]'` em Linux;
essa plataforma não foi validada nesta entrega. OpenGL só é necessário para
visualização/renderização, não para reset/advance e os testes de física.

## Abrir e controlar

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1
```

O script usa `.venv`, compila um bundle em `runs/upright-chess-v3` na primeira vez e
abre o visualizador. Se a política local bloquear scripts, use os comandos Python
abaixo; não é necessário alterar a política do sistema.

Com a janela focada: **Q/A** movem a junta 1, **W/S** a junta 2 e **E/D** a junta 3.
Cada tecla altera a meta em 5% da faixa do protótipo. **R** reinicia; **Espaço**
define a posição atual como meta de hold (não é parada instantânea da dinâmica).
Feche a janela para sair. As teclas são processadas pelo nosso controlador;
os sliders internos de atuadores do viewer não são o contrato público deste pacote.
Velocidade do laço visual acompanha o tempo de parede; testes e experimentos
avançam pelo relógio simulado sem `sleep`.

Alternativa sem script, no mesmo terminal preparado acima:

```powershell
& $atomPy -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --output simulation/mujoco/runs/upright-chess-v3
& $atomPy -m atom_mujoco.cli view --bundle simulation/mujoco/runs/upright-chess-v3
```

`build` exige diretório novo e nunca sobrescreve um bundle anterior. Após mudar
URDF/perfil, use outro diretório e informe-o em `--bundle`. O script não recompila
um bundle já existente; confira source_urdf_sha256 no manifest.

## Demonstração reproduzível e testes

```powershell
& $atomPy -m atom_mujoco.cli demo --bundle simulation/mujoco/runs/upright-chess-v3 --output simulation/mujoco/runs/demo-01.json
& $atomPy -m atom_mujoco.cli render --bundle simulation/mujoco/runs/upright-chess-v3 --output simulation/mujoco/runs/arm.ppm
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
```

Demo: parte de zero e aplica [0.3 rad, 0.08 m, -0.4 rad] por 4 s simulados.
JSON contém trajetória, configuração, hashes, versões, forças simuladas, erros e
excesso dos limites. Saídas exigem nomes novos. Render gera PPM sem bibliotecas
adicionais. O teste gráfico exige contexto OpenGL e compara imagens antes/depois;
em CI sem contexto, mantenha a variável ausente para executar a suíte headless.

Veja [contratos e próximos exercícios](docs/interfaces.md),
[resultados verificados](docs/validation.md) e [ADR S003](../docs/adrs/S003-mujoco.md).

A cena atual tem braço vertical, tabuleiro 8×8 e as três malhas da garra. A garra
acompanha o braço, mas ainda não abre/fecha ou segura peças. Veja as escolhas de
montagem e coordenadas no [ADR S004](../docs/adrs/S004-upright-chess-scene.md).
O URDF permanece no referencial original; apenas o conjunto MuJoCo recebe a
transformação Y→Z. A prismática agora desloca verticalmente na cena.

Atualização v3: 32 peças estilizadas na disposição inicial, identificadas por
cor/tipo/casa no manifest. São referências visuais fixas; ainda não são agarráveis.
O launcher usa runs/upright-chess-v3, preservando os bundles v1/v2 existentes.
Veja [integração futura com acmotion](../docs/learning/deployment-acmotion.md) e
[estado do Gazebo completo](../docs/gazebo-readiness.md).

Comece o estudo pelo [exercício 1: juntas e estados](docs/exercise-01.md), com
exemplo executável em examples/inspect_joints.py.
