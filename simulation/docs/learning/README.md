# Preparação para RL — estudo guiado

O agente será desenvolvido por você. Não é necessário instalar Gymnasium,
PyTorch ou Stable-Baselines3 para executar ROS, consultar estados ou controlar
o protótipo. [Escopo e experimento anterior](adrs/L001-scope.md).

## Etapa atual: entender o que o robô simulado representa

Leia src/urdf/atom.urdf.xacro e observe TF de world até arm2_link. Juntas revolutas
usam radianos; a prismática usa metros. O eixo de translação atual é Y, não Z,
apesar do nome. Isso vem do protótipo e precisa de confirmação CAD.

Seu exercício: mover uma junta por vez, registrar posição articular e pose do
frame arm2_link, prever qual componente muda e comparar com TF. A última junta
altera orientação dessa origem sem deslocá-la; o TCP ainda não existe.
Critério: explicar as três respostas e distinguir erro do modelo de erro de
controle. Erro comum: chamar o frame final de ponta da garra ou assumir eixo Z
pelo nome da junta. Arquivos: URDF, RViz e interface de controle ROS documentada
no guia de simulação. Não escrever recompensa ou rede neural ainda.

## Próximas etapas, sem implementação antecipada

| Etapa / conceito | Decisão e trabalho pessoal | Evidência e erro comum |
|---|---|---|
| Controle convencional | Escolher meta articular; registrar estados e tempo | Alcançar meta e repetir após reset; não confundir estado comandado com medição física |
| Observação / estado | Definir o que estará disponível ao agente em módulo futuro separado | Dimensões/unidades testadas; evitar informação inacessível no hardware |
| Ação | Comparar posição-alvo e velocidade, escolher frequência | Comandos inválidos rejeitados; não misturar unidades |
| Transição e episódio | Implementar pessoalmente reset/step do ambiente futuro | Reset repetível, término distinto de timeout; não carregar estado entre episódios |
| Recompensa / retorno | Propor objetivos e penalidades, discutir conflitos | Casos pequenos ordenados por qualidade; evitar premiar imobilidade ou explorar erro do simulador |
| Política / exploração | Comparar PPO, SAC e TD3 antes de escolher dependências | Explicar restrições e custo de dados; não escolher por popularidade |
| Agente | Implementar pequenas etapas com revisão | Atualização e inferência verificáveis; não usar implementação pronta para pular compreensão |
| Avaliação | Escolher sementes, metas separadas e métricas | Comparar controle convencional, reportar falhas; não selecionar modelo no conjunto final |
| Sim-to-real | Investigar diferenças após física calibrada | Latência, limites e parada validados; não transferir política deste protótipo ao braço |

As etapas futuras não definem recompensa definitiva, algoritmo ou estratégia de
pesquisa. Os módulos de aprendizado e testes serão criados quando você iniciar
cada exercício. Episódio é uma tentativa; transição é um passo entre estados;
política escolhe ações; retorno acumula recompensas; exploração coleta experiências.
Esses conceitos devem primeiro ser ligados ao cenário convencional observado.
