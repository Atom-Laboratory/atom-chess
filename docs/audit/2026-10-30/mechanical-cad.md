# Mecânica, fabricação e CAD próprio

Fontes E02/E07/E11 definidas no [relatório geral](README.md). Fatos e inferências
abaixo valem para os arquivos examinados; não atestam a montagem física.

## Inventário e capacidade de reconstrução

| Artefato | Local/finalidade | Estado, utilidade e limitação |
|---|---|---|
| SCARA Robot.f3d | Raiz do repositório externo 3DSCARAROBOT; referência selecionada pelo responsável | Verificado existir, 4.048.369 bytes; hash previamente registrado em simulation/docs/mechanical-evidence.md. Potencialmente editável no Fusion, mas árvore paramétrica/juntas não extraídas nesta auditoria |
| SCARA Robot 3D Model.STEP | Base3DProject/.../HowToMechatronics/scara-robot-arm | Geometria de montagem AP214, header original 2021; exportação/revisão não comprovada equivalente ao F3D. Pode apoiar intercâmbio, não preserva necessariamente histórico paramétrico |
| SCARA Robot.SLDASM / Gripper Mechanism.SLDASM | Subpasta SCARA Robot 3D Model - Solidworks Files | Duas montagens e 59 SLDPRT; nomes incluem comerciais e peças próprias. Referências externas, mates e configurações não resolvidos no aplicativo nativo nesta auditoria |
| 11 STEP | Conjunto externo | Arquivos identificados, não 11 componentes necessariamente diferentes; equivalência entre exportações pendente |
| 4 ZIP | Conjunto externo | Distribuições/arquivos compactados de referência; conteúdo não contabilizado como estoque; malhas de impressão previamente identificadas em arquivo de distribuição |
| 7 STL | simulation/src/meshes | Base, coluna, dois braços, fundo da garra e dois dedos. Visualização testada; escala/offsets herdados, não desenhos dimensionados nem parametrização editável |
| Base drawing - for base holes.pdf | Conjunto externo | Uma folha de contorno/furação inspecionada visualmente; carimbo Dejan 2024-08-12, unidade mm. Sem cotas suficientes/material/preenchimento de revisão; não escalar a imagem para fabricar |
| Case/lid 3MF | main: hardware/Project/Banana Pi M5 case | Duas peças de gabinete; não demonstram pacote de fabricação do braço |
| Capturas da garra | docs/mechanics/evidence/gripper-2026-10-30 | Limites -45°..+10° em revoluta Z local. Nome/frames e relação com servo não confirmados |

O nome do diretório de download 20240812, header STEP 2021, carimbo PDF 2024 e
nome genérico F3D não constituem revisão de engenharia comum. É necessário
mapear explicitamente fonte/exportação/alterações. Não localizar G-code/DXF de
braço ou desenhos de cada peça no escopo inventariado não prova que jamais
existiram fora desses repositórios.

## Geometria e cinemática

| Item | Evidência atual | Ainda não confirmado / ação |
|---|---|---|
| Graus de liberdade | main JointTarget: J1/J2/J3/Z + abertura; referência tutorial quatro motores+servo; URDF atual duas revolutas+prismática | Inconsistente entre contrato e simulação; resolver identificação de juntas |
| Eixos/frames | URDF usa Y; MuJoCo aplica Rx(+90°), offset .035 m | São convenções do protótipo; extrair frames locais da montagem e validar sinais |
| Comprimentos | IK main recebe L1/L2 em mm; template continua TBD | Não usar fixtures numéricas de teste como medidas; extrair centros de juntas |
| Garra | Limites visuais de uma junta e três meshes | Extrair motora/passivas, pontos de pivô, elos e slider; geometria pode ser mecanismo fechado, não dois dedos independentes |
| Z/home | Limites de software no URDF e configuração firmware incompleta | Curso mecânico, homing, endstop e conversão steps/mm não medidos |
| Transmissões | Nomes CAD incluem GT2, polias, fuso e porca | Contar dentes/ocorrências, relações e passo real; não usar apenas nomes como calibração |
| Envelope/TCP | arm2_frame é origem de arm2_link | Não é TCP; medir ferramenta, peça mais alta e afastamentos; calcular envelope só com geometria validada |
| Interferências | Sem colisões no perfil atual | Checar CAD e varrer juntas; não há aprovação de movimento livre de colisão |

## Fabricação e montagem

Peças próprias: base, elos/tampas, placas Z, suportes, polias/acoplamentos e
mecanismo da garra são candidatos CAD. Comerciais: rolamentos, motores, servo,
correias, guias, fuso e fixadores precisam de part number e quantidade por ocorrência.
Modelos comerciais no CAD podem ser simplificados; não garantem o produto comprado.

Não foi localizado pacote completo com material por peça, orientação de impressão,
parâmetros de processo, preenchimento, tolerâncias de furos/eixos, ajustes de
rolamento, torque de aperto ou critérios de inspeção. O tutorial externo oferece
sequência de referência, mas a adaptação ATOM não tem montagem as-built fechada.
Não é possível prometer fabricação independente sem perguntas fundamentais.

Para manutenção faltam periodicidade/critério de tensão de correia, folga,
inspeção de fixadores/cabos, lubrificação conforme o componente, desgaste de dedos,
peças de reposição e verificação após troca. Não estabelecer intervalo fictício:
obtê-lo do fabricante e dos ensaios do mecanismo.

## Plano específico de CAD próprio

| Passo | Entrada/dados | Trabalho e aceite |
|---|---|---|
| 1. Baseline | F3D/STEP/SLDASM, fotos e revisão real | Arquivo-mestre identificado; hashes e mudanças mapeados; preservar referências |
| 2. Levantamento | Acesso ao protótipo; paquímetro/medição angular adequados | Medir interfaces críticas, centros/alturas, cursos e peças comerciais com incerteza/instrumento registrados |
| 3. Frames | Árvore da montagem e eixos CAD | Definir base, frames de cada junta e TCP; tabela pai/filho, unidade, sinal, zero, limites e fonte |
| 4. Comerciais | Etiquetas/datasheets e BOM por ocorrência | Resolver modelos de motores, rolamentos, correias, guias, fuso, servo e fixadores antes de dimensionar encaixes |
| 5. Requisitos | Carga útil, alcance, velocidade, custo/processo definidos pelo responsável | Lista de requisitos e casos de carga com critérios mensuráveis |
| 6. Esqueleto paramétrico | Centros/eixos, comprimentos, interfaces | Parâmetros nomeados, relações/restrições explícitas e variações controladas |
| 7. Peças próprias | Interfaces comerciais e processo de fabricação | Modelar base/elos/suportes/garra; dimensão crítica ligada à função; evitar remontar STL como se fosse parametrização |
| 8. Montagem | Peças e transmissões | Mates/juntas, interferência/curso e gerenciamento de cabos testados; resolver cadeia fechada da garra |
| 9. Cálculos | Carga, massa, redução, material e propriedades reais | Torque/força, deflexão, fixação, atrito, folga e margem térmica com hipóteses e limites documentados |
| 10. Desenhos | Peças aprovadas | Material, processo, cotas funcionais, tolerâncias/ajustes, acabamento e revisão suficientes para produzir/inspecionar |
| 11. Fabricação piloto | Desenhos e ferramentas/processo | Produzir e medir primeira peça; registrar desvios e alterar projeto quando necessário |
| 12. Exportações | Baseline CAD | Nativo+STEP para sólidos, STL/3MF para processo, DXF somente quando processo exigir; unidades e revisão presentes |
| 13. URDF/MJCF | Árvore/corpos/inércias exportados | Comparar FK/poses em configurações conhecidas, visuais, colisões e tool frame nos dois simuladores |
| 14. Release | Aceites e BOM associada | Revisão imutável com manifesto, desenhos, fontes, exportações, montagem e histórico de alterações |

**Medir:** centros, interfaces, folgas, sinais/home/cursos, TCP, montagem real,
repetibilidade. **Extrair do CAD:** corpos/juntas/transformações e volume; massa
só após material/densidade corretos. **Calcular:** relações steps/rad e steps/mm,
esforços, deflexões, envelope e orçamento de tolerâncias. **Decidir:** requisitos,
materiais, fabricação, revisão e ferramenta/colaboração.

Ferramentas: Fusion existente favorece leitura do F3D; SolidWorks nativo preserva
fontes SLDPRT/SLDASM se acesso/licença estiverem disponíveis; avaliar alternativa
paramétrica interoperável para CAD próprio conforme acesso da equipe. STEP é
intercâmbio geométrico, não garantia de mates/parametrização. Não recomendar migração
ou licenças sem testar importação/exportação e automação no fluxo necessário.
