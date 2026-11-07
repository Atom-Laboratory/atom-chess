# Matriz consolidada de lacunas

Fontes E01–E11 em [README](README.md). Prioridades dependem da próxima etapa:
P0 bloqueia operação física, sem alegar que há bancada energizada agora. Nenhuma
ação abaixo foi silenciosamente implementada durante esta auditoria.

| ID | Área | Item/artefato | Estado atual | Evidência | Lacuna | Impacto | Prioridade | Próxima ação | Dependências |
|---|---|---|---|---|---|---|---|---|---|
| G01 | Segurança elétrica | Parada/potência | Documentado, não testado | E03/E04/E06 | Circuito independente e corte não demonstrados | Movimento/energia sem proteção comprovada | P0 antes de energizar | Revisar fiação e ensaio por operador competente | Placas/fontes reais |
| G02 | Firmware | Gate de config | Verificado por inspeção | E04 configurationValid | Não exige limites/E-stop configurados | Habilitação pode não ter entradas de segurança | P0 antes de habilitar | Definir invariantes e testes de rejeição | G01, pinagem |
| G03 | Alimentação | Rails/corrente | Documentado | E03 | Modelo/rating/picos, proteção e bitola ausentes | Reset, aquecimento, dano | P0 antes de carga | Dimensionar/medir por rail | BOM real |
| G04 | Configuração | Revisão do robô | Inconsistente | E01–E04 | 3 juntas simuladas, 4+servo no contrato, 5 drivers diagrama | Modelo/interface errados | P1 | Congelar revisão e lista de eixos | Decisão do responsável |
| G05 | Mecânica | Frames e elos | Desconhecido/parcial | E02/E06/E07 | Centros/zeros/sinais/TCP não extraídos | IK/alcance não confiáveis | P1 | Extrair do CAD e validar poses | Leitura CAD confiável |
| G06 | Garra | Articulação | Documentado parcialmente | E11 | Junta nomeada, frame e vínculo dos dedos faltam | Não permite preensão física simulada | P1 | Mapear junta -45..10° e mecanismo fechado | G05 |
| G07 | BOM | Quantidades/part numbers | Parcial | bom-audit.csv | Ocorrências/estoque/datasheets incompletos | Compra e reprodução inviáveis | P1 | Conciliar BOM CAD e as-built | G04, acesso físico |
| G08 | Firmware | Homing/referência | Não identificado no código | E04 | Estado inicial conhecido não demonstrado | Alvo absoluto pode partir de referência errada | P1 antes de mover | Implementar/testar procedimento em tarefa própria | G01/G05 |
| G09 | Firmware | Watchdog/soft limits | Não identificado | E04 | Perda de link e limites por junta sem contrato | Continuação inesperada do segmento | P1 | Definir fail-safe/testar desconexão | G01/G08 |
| G10 | Build | Exportação ament | Falha reproduzida | E08 | motion exporta dependência fora do export set | Bloqueia build no ambiente ROS | P1 | Correção isolada e testes com/sem ROS | Política de pacotes |
| G11 | Integração | Transport runtime/FSM | Parcial/planejado | E05 | Só fake transport identificado; sem coordenador completo | Jogo não executa pipeline completo | P1 para integração | Mapear executáveis e implementar interfaces faltantes | G10/G08, calibração |
| G12 | Simulação | Todos os eixos/contatos | Parcial | E07 | J3, garra, corpos dinâmicos e collision faltam | Não treinar/validar pick-place | P1 para preensão | Modelo compartilhado e ensaios MuJoCo/Gazebo | G05/G06, inércias |
| G13 | Teste | Stockfish real | Não executado | E08 | Binário ausente, teste não registrado | Aprovação de UCI incompleta | P1 para jogo | Provisionar dependência e executar teste | Ambiente Linux |
| G14 | Documentação | Requisitos físicos | Desconhecido | E06 e matriz R | Metas de precisão/carga/custo/velocidade não fechadas | Reprojeto sem critério | P1 para CAD próprio | Definir critérios e casos de uso | Responsável |
| G15 | Mecânica | Fabricação/ajustes | Parcial | E02 | Material, tolerâncias, encaixes e processo insuficientes | Peças podem não montar/funcionar | P1 para fabricar | Desenhos/primeira peça/inspeção | G07/G14 |
| G16 | Elétrica | Pinagem/chicote | Desconhecido | E04 GPIO -1 | Conector/nível lógico/retorno não fechados | Ligação não reproduzível | P1 | Esquema de conexão e inspeção sem energia | G07 |
| G17 | Firmware | Parser e cancelamento | Inferido risco por inspeção | SW3/SW4 | Overflow/sinal/tokens extras/DONE em cancel não cobertos aqui | Protocolo ambíguo ou inválido | P1 antes de integrar | Harness e especificação de respostas | Build firmware |
| G18 | Visão | Borda externa/URL | Defeitos por inspeção | SW7/SW8 | Escala de extrapolação e std::get<int> | Erro geométrico/crash em falha de URL | P2 agora; P1 para visão integrada | Testes específicos e correção pequena | Dataset/cenário definido |
| G19 | ROS | RViz e nomes action | Inconsistente | E07/SW9 | Erro TF visual; main action/YAML divergentes | Dificulta diagnóstico/controlador | P2 | Reproduzir isolado e alinhar nomes | Modelo/pacotes selecionados |
| G20 | Repositório | Caixa/gerados/presets | Verificado | E01 | Hardware/hardware duplicados; install/log; JSON legado inválido | Reproduções/merges confusos | P2 | Limpeza revisada em ambiente case-sensitive | Backups/baseline |
| G21 | Ambientes | Docker/OS/versões | Inconsistente | E07/E09 | Humble/Lyrical, Dockerfile raiz ausente, senha VNC exemplo | Guia não reproduzível por esse caminho | P2 | Definir fluxos suportados e validar containers | Escolha de runtime |
| G22 | Pesquisa | Dados/métodos | Parcial | E09/E10 | Benchmark sem pacote bruto/protocolo completo | Conclusões não reproduzíveis | P2 | Registrar/extrair experimentos com dados e limites | Acesso a dados originais |
| G23 | Aquisição | Custos e estoque | Desconhecido | E02/E06 | Quantidade disponível e notas não encontradas | Não estimar compras/custo total | P2 | Inventário físico e preços comprovados | Responsável |
| G24 | Manutenção | Procedimento | Não localizado completo | E02/E06 | Inspeção, desgaste e reposição não definidos | Falhas recorrentes e perda de referência | P2 | Plano após identificar componentes | G07, dados de uso |
| G25 | Qualidade | CI/cobertura e firmware | Configurado/não executado | E08 | CI remoto/cobertura/harness não auditados | Limites da confiança em regressão | P2 | Build firmware e análise/coverage em tarefa própria | Toolchain/dependências |
| G26 | RL | Pesquisa de política | Planejado | E07/E10 | Tarefa/observações/reward/avaliação do usuário ainda por formular | Treino sem pergunta científica | P2 para controle; P1 para iniciar treino | Exercícios e proposta revisada | G14; G12 para preensão |
| G27 | Produto | Otimização/redesenho | Futuro | Objetivo do responsável | Geometria própria sem requisitos fechados | Retrabalho | P3 | Otimizar depois da baseline e critérios | G04/G14/G15 |

Pontos mais urgentes não são sinônimo de mais linhas de código. G01–G03 são
gates físicos; G04/G05/G06/G07 fecham o objeto do projeto; G10 pode ser resolvido
imediatamente sem depender do hardware. Isso define uma sequência executável.
