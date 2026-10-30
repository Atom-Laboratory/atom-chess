# Exercício 1 — das juntas ao movimento observado

Objetivo: entender quais grandezas o backend fornece e o significado de um
comando antes de formular um problema de aprendizado. Use o ambiente já instalado
e o bundle gerado pelo launcher. Execute no PowerShell, na raiz do repositório:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/inspect_joints.py --bundle simulation/mujoco/runs/upright-chess-v2 --output simulation/mujoco/runs/exercise-01.json
```

Use um nome novo em --output ao repetir. O script primeiro reinicia em zero,
comanda apenas uma junta durante 4 s simulados e registra a resposta; depois
reinicia novamente e reproduz a mesma sequência para comparar. O processo é
repetido para cada junta. Não inicia treinamento nem precisa de janela.

## Antes de olhar o resultado

Leia o URDF e faça três previsões por escrito:

1. Ao mudar a primeira junta, quais coordenadas de arm2_frame devem mudar?
2. Ao mudar a prismática, em qual direção se desloca esse frame?
3. Ao mudar a última junta, a origem de arm2_frame muda de posição?

Depois compare com frame_translation_delta_m e frame_rotation_delta_rad no JSON.
O arquivo examples/inspect_joints.py mostra o uso mínimo de reset/advance/observe.
`target` é a solicitação; `final_position` é a resposta da dinâmica sintética.
`joint_error` é a diferença nas unidades de cada junta. Não some radianos e metros
para interpretar um erro físico escalar sem definir normalização.

`replay_max_error` compara estados articulares de duas execuções completas. Zero
comprova repetição local desse cenário e versão, não portabilidade bit a bit.
Reset é uma intervenção no simulador, não uma ação física disponível ao braço.

## Seu trabalho

Crie uma cópia local do exemplo e altere a meta da primeira junta de 0,3 para
0,6 rad. Preveja a posição final do frame antes de executar. Depois reduza a
duração de 4 s para 0,1 s e compare erro de controle: a referência e a dinâmica
precisam de tempo para responder. Não escreva uma política para compensar um
erro de geometria que ainda depende do CAD.

Critério de conclusão: explicar as três previsões, distinguir posição-alvo de
posição obtida, reconhecer unidades e explicar por que reset permite comparar
experimentos. Envie suas previsões e resultados para revisão; a próxima decisão
será qual tarefa de controle você quer aprender e quais observações ela exige.

## Resultado de referência do protótipo atual

Depois de fazer suas previsões, use esta conferência:

- Primeira junta, 0,3 rad na cena upright-chess-v2: deslocamento aproximado [-0,00983, 0,06501, 0] m;
  rotação de 0,3 rad.
- Prismática, 0,08 m: deslocamento [0, 0, 0,08] m, orientação preservada.
- Última junta, -0,4 rad: origem final preservada, rotação de 0,4 rad em módulo.

Esses valores vêm da geometria do URDF e não validam o TCP ou a montagem física.
Bundles antigos prototype-v1 usam Y vertical; a cena v2 aplica [x,y,z]→[x,-z,y+0.035].
Use o bundle v2 nos comandos acima para comparar com estes resultados atuais.
