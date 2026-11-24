# P002 — Auditoria de engenharia por evidência e revisão

Data: 30/10/2026. Estado: aceito para esta auditoria.

Contexto: responsável solicita visão geral de mecânica, BOM, elétrica, firmware,
software, simulação e preparação para CAD próprio antes de novas implementações.
Existem branches divergentes, referência CAD externa e artefatos locais não Git.

Decisão: congelar referências HEAD 0b13845/main f72c893, inventariar separadamente,
usar estados Verificado/Documentado/Inferido/Desconhecido/Inconsistente/Não aplicável
e registrar achados com evidência, limite da conclusão e ação. Entrega em
docs/audit/2026-10-30, relatórios por área e índice A–G, sem refatoração ou CAD novo.
Guardar resultados de testes proporcionais e falhas, sem confundir teste sintético
com validação física ou contagem de arquivo com quantidade de BOM.

Consequência: componentes de main são examinados em cópia isolada sem merge;
alterações locais preservadas. P0 de alimentação/parada é gate antes de operação,
não declaração de bancada energizada ou conformidade. Dados ausentes não serão
substituídos por números de fixtures, nomes de malhas ou parâmetros sintéticos.
Correções propostas entram em entregas posteriores após avaliação e priorização.

Histórico: build main com ament falhou; headless sem descoberta ament passou.
Ambos os resultados pertencem à auditoria; o contorno não foi promovido a correção.
Referência: [auditoria A–G](../audit/2026-10-30/README.md).
