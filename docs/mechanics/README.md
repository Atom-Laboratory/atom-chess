# Mecânica — fontes e lacunas

Atualização: [capturas e limites CAD da garra](gripper-cad-evidence.md), com
junta revoluta em Z local de -45° a +10°. Nome/frame e acoplamento ainda precisam
de extração da montagem. [ADR M002](adrs/M002-gripper-limits.md).

Fonte oficial confirmada: SCARA Robot.f3d no repositório 3DSCARAROBOT.
[Registro detalhado de evidências](../../simulation/docs/mechanical-evidence.md)
mantido no caminho original para preservar referências anteriores.

O STEP disponível é uma exportação antiga; equivalência à revisão F3D não foi
confirmada. O CAD dentro de Hardware também não foi declarado substituto da
referência externa. Não houve extração confiável de centros/eixos da montagem.

| Necessário | Estado | Bloqueia |
|---|---|---|
| Transformações entre corpos, unidades e eixos | Desconhecidas/calibração pendente | URDF fiel |
| Zeros, sinais, limites físicos | Desconhecidos | Hardware e homing |
| TCP, J3, garra | Ausentes no protótipo | Manipulação |
| Massas, inércias, atrito | Desconhecidos | Dinâmica |
| Geometria de colisão validada | Ausente | Movimento seguro e contatos |

Próxima entrega: tabela por junta com pai/filho, frame, eixo, zero, limite,
unidade, fonte CAD/medição e evidência de revisão. Comparar malhas no RViz com
montagem antes de alterar offsets. [Decisão M001](adrs/M001-cad.md).
