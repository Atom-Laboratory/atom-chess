# Requisitos, testes, cobertura documental e reprodução

Fontes e hashes no [relatório geral](README.md). Resultados desta rodada:

| Execução | Resultado | Limite da evidência |
|---|---|---|
| Atual: CMake raiz/build + CTest | 3 suítes passaram | Visão sintética; não câmera/precisão real |
| main com setup ROS Lyrical | Geração falhou em export_motion→acchess | Não compilou nesse modo; não marcar aprovado |
| main headless sem ament | Build e 15 suítes passaram | Stockfish não instalado, teste UCI não registrado; sem viewer/câmera |
| Atual: colcon build/test | 4 suítes, 13 casos pytest passaram | Colcon reporta 17 somando wrappers; não são 17 cenários independentes |
| Atual: pytest MuJoCo com ATOM_TEST_RENDER=1 | 13 casos passaram | Física experimental, render, reset, limites e cena; não preensão |
| Firmware | Não executado | PlatformIO não encontrado; sem flash/hardware |
| Gazebo | Teste anterior do servidor shapes, 20 iterações/código 0 | Nenhum teste do ATOM completo; não repetido por não haver mudança dependente |
| Hardware físico | Nenhum ensaio executado | Sem aprovação elétrica/mecânica/movimento |

Os logs relevantes da rodada estão em [evidence](evidence/). A existência de CI,
fixtures ou logs de build históricos não altera esses resultados. Cobertura de
linhas, static analysis e execução de CI remoto não foram medidos nesta rodada.

## Como reproduzir os testes

Branch atual, no Ubuntu/WSL com dependências instaladas, a partir da raiz:

```bash
source /opt/ros/lyrical/setup.bash
cmake -S . -B "$HOME/atom-audit-cpp" -DACVISION_BUILD_HARDWARE_TESTS=OFF
cmake --build "$HOME/atom-audit-cpp" --parallel 4
ctest --test-dir "$HOME/atom-audit-cpp" --output-on-failure
```

Para main **sem trocar o checkout**, criar diretório novo externo e extrair
`git archive main` nele. A extração no Linux preservou links; tar Windows não
conseguiu criar alguns links históricos, portanto não foi usada no build.

```bash
# Após extrair main em /caminho/novo/atom-main:
cmake -S /caminho/novo/atom-main -B "$HOME/atom-audit-main" \
  -DACCHESS_BUILD_VIEWER=OFF -DACVISION_BUILD_HARDWARE_TESTS=OFF \
  -DCMAKE_DISABLE_FIND_PACKAGE_ament_cmake=ON
cmake --build "$HOME/atom-audit-main" --parallel 4
ctest --test-dir "$HOME/atom-audit-main" --output-on-failure
```

O parâmetro ament é um contorno diagnóstico executado, não correção do defeito.
Para reproduzir a falha, use outro build com ROS carregado e sem esse parâmetro.
GTest instalado foi usado; aquisição via rede pode ocorrer se ele faltar.
ROS: procedimento em simulation/README.md; foram usados build/install externos.
MuJoCo, no PowerShell da raiz, com `.venv` instalada:

```powershell
$env:ATOM_TEST_RENDER = '1'
& ./simulation/mujoco/.venv/Scripts/python.exe -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
```

## Matriz requisito → subsistema → verificação → resultado → pendência

As descrições abaixo são candidatos de requisito/capacidade, não especificação
numérica aprovada. Metas físicas devem ser estabelecidas pelo responsável.

| ID | Requisito/capacidade | Subsistema | Método | Resultado disponível | Pendência |
|---|---|---|---|---|---|
| R01 | Capturar e identificar tabuleiro | Visão | Câmera real + dataset rotulado | Suítes sintéticas; captura real não validada | Meta de detecção, luz/oclusão/latência |
| R02 | Manter estado legal e consultar engine | Xadrez | Unitários + UCI real + partidas | Componentes main passaram; UCI não rodou | Binário/teste UCI e coordenação de partida |
| R03 | Planejar transferência | acmotion | Casos de tarefas e waypoints | Unitários passaram | Calibração, colisão e confirmação real |
| R04 | Comandos e feedback de simulação | ROS/MuJoCo | Launch DDS/FK/render/reset | Aprovados no perfil atual | Modelo com todos os eixos/garra |
| R05 | Precisão de posição | Mecânica/controle | Comparação metrológica TCP↔alvo | Desconhecido | Meta, instrumento, amostras e incerteza |
| R06 | Repetibilidade | Mecânica/controle | Repetir alvos em condições definidas | Só replay simulado repetível | Ensaio físico e estatística |
| R07 | Velocidade/tempo por tarefa | Controle | Trajetória temporal medida | Constantes de software; não desempenho real | Meta e medições sob carga |
| R08 | Carga útil/alcance | Mecânica | Cálculo + ensaio/envelope | Desconhecido no hardware | Requisitos, CAD e fatores de projeto |
| R09 | Consumo e térmica | Elétrica | Corrente/temperatura/pico por rail | Diagrama declarativo | Medir e dimensionar |
| R10 | Parada e limites | Elétrica/firmware | Injeção de falhas e parada independente | Código/diagrama, sem ensaio | Validar configuração, circuito e resposta |
| R11 | Perda de comunicação/recuperação | Firmware/host | Desconexão, timeout e retomada | Host unitário, firmware inspecionado | Watchdog, home e critério de retomada |
| R12 | Pegar e colocar peças | Garra/simulação | Levantar/manter/transportar/soltar | Não realizado | Articulação, contatos e teste físico |
| R13 | Fabricação reproduzível | CAD/BOM | Fabricar por documentação e inspecionar | Referências parciais | Desenhos, BOM e processo |
| R14 | Manutenção e confiabilidade | Sistema | Ciclos/inspeção/trocas/falhas | Não encontrado protocolo preenchido | Metas, duração, falhas e periodicidade |
| R15 | Custo de reprodução | BOM | Notas e cotação datada | Desconhecido | Inventário, compras e processo |
| R16 | Reprodutibilidade experimental | Pesquisa | Reexecutar com dados/configuração | Testes atuais sim; benchmark antigo parcial | Datasets, versões, hashes e protocolo |

## Avaliação individual dos artefatos necessários

Não criar documentos vazios: agrupar os relacionados onde isso melhora uso.

| Artefato | Estado observado | Necessidade e destino recomendado |
|---|---|---|
| Requisitos do sistema | Objetivos dispersos; sem baseline de metas físicas | Necessário antes de reprojeto; documento curto com R05–R15 aprovados |
| Especificação técnica | Parcial e divergente | Uma especificação por revisão física; distinguir medido/proposto |
| Arquitetura geral | Diagramas e docs existentes | Manter; reconciliar main e branch de simulação |
| BOM principal | Não localizada como lista liberada | Necessária; derivar de BOMs por subsistema/ocorrência |
| BOMs de subsistema | Menções dispersas, CSV de auditoria agora | Transformar grupos candidatos em itens especificados |
| Inventário de hardware | Não confirmado | Necessário para saber o que adquirir |
| Esquema elétrico | Diagrama de blocos existe; esquema de conexão não fechado | Necessário antes de operação física |
| Diagrama de alimentação | Existe E03 | Revisar rails/correntes/proteções para revisão real |
| Pinagem/conexões | GPIO -1 no firmware | Necessária, ligada ao chicote e placa real |
| Motores/drivers | Classes/modelos propostos | Datasheets de part numbers/carriers reais necessários |
| Desenhos mecânicos | Molde de base isolado | Necessários para peças fabricadas e tolerâncias funcionais |
| CAD editável | F3D/SLDPRT/SLDASM existem | Extrair revisão/interfaces; não redesenhar agora |
| Arquivos de fabricação | Malhas/STEP/3MF parciais | Release ligado a processo/revisão; G-code não obrigatório se fabricação não usa CNC/impressão específica |
| Montagem | Tutorial externo/runbook geral | Sequência ATOM com fixadores, inspeção e desvios necessária |
| Modelo cinemático | IK main e URDF protótipo | Reconciliar e validar com CAD |
| Coordenadas/juntas | Defaults e template TBD | Tabela rastreável com ferramenta/TCP necessária |
| URDF/Xacro | Existe e carrega | Completar mecânica/dinâmica/colisão com fonte |
| Configuração ROS 2 | Existente; atual testada | Completar integração/controladores; corrigir export main |
| Configuração de simulação | MuJoCo versionado; Gazebo parcial | Perfil atual declarado; modelo físico completo pendente |
| Plano de testes | Testes/roteiros distribuídos | Matriz R01–R16 com resultados ligados à revisão |
| Relatórios de validação | Simulação recente e benchmark narrativo | Preservar logs/resultados; não converter em aprovação de hardware |
| Calibração | Template detalhado, sem preenchimento | Registro por robô/revisão com medições |
| Análise de riscos | Alertas e riscos nesta auditoria | Transformar gates físicos em procedimento revisado |
| Plano de manutenção | Não localizado completo | Definir quando componentes/processo estiverem identificados |
| ADRs | Vários existentes | Manter por módulo e vincular mudanças reais |
| Alterações de engenharia | Commits; sem release mecânico uniforme | Manifesto de revisão CAD/BOM/chicote/firmware |
| Roadmap | Existente e evoluído | Priorizar dependências da engenharia física desta auditoria |
| Reprodução do ambiente | Guias recentes e CI main | Corrigir incompatibilidades; manter versões/sistemas distintos |
| Histórico de experimentos | Logs locais e relatório parcial | Registro com hipótese/método/dados/limitações por experimento |

Documentos adicionais só devem nascer quando uma tarefa produz informação nova.
Requisitos de certificação formal de produto são não aplicáveis como conclusão
desta auditoria de protótipo: não foi solicitado nem realizado processo de certificação.
