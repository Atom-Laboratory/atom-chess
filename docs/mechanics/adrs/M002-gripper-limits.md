# M002 — Incorporar limites CAD sem presumir correspondência de juntas

Data: 30/10/2026. Estado: aceito para evidência; aplicação ao runtime pendente.

Contexto: responsável forneceu captura Edit Joint da garra em Arm_Assembly,
com revoluta Z local, mínimo -45° e máximo +10°, ambos habilitados. Rest +10°
está desabilitado. Nome da junta e transformação dos referenciais não aparecem.

Decisão: versionar capturas e transcrição em gripper-cad-evidence.md; converter
limites para radianos explicitamente. Vincular dados a essa evidência visual,
sem declarar confirmação de limites físicos ou do servo. Não atribuir essa
faixa a todos os elos nem inventar zeros/abertura. Aplicação ao modelo depende
de identificar junta motora/passiva, pai/filho e acoplamento na montagem.

Consequência: parte da lacuna de limites está resolvida, mas garra articulada,
colisão e preensão ainda exigem extração geométrica/mecânica. A indicação de
Z no Fusion é local; orientação global depende da cadeia de transformações.
