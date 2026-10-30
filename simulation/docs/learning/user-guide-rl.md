# Guia do usuário — começar RL no ATOM Chess

Revisão: 30/10/2026. Seu objetivo inicial é entender o controle do protótipo e
depois construir pessoalmente um ambiente de aprendizado, com revisão em etapas.
Não há treinamento novo neste guia. A infraestrutura atual é MuJoCo no Windows;
Gazebo é o caminho de integração ROS em preparação.

## 1. O que significa “modelo”

| Termo | O que é no ATOM |
|---|---|
| Modelo do robô | Geometria, juntas e física em URDF/MJCF; define o mundo simulado |
| Ambiente | Sua tarefa: o que observar, comandar, recompensar e quando terminar |
| Política/modelo treinado | Função com parâmetros aprendidos: observação + meta → ação |
| Treinamento | Coletar experiências e atualizar a política |
| Inferência | Executar a política já treinada para gerar ações |
| Episódio | Uma tentativa iniciada por reset e encerrada por sucesso/falha/timeout |
| Transição | Observação, ação, recompensa e próxima observação de um passo |
| Retorno | Soma de recompensas, possivelmente com desconto ao longo do tempo |
| Exploração | Experimentar ações para coletar informação durante treinamento |

Não é necessário um modelo por lance. Uma política condicionada à meta pode
receber muitos alvos. Agarrar envolve contatos e pode exigir tarefa/habilidade
própria; a organização entre habilidades será uma decisão sua após o baseline.

## 2. Abrir o ambiente certo

Abra **PowerShell** no Windows. Na máquina atual:

```powershell
cd F:\Users\EHD\Github\Atom\atom-chess
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1
```

O launcher usa a `.venv` local e o bundle `runs/upright-chess-v3`. Ele abre o
MuJoCo com braço vertical, tabuleiro, garra visual e 32 peças estilizadas.
**Q/A**, **W/S** e **E/D** alteram as três metas articulares; **R** reinicia e
**Espaço** usa a posição atual como meta. Feche a janela para encerrar.
Clique na área da cena antes de usar teclas. Arrastar a câmera muda apenas a
vista; não é comando de movimento do braço.

Se `.venv` não existir, faça a [instalação do módulo](../../mujoco/README.md).
Não precisa de Ubuntu, ROS ou Gazebo para esses exercícios. Não altere a política
de execução do Windows para rodar o script: o README oferece comandos Python
equivalentes se o PowerShell bloquear scripts.

## 3. Rodar o controle convencional sem janela

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
```

Esse modo executa uma meta por 4 s simulados e salva JSON. Cada execução gera
outro arquivo; é normal não abrir janela. Leia:

- `finite`: deve ser true, indicando posições numéricas finitas.
- `final_error`: erro final por junta; duas usam radianos, uma usa metros.
- `max_joint_limit_excess`: excesso máximo do intervalo articular durante a demo.
- `contacts: null`: contatos desativados; não significa “zero colisões verificado”.
- `trajectory`: estados ao longo do tempo; `manifest`: versão, perfil e hashes.

Os erros muito pequenos da demo resultam do perfil sintético simples; não são
precisão medida no hardware nem resultado de aprendizado.

## 4. Fazer o exercício de juntas

```powershell
$atomResult = 'simulation/mujoco/runs/exercise-' + [guid]::NewGuid().ToString('N') + '.json'
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/inspect_joints.py --bundle simulation/mujoco/runs/upright-chess-v3 --output $atomResult
```

O nome único evita o erro “Choose a new output path”; o script preserva resultados
existentes. Cada junta recebe uma meta isolada e a sequência é repetida após
reset. Confira `replay_max_error`, deslocamento e rotação do frame final. Faça
as previsões propostas no [exercício 1](../../mujoco/docs/exercise-01.md) antes
de olhar o resultado. Copie o exemplo para um arquivo seu e faça as alterações
propostas ali; o backend já existente não precisa ser reescrito.

Critério: explicar por que a prismática sobe em Z na cena, por que a última
revoluta gira a orientação da origem final sem deslocá-la e por que isso ainda
não define o TCP da garra. Saber repetir esse exercício é a primeira entrega.

## 5. Entender o passo do simulador

Exemplo curto, já disponível na API, para estudar em seu código:

```python
from atom_mujoco.backend import Simulation

sim = Simulation('simulation/mujoco/runs/upright-chess-v3')
initial = sim.reset(seed=7, randomize=True)
next_state = sim.advance([0.3, 0.08, -0.4])
print(next_state['position'], next_state['velocity'])
```

Um `advance` executa 10 subpassos de 0,002 s, totalizando 0,02 s simulados. A
entrada é posição-alvo SI, não torque ou velocidade. O backend valida a meta e
limita a velocidade da referência; a dinâmica pode diferir dela. Em testes não
precisamos aguardar tempo real ou abrir o viewer.

Isso ainda não é `env.step(action)`: faltam a tarefa e as decisões de aprendizado.
Os arrays recebidos são cópias; alterar uma observação não muda o simulador.
Consulte [contratos](../../mujoco/docs/interfaces.md) antes de propor ações novas.

## 6. Sua primeira decisão de pesquisa

Escreva uma página respondendo aos itens abaixo e traga para revisão. Não precisa
instalar bibliotecas novas para responder.

| Decisão | Pergunta a responder | Como conferir sua proposta |
|---|---|---|
| Tarefa | Quer começar atingindo uma meta articular ou uma pose? | O controle convencional já resolve o cenário? Qual melhoria pretende medir? |
| Observação | Quais posições, velocidades, metas e histórico são necessários? | Listar dimensão, unidade e disponibilidade no robô físico |
| Ação | Metas absolutas ou incrementos limitados? | Definir escala/frequência e tratamento de entrada inválida |
| Episódio | Como inicia, quando tem sucesso e quanto dura? | Casos de sucesso, falha e timeout separados |
| Recompensa | Que comportamento quer incentivar e que atalhos podem surgir? | Ordenar manualmente alguns estados bons/ruins antes de treinar |
| Avaliação | Quais metas ficam fora do treinamento? | Comparar com o mesmo baseline em condições iguais |

Sugestão para discussão: começar por metas articulares no protótipo, pois isso
usa as interfaces verificadas. Não é uma decisão definitiva da pesquisa. Pegar
peças ainda não é cenário válido: elas são fixas e a garra não articula.

## 7. Etapas que você implementará depois da revisão

1. **Adaptador do ambiente:** definir observações e ações; implementar reset e
   step com composição do backend, preservando validação de comandos.
2. **Semântica do episódio:** sucesso/falha em `terminated`; limite de tempo em
   `truncated`. Um timeout não deve ser tratado automaticamente como sucesso.
3. **Recompensa:** implementar sua proposta e testar exemplos pequenos antes
   de iniciar coleta longa; verificar unidades e possíveis formas de explorar erros.
4. **Algoritmo:** comparar PPO, SAC e TD3 e então escolher dependências e uma
   primeira implementação acompanhada. Algoritmo não corrige modelo físico errado.
5. **Avaliação:** separar treino/validação/teste, usar sementes registradas,
   guardar falhas e comparar política com controle convencional.

Não há arquivo de agente pronto ou comando de treino MuJoCo novo a executar.
`simulation/learning` é experimento local anterior, não a implementação desta
trilha. Não misturar seus resultados com o perfil MuJoCo como se fossem iguais.

Se usarmos Gymnasium, `reset` retorna `(observation, info)` e `step` retorna
`(observation, reward, terminated, truncated, info)`. Esta é uma referência para
sua implementação futura; o backend atual oferece outra interface. Estude o
[guia oficial de ambiente customizado](https://gymnasium.farama.org/introduction/create_custom_env/).

## 8. O que registrar em cada experimento

Guarde configuração, seed, hash do URDF/MJCF, manifest/perfil, versão de bibliotecas,
tarefa, unidades, frequência, critério de término e métricas. O resultado deve
explicar sucesso e falha, não apenas retorno médio. Para uma política futura,
salve também pesos, normalização, ordem das entradas/saídas e compatibilidade do
runtime; registre desempenho de inferência na SBC antes de uso real.

Compare erro por eixo, tempo até a meta, excesso de limites, falhas e repetição
do reset. Para preensão futura, acrescentar retenção, queda e colocação: isso
requer corpos com contatos. Não contar objetos presos artificialmente como
sucesso físico.

## 9. Depois do treinamento: acmotion e hardware

A política executará no computador/SBC se essa arquitetura for confirmada. Seu
resultado passará por validação e adaptação a segmentos de movimento, antes de
MotionExecution/ACM1/ESP32. O ESP32 continua responsável pela execução dos motores.
Não copiar simplesmente os pesos para a placa e enviar torque a um protocolo
de posições. Há diferença de unidade: MuJoCo usa metros na prismática e acmotion
usa mm em zMm. O protótipo também não tem ainda todos os graus de liberdade reais.

Leia o [plano de integração baseado nos headers de main](deployment-acmotion.md).
Ele descreve o que existe e o que falta: telemetria, tempo, calibração e adaptação.
No futuro, testar a integração ROS no Gazebo não elimina ensaios de bancada nem
garante transferência da física do MuJoCo ao braço real.

## 10. Problemas comuns

| Mensagem/sintoma | Solução |
|---|---|
| Demo imprime JSON e não abre janela | Esperado; execute o launcher sem `-Mode demo` para visualizar |
| Choose a new output path | Use nome novo ou o comando com GUID da etapa 4 |
| Braço antigo deitado ou sem peças | Feche o viewer antigo e abra pelo launcher atual; ele usa upright-chess-v3 |
| Arquivo/bundle não encontrado | Execute o launcher/demo primeiro a partir da raiz correta |
| Meta inválida | Confira tamanho, valores finitos, unidades e intervalos no manifest |
| Garra/peças não respondem | São visuais no perfil atual; não há comando de preensão implementado |
| GUI falha, testes de física passam | Renderização/OpenGL é uma camada distinta; registre o erro completo |

Próxima entrega sua: previsões e resultados do exercício 1, mais a página de
decisões da etapa 6. A partir disso, avançamos juntos para o primeiro ambiente.
