# Roadmap verificável

Situação em 30/10/2026: entregas 1 e 2 executadas, com testes C++/ROS e CLI
aprovados. A etapa 3 permanece pendente: inicialização do RViz foi observada em
logs, mas montagem não inspecionada visualmente nem calibrada contra o F3D.
Etapas dependentes de fidelidade física não foram iniciadas.

| Ordem | Entrega | Dependência e critério de conclusão |
|---|---|---|
| 1 | Auditoria e guias por módulo | Build C++, testes ROS, inventário de lacunas e comandos reproduzíveis; registrar limitações visuais e físicas |
| 2 | Controle convencional ROS | URDF carregável; comando válido produz evolução de estado e TF, comando inválido rejeitado, reset testado, fonte única de estados |
| 3 | Conferência visual/mecânica | Inspecionar RViz e montagem F3D; registrar eixos, zeros, unidades, frames de malhas, TCP e limites com fonte |
| 4 | Backend físico principal | Etapa 3, massas/inércias/colisões ou aproximações acordadas; Gazebo carrega modelo e responde a controle com testes de estabilidade |
| 5 | Primeira etapa pessoal de RL | Controle convencional validado; responsável define tarefa, observa estados, implementa ambiente mínimo e testes; sem treinamento automático |
| 6 | Integração de xadrez | Reconciliação de branches, estado legal, UCI testado, calibração tabuleiro→robô e planejamento de tarefas |
| 7 | Peças e hardware | Colisões, garra, TCP, parada, homing e limites validados; só então pick/place e sim-to-real |

Riscos: modelo cinemático não representa ferramenta; teste sintético de visão não
mede qualidade com câmera; caminhos com caixa duplicada dificultam merges;
artefatos instalados antigos podem mascarar o pacote novo; RL pode explorar
erros de modelagem. Não usar taxa de sucesso do experimento anterior para aprovar
nenhum desses critérios. Cobertura de linhas não foi medida.

Pendências de manutenção separadas: extrapolação de cantos, erro de captura URL,
presets CMake com comentários e vírgula final, Compose com Dockerfile ausente,
duplicação de caminhos e artefatos versionados. Corrigir cada problema com teste
ou validação específica, sem misturá-los com a infraestrutura ROS.
