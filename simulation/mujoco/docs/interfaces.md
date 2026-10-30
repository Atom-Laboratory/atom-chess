# Contratos e orientação aos desenvolvedores

## Fonte, modelo compilado e perfil

`atom_mujoco.model.build_bundle(urdf, output)` converte o subconjunto atual de
URDF: árvore conectada, juntas fixed/revolute/prismatic independentes e visuais
mesh. Rejeita Xacro executável, mimic, topologia inválida, recursos ausentes,
eixos não unitários e limites inválidos. Expanda macros antes de usar.
O bundle contém model.xml, quatro STL usados e manifest.json. Não depende de
caminhos absolutos, ROS package resolution ou instalação do código antigo de RL.

Origem, rotação RPY, eixos, faixas, velocidade nominal de referência e escala de
malhas vêm do URDF. Inércias disponíveis em um futuro URDF **ainda não são
importadas**: este conversor implementa exclusivamente o perfil experimental
atual, declarado em `model.PROFILE`. Para outro perfil, implementar a importação
e testes em um incremento específico; não apenas remover o aviso.

Hipóteses v1: cada corpo móvel tem massa 0,1 kg e inércia diagonal
[0,001, 0,001, 0,001] kg·m² no frame da junta. Damping 0,2 e armature 0,01 nas
unidades generalizadas MuJoCo; servos de posição kp=50, kv=5 para todos os eixos.
Esses números são apenas regularização/controle experimental; não são medições
e têm interpretação diferente entre junta prismática e revoluta.
Gravidade [0,0,0], integrador implicitfast, passo de 0,002 s, dez subpassos por
comando (50 Hz de controle). Nenhum limite físico de força foi identificado.
Forças dos atuadores não são saturadas pelo effort=50 do URDF não calibrado.

Geometrias são somente visuais, sem contato; o piso é uma referência gráfica.
Não interpretar `ncon=0` como evidência de movimento livre de colisões.
O ponto laranja/site arm2_frame representa a origem de arm2_link, não TCP.

## API do backend

```python
from atom_mujoco.backend import Simulation

sim = Simulation('simulation/mujoco/runs/prototype-v1')
initial = sim.reset(seed=7, randomize=True)
state = sim.advance([0.3, 0.08, -0.4])
```

- `names`: ordem das juntas definida no manifest, igual a qpos/qvel e atuadores.
- `reset(position=None, seed=None, randomize=False)`: limpa tempo, velocidades,
  ctrl e dados do MuJoCo; por padrão inicia em zero limitado ao intervalo.
  Posição explícita e randomize são mutuamente exclusivos. Aleatorização uniforme
  nos 40% centrais de cada faixa; somente cenário de teste, não currículo de RL.
- `advance(target)`: vetor SI de posições-alvo, inteiro validado antes de alterar
  estado; executa exatamente um intervalo de física, sem aguardar relógio real.
  NaN, infinito, tamanho errado e meta fora dos limites geram ValueError.
- `observe()`: dicionário com cópias dos arrays; modificar a observação não altera
  o simulador. Não acessa ROS, hardware ou política.

| Campo de estado | Semântica |
|---|---|
| time_s | Tempo simulado desde reset |
| position, velocity | qpos/qvel, rad e rad/s ou m e m/s |
| target, reference | Meta solicitada e referência limitada por velocidade |
| actuator_force | Esforço simulado do atuador: N·m ou N; sem calibração |
| arm2_position, arm2_rotation | Origem e matriz 3×3 do frame final no mundo |
| joint_limit_excess | Excesso em relação aos limites de software, nas unidades de cada junta |
| contacts | None: contatos não modelados |
| profile | Identificação do perfil experimental |

Referência do servo varia no máximo velocity_URDF × timestep por subpasso.
Isso não limita rígida/instantaneamente velocidade ou posição da dinâmica:
restrições articulares MuJoCo são suaves e podem permitir pequeno excesso.
Monitore `joint_limit_excess`; não recorte qpos para esconder violações.
Warnings e estados não finitos interrompem advance com RuntimeError; faça reset
e investigue o perfil, não continue coletando transições inválidas.

Um objeto Simulation pertence a um experimento/thread. Para cenários paralelos,
crie instâncias independentes; nenhum callback global é usado. Não há promessa
de igualdade bit a bit entre plataformas ou versões. Hashes verificam XML/STL
do bundle; não autenticam arquivos recebidos de terceiros.

## O que falta para o seu treinamento

Infraestrutura pronta para o exercício: reset, observação, aplicação de comandos,
tempo simulado, render opcional e registro convencional. Você implementará o
adaptador de ambiente em módulo futuro: escolher observações/normalização,
ações (posição ou outra interface acordada), tarefa, meta, reward e critérios
terminated/truncated. Não existe Gym Env ou algoritmo novo nesta entrega.

Primeiro exercício: enviar uma meta por junta, explicar suas unidades, comparar
position/target e pose arm2_frame, repetir após reset com a mesma semente e medir
erro/tempo. Só depois discutiremos a formulação do episódio. Benchmark físico,
contatos, manipulação e transferência real dependem do gate mecânico.

Referências: [Python/viewer](https://mujoco.readthedocs.io/en/stable/python.html),
[modelagem MJCF](https://mujoco.readthedocs.io/en/stable/modeling.html).
