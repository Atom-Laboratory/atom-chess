# Firmware, software, ROS, simulação e pesquisa

Fontes E04–E10 do [relatório geral](README.md). Não houve mudança de runtime.

## Arquitetura implementada por revisão

| Área | Branch atual 0b13845 | main f72c893 |
|---|---|---|
| Visão | Camera, BoardDetector, PieceDetector, FEN simplificada; demos | BoardObservation, BoardVision/homografia, ocupação/cor e testes geométricos |
| Xadrez | Não integrado | Board, comparação, validação/aplicação de movimentos, FEN e cliente UCI POSIX |
| Movimento | Servo cinemático ROS e backend MuJoCo independentes | CoordinateMapper, graveyard, TaskPlanner, MotionPlanner, IK J1/J2/J3/Z, ACM1/MotionExecution |
| Integração | Sem visão→jogo→robô completo | ObservationInterpreter e testes de observação; não coordenador de partida executável demonstrado |
| Firmware | Não versionado nesta branch | Referência Arduino/ESP32-S3 com Serial/AccelStepper/ESP32Servo |
| ROS | Um pacote atom_description testado | atom_description raiz e subpacote duplicados; atom_control com exemplo de action e nomes TODO |

Main mantém fronteiras úteis: visão estima observação, xadrez mantém estado,
planejamento produz tarefas/poses e execução manda segmentos. Não foi encontrada
dependência circular demonstrada no núcleo; há acoplamento motion→acchess que
requer exportação correta no modo ament. TaskPlanner não deve ir para firmware;
stockfish/FEN não pertencem ao servo. Não há justificativa para reescrever tudo.

O cliente UCI em main usa pipes POSIX e rejeita init no Windows por código;
execução nativa Windows não é caminho equivalente. Teste real de Stockfish não
rodou sem binário. IMotionTransport só tem implementação falsa identificada nos
testes; serial_monitor.py é diagnóstico, não prova transporte runtime integrado.
Não confundir teste com fake com entrega de movimento físico.

## Problemas de código por inspeção (não corrigidos)

| ID | Evidência | Conclusão e próxima verificação |
|---|---|---|
| SW1 | main firmware configurationValid() | Não exige GPIOs de limites/emergência; pinos negativos retornam false em inputActive(). configured=true pode passar sem entradas; testar gate de configuração antes de habilitar potência |
| SW2 | main executeSegment() e setup() | Sem homing/setCurrentPosition demonstrado, sem limites de software por junta, sem telemetria medida; origem após boot não é posição física conhecida |
| SW3 | main cancellationRequested()/executeSegment() | CANCEL durante movimento gera DONE; host pode não distinguir cancelamento de conclusão se não coordenado. Testar semântica e invariantes por sequência |
| SW4 | main parseUnsigned() usa strtoul; splitFields() interrompe no limite | Sinal/overflow e tokens extras precisam de teste específico; não afirmar parser host garante validação firmware |
| SW5 | main executeSegment(): min(distância/tempo,maxSpeed) com aceleração por eixo | durationMs não garante término sincronizado; medir/definir tolerância e limites; execução é bloqueante |
| SW6 | main: não há watchdog/homing/enable de driver identificados | Perda de comunicação/energização requer projeto e teste; timeout do host não assegura parada física |
| SW7 | Camera::capture_frame(), ambas revisões | std::get<int>(m_source) em erro pode lançar para fonte URL; teste de falha de stream necessário |
| SW8 | BoardDetector | Extrapolação interna usa 0.5 na branch atual e 0.8 em main; não extrapola um passo de grade para a borda externa. Testes de geometria aprovados não eliminam esse caso de precisão |
| SW9 | main atom_control/src/scara_commander.cpp e controllers.yaml | Código de exemplo usa quatro nomes shoulder/elbow/z/wrist; YAML lista três juntas reais do protótipo. Não demonstrado como action funcional |

Flags de segurança e software cancel não substituem corte de energia apropriado.
Esses achados são inspeção estática; não se testou falha em motor energizado.

## ROS e simulação

No protótipo atual o comando valida posições e um servo publica estados/TF.
Testes DDS reais comprovaram transporte e movimento numérico. A sessão RViz do
usuário mostrou “No transform ... to world”, apesar de tf2_echo externo funcionar;
erro visual não foi resolvido/comprovado como corrigido. Portanto “janela abriu”
e “viewer físico fiel” continuam afirmações diferentes.

MuJoCo usa URDF como entrada, aplica Y→Z à montagem e inércias/ganhos sintéticos,
sem gravidade/contatos. Três meshes de garra são rígidos no braço; 32 peças são
corpos fixos. Não há abrir/fechar, TCP calibrado, sensor/contato de preensão,
quarto eixo, física de peças, bridge ROS ou adaptador de acmotion. Os 13 testes
atestam esse perfil, não o mecanismo final. Limites -45°..+10° da captura não
foram atribuídos arbitrariamente a um link.

Gazebo está instalado e mundo exemplo executou; modelo completo bloqueado pela
extração mecânica. ROS Lyrical/Ubuntu26.04 WSL do desktop é diferente do registro
histórico Armbian/Ubuntu24.04 da SBC. Instrução Docker Humble e devcontainer
Lyrical não formam ambiente único validado. Compose aponta Dockerfile ausente
na raiz e tem senha VNC de exemplo; instalação antiga não deve ser fonte do URDF.

## Pesquisa e reprodutibilidade

E09 é um relatório de performance do Banana Pi que declara ~90–100% de sucesso
funcional e cita remap ~182 ms. Isso não comprova taxa de reconhecimento de peças
do ATOM. Não localizados dados brutos completos, comando/suite/semente/configuração
e hash de OpenCV suficientes para reproduzir as conclusões. Log de OS é útil,
mas não caracteriza câmera, carga, temperatura e método do benchmark.

E10 existe fora do Git: treino protótipo anterior reporta 50.000 passos/302,25 s
e retomada até 150.000/653,22 s no arquivo training_result.json. Arquivos foram
inspecionados, não foi reexecutado treinamento. Não considerar tempos como
benchmark independente ou taxa de sucesso física. A nova orientação do usuário
reserva RL a ele; não foi feito treinamento nesta auditoria. O modelo cinemático
anterior e o MuJoCo atual não têm o mesmo contrato físico.

Para novos experimentos: hipótese/tarefa e baseline, versão de código/modelo,
parâmetros, dados brutos, sementes, métricas/unidades, validação separada, falhas,
limitações e conclusão proporcional. Registrar hardware/câmera/luz e latência
para visão; perfil e contatos para simulação; calibração para hardware. Precisão,
repetibilidade, carga, consumo e tempo por lance ainda não têm metas/medidas reais
fechadas nesta auditoria.
