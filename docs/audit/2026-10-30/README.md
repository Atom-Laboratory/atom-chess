# Auditoria geral de engenharia do ATOM — 30/10/2026

## A — Resumo executivo

O ATOM possui bibliotecas de visão/xadrez/movimento, firmware de referência,
diagramas de arquitetura, CAD de referência e um protótipo de simulação. **Não
há evidência suficiente para certificar uma revisão física reproduzível,
fabricável e apta a manipulação autônoma.** Não é necessário reescrever tudo:
os módulos já testados são ativos úteis; integração, calibração e documentação
de fabricação precisam fechar suas interfaces.

Estado verificável nesta auditoria:

- Branch atual ros2_simulation, base 0b138450738a12118ca9c32230327be24c644e52:
  build C++ e 3 suítes CTest passaram; ROS build/launch e 13 casos pytest em
  quatro suítes passaram; MuJoCo 13 casos, incluindo render, passaram.
- main local/remota f72c89398f782367b0cc7663804fef8ca53752ae: build CMake com
  ament disponível falhou na exportação de motion→acchess. Configuração isolada
  sem ament compilou e passou 15 suítes. Stockfish ausente: teste UCI não foi
  registrado, portanto não foi aprovado. CI configurado não prova CI verde.
- Gazebo 10.4.0 executou anteriormente shapes.sdf por 20 iterações. Não existe
  modelo completo do ATOM validado no Gazebo. MuJoCo contém braço vertical,
  garra e 32 peças visuais fixas; gravidade/contatos desativados e inércias
  sintéticas. Não valida preensão, colisões, precisão real ou carga útil.
- Firmware em main está configurado para rejeitar movimento até calibração;
  não foi compilado nesta auditoria (PlatformIO ausente), gravado ou testado
  em bancada. E-stop/homing/telemetria reais não foram comprovados.
- Há F3D, STEP e SolidWorks externos, mas equivalência de revisões, materiais,
  BOM de ocorrência, tolerâncias e registros de fabricação não estão fechados.

Riscos principais: alimentação e parada independente não demonstradas; divergência
de graus de liberdade; perda de referência/perda de passos; preensão não modelada;
geometria e limites ainda sem correspondência completa ao CAD. A prioridade
imediata é fechar a configuração de referência e sua rastreabilidade, sem
habilitar motores por preencher constantes com valores de exemplo.

### Escopo, critérios e limites

Esta auditoria confronta código, configuração, documentos, testes, metadados CAD,
nomes de peças, desenhos e fontes externas acessíveis. Não substitui ensaio do
hardware nem certificação. Não foi possível inspecionar todo o modelo nativo
no Fusion: falhas de captura impediram leitura confiável; capturas de juntas
fornecidas pelo responsável foram usadas com identificação parcial explícita.
Não foram testados todos os caminhos de erro, regras de xadrez ou desempenho.

Classificações: **Verificado** = teste executado ou conteúdo diretamente observado
(limitado à afirmação); **Documentado** = declarado em fonte; **Inferido** =
dedução parcial; **Desconhecido** = não localizado/medido no escopo; **Inconsistente**
= fontes conflitantes; **Não aplicável** = sem função no estágio, com justificativa.
Presença de arquivo é verificação de existência, não de funcionamento.

Nível de inspeção: inventário de caminhos completo para os snapshots; conteúdo
de código/documentos selecionado por responsabilidade e risco, mais execução
das suítes disponíveis. Não houve revisão formal de cada linha de todos os
commits, engenharia reversa de todos os sólidos nativos, inspeção integral de
todas as imagens/dados de teste ou execução de cada caminho de software.
PDFs de arquitetura foram extraídos para leitura; o desenho de base e o diagrama
elétrico tiveram inspeção visual. Esses limites restringem o significado de
“não encontrado” ao escopo examinado, não a todo conhecimento histórico do projeto.

## B — Inventário técnico e rastreabilidade

[inventory.csv](inventory.csv) lista cada entrada versionada de HEAD e main com
path, tamanho, extensão e blob Git, mais arquivos CAD externos. Snapshot antes
dos documentos desta auditoria: 224 entradas HEAD, 494 main, 79 externas. Não
somar como peças físicas: há duplicatas por branch, caminhos com caixa diferente,
malhas instaladas/copias e arquivos gerados. Contagem externa exclui .git; arquivos
dentro dos ZIP não viram arquivos independentes no inventário de filesystem.

### Registro de evidências

| ID | Localização e revisão | O que foi efetivamente examinado |
|---|---|---|
| E01 | main f72c893 e HEAD 0b13845; git ls-tree/log/status/ls-remote | Estrutura versionada, histórico recente, remotos e diferença de módulos |
| E02 | F:\Users\EHD\Github\er\3DSCARAROBOT | F3D, inventário de STEP/SLDPRT/SLDASM/ZIP; nomes das 59 peças CAD; PDF de base renderizado; cabeçalho STEP e arquivo F3D já registrados |
| E03 | main: hardware/Architechture/Eletronic/v0.0/v0.0 eletronic diagram.{svg,png}; DistributedSystem/v0/v0.4 e v0.5 PDFs | Texto extraído, diagrama elétrico PNG inspecionado; PDFs de arquitetura lidos como declarações funcionais |
| E04 | main: firmware/esp32-s3-motion/{src/main.cpp,include/robot_config.hpp,platformio.ini,README.md} | Configuração, parser, cancelamento, execução e entradas de segurança por inspeção |
| E05 | main: software/acvision, acchess, acmotion, integration; HEAD: Software/acvision | Fontes, headers, CMake, testes e principais fronteiras de responsabilidade |
| E06 | main: software/acmotion/docs/{dejan-scara-bringup,physical-integration-runbook,physical-calibration-template}.md | Sequência de bring-up, configuração proposta, campos TBD e critérios físicos sem resultados preenchidos |
| E07 | HEAD: simulation/src, simulation/mujoco, simulation/docs | Modelo de 3 juntas, controle, manifest/perfil, testes, peças/garra visuais e guias |
| E08 | .github/workflows/ci.yml em main; logs desta auditoria em validation.md | Build/testes executados localmente; workflow somente inspecionado |
| E09 | hardware/Plataforms/Banana Pi M5/{specs.txt,Benchmarks/BPIM5/1/doc.md} | Log histórico de OS e relatório de desempenho; ausência de protocolo/dados completos para reproduzir conclusões |
| E10 | work/rl-runs/sac-seed7 e sac-seed7-resumed fora do repositório; simulation/learning não versionado | manifests, modelos, monitor e training_result.json de experimentos anteriores, não reexecutados |
| E11 | docs/mechanics/gripper-cad-evidence.md e três PNG associados | Junta da garra revoluta Z local, mínimo -45°, máximo +10°, Rest desabilitado; nome/frame pendentes |

Para ler conteúdo de main sem trocar branch: `git show main:software/acmotion/README.md`.
Os relatórios citam paths Git, não o snapshot temporário como fonte permanente.
O arquivo não versionado simulation/learning foi preservado e não integra os
resultados do backend MuJoCo nem os commits desta auditoria.

### Fontes externas e acessibilidade

[Tutorial How To Mechatronics](https://howtomechatronics.com/projects/scara-robot-how-to-build-your-own-arduino-based-robot/)
acessível: referência de projeto com quatro motores e servo, fabricação e montagem.
É referência externa, não confirmação de componentes instalados no ATOM. Não
foi validada equivalência entre todos os downloads e o F3D selecionado.
[Lista pública de issues](https://github.com/Atom-Laboratory/atom-chess/issues)
acessível como listagem: inclui integração/FSM e dívida de artefatos. Não foi
audicionado o histórico completo de cada issue/comentário ou CI remoto. A
listagem pode estar desatualizada em relação ao código: #138 aparece na listagem
consultada enquanto main tem commit de limpeza, logo status de issue não prova
ausência de implementação. Vídeo de onboarding YouTube 9TsCbVWJvaY não pôde ser
obtido (throttling); não analisado. Links de compra não são registros de aquisição.

## C — Análise de completude por subsistema

Critério usado: existência identificada → especificação suficiente → teste de
componente → teste integrado → validação física/reprodução. Sem nota numérica:
o nível só é afirmado onde há evidência, e não é média entre áreas.

| Área | Maturidade demonstrada | Lacuna que impede avanço |
|---|---|---|
| Mecânica | Artefatos CAD/mesh identificados e um limite de garra documentado | Revisão, eixos, acoplamentos, tolerâncias e TCP sem fechamento |
| BOM/aquisição | Componentes candidatos identificados por documentos/CAD | Quantidades de ocorrência, estoque, part numbers e custos não conciliados |
| Eletrônica | Diagrama de blocos e arquitetura de alimentação documentados | Esquema de conexão, 4 vs 5 drivers, dimensionamento e ensaio ausentes |
| Firmware | Implementação de referência inspecionada | Build e testes de bancada não executados; config vazia e riscos por inspeção |
| Software | Componentes headless de main compilados/testados | Aplicação coordenadora e transporte físico não demonstrados; UCI não testado nesta máquina |
| ROS 2 | Launch e estados/TF testados na branch atual | RViz apresentou erro de TF na sessão visual; integração completa/ament main falha |
| Simulação | Backend MuJoCo e render testados | Modelo incompleto e sintético, sem contatos; Gazebo só mundo exemplo |
| Fabricação/montagem | STEP, malhas e molde de base existentes | Desenhos de cada peça, material, tolerância, processo e inspeção sem conjunto completo |
| Testes/validação | Suites locais e cenários convencionais reproduzíveis | Sem matriz física preenchida, cobertura medida ou carga/precisão/repetibilidade reais |
| Documentação | Guias recentes e ADRs por módulo | Revisões divergentes, estrutura histórica duplicada, documentos de requisitos incompletos |
| Pesquisa | Logs de protótipos e relatório de benchmark localizados | Falta protocolo consistente, dados originais completos e validação independente |

Detalhes: [mecânica/CAD/fabricação](mechanical-cad.md), [BOM/elétrica/segurança](bom-electrical.md),
[firmware/software/simulação](software-simulation.md), [testes/requisitos](validation.md).

## D — Matriz geral de lacunas

[gaps.md](gaps.md) consolida ID, área, estado, evidência, lacuna, impacto,
prioridade, ação e dependência. P0 é **condição para operação física**, não afirma
de perigo atualmente energizado. P1 bloqueia a próxima integração; P2 é dívida
ou melhoria de reprodução; P3 fica depois da base validada. Não há orçamento ou
prazo fictício: cada entrega tem critério de conclusão.

## E — Plano para CAD próprio

O projeto tem referências suficientes para iniciar levantamento e modelagem
assistida, mas não para prometer reconstrução fabricável validada. Plano detalhado
e dados a medir/calcular/decidir em [mechanical-cad.md](mechanical-cad.md). Preservar
o CAD de referência; não redesenhar nesta auditoria. Escolha inicial de menor
fricção é investigar Fusion já instalado para F3D, mas portabilidade/licença e
acesso aos SolidWorks precisam entrar na decisão de ferramenta de CAD próprio.

## F — Plano de ação priorizado

| Etapa | Objetivo/tarefas | Dependências | Entregável e aceite | Testes/documentação |
|---|---|---|---|---|
| F1, imediata | Congelar revisão física pretendida e conciliar componentes | Escolha do responsável e acesso ao CAD | Mapa de revisões e BOM por ocorrência com conflitos explicitados | Conferência CAD↔inventário; preencher fontes da BOM |
| F2, imediata em software | Reproduzir/corrigir exportação ament em tarefa isolada; preservar core | E08 e decisão de integração de branches | CMake com/sem ROS gera, compila e testa sem exportação inválida | Testes existentes + teste de configuração; ADR se fronteira mudar |
| F3, antes de energizar | Dimensionar alimentação, definir pinagem/proteção/parada | F1, modelos reais de motores/drivers/fontes | Esquema de alimentação e conexão revisado; valores de calibração documentados | Ensaios sem potência e elétricos por responsável competente; registro de bancada |
| F4, mecânica | Extrair juntas/frame/garra e construir BOM comercial/fabricada | F1; capacidade de ler CAD nativo | Tabela pai/filho/eixo/zero/limite/unidade/fonte, conferência em posições conhecidas | FK, comparação da montagem e revisão das cotas críticas |
| F5, firmware | Validar configuração, homing, cancelamento, watchdog/estado de posição e testes | F3/F4 | Build reproduzível e rejeições demonstradas; sem defaults virarem calibração | Harness de parser, limites, perda de comunicação, E-stop; relatório físico separado |
| F6, simulação | Modelo compartilhado J1/J2/J3/Z/garra e peças com contatos | F4 e dinâmica com fonte ou hipóteses acordadas | MuJoCo/Gazebo movem cada eixo e garra; preensão/soltura reproduzíveis | Reset, contatos, quedas, estabilidade, feedback; atualizar guias |
| F7, CAD próprio | Modelar interfaces/peças, desenhos e pacote de fabricação | F1/F4, requisitos físicos e processo | Montagem paramétrica, BOM associada, interferências e desenhos revisados | Inspeção de primeira peça, medição de montagem; plano CAD detalhado |
| F8, integração | Transportar segmentos, coordenar jogo e reconciliar branches | F2/F5/F6 | Fluxo observado de visão validada até resposta física e confirmação | Timeout, cancelamento, erro de visão, peça caída e recuperação |
| F9, pesquisa RL | Responsável define tarefa/ambiente/agente e avalia benefício | Exercícios atuais podem começar; preensão exige F6 | Protocolo, baseline, sementes, metas independentes, versão do modelo | Avaliar erro/falhas/latência; política não bypassa validações |

F2 e coleta documental/medição de F1/F4 podem avançar em paralelo, sem alterar o
robô. A automação pode inventariar/extrair código e artefatos; medições físicas,
estoque e escolha de revisão dependem de quem tem o protótipo. Não registrar
hipóteses como respostas. Esta entrega não implementa correções de runtime.

## G — Decisões e informações do responsável

| Prioridade | Informação/decisão | Por que é necessária |
|---|---|---|
| Antes de operar | Existe protótipo montado/energizado? Onde e quem o opera? | Definir quais riscos/ensaios são atuais; auditoria local não vê a bancada |
| Antes de operar | Fotos legíveis da ligação e etiquetas de fonte, drivers, motores, placas e servo; estado da parada | Conciliar diagrama e componente real, sem supor ratings ou pinagem |
| P1 | Confirmar revisão a fabricar/evoluir e se Arm_Assembly é parte/revisão do F3D oficial | Rastrear os limites de garra e evitar misturar montagens |
| P1 | Confirmar estoque/quantidades e notas de compra acessíveis | Separar identificado, disponível e a adquirir; não criar pedido de compra fictício |
| P1 | Definir escopo físico inicial e número de eixos, reconciliando diagrama 5 e contrato 4+servo | Fechar interfaces elétrica/mecânica/firmware |
| P1 | Quem pode medir bancada, ferramentas disponíveis e processo de fabricação pretendido? | Determinar metrologia, tolerâncias e testes realizáveis |
| P1 | Quais metas de carga, alcance, precisão, repetibilidade, tempo por tarefa e custo são requisitos? | Selecionar projeto e critérios; não escolher números arbitrários |
| P2 | Ferramenta/licença e política de compartilhamento para CAD próprio | Evitar fonte editável inacessível aos demais desenvolvedores |
| P2 | Dados brutos de benchmarks, ensaios e experimentos anteriores | Reproduzir conclusões e não confundir resultado narrativo com dado |

O responsável já orientou que a extração de eixos/limites seja feita do CAD:
isso é trabalho técnico pendente da automação/engenharia, não uma solicitação
para ele preencher novamente todos os frames. Só medições/decisões não contidas
no modelo precisam de informação humana. Informações desconhecidas da BOM não
significam obrigatoriamente componentes faltando fisicamente.
