# Evidências e condições para avançar

## Base desta implementação

- Branch recebida: `ros2_simulation`.
- HEAD antes das alterações: `e6c9b1eba91976e78e64c2cde4ce0972b077aa3a`.
- Estado Git inicial limpo; branch preservada.
- O planejamento anterior inspecionou outra revisão (`main`, `f72c893...`).
  Suas conclusões sobre pacotes duplicados, acmotion e atom_control não devem
  ser aplicadas automaticamente a esta branch, que contém apenas acvision e a
  descrição ROS em `simulation/src`.
- Referência mecânica oficial: `SCARA Robot.f3d`, confirmada pelo usuário em
  27/10/2026. Caminho observado:
  `F:\Users\EHD\Github\er\3DSCARAROBOT\SCARA Robot.f3d`.
- SHA-256 do F3D inspecionado:
  `87C6AC84DCD57B70577587C37F9D8D7049D3EF2A207B9D8F500557833E5C98A5`.

## Registro de geometria

| Dado | Evidência atual | Confiança/ação pendente |
|---|---|---|
| Revisão CAD de referência | Confirmação do responsável: F3D | Fonte selecionada; extrair montagem |
| Sete STL existentes | `src/meshes` | Proveniência da exportação a comparar com F3D |
| Escala 0,001 | Xacro herdado | Hipótese do protótipo; confirmar unidade CAD/STL |
| Eixos Y, offsets e limites | Xacro herdado | Não são calibração física |
| Três juntas móveis no URDF | Duas revolutas e uma prismática | Estrutura de software; não confirma DOFs completos |
| J3, TCP, garra | Ausentes do URDF atual | Extrair da montagem antes de implementar |
| L1/L2 entre centros | Não medidos nesta branch | Bloqueiam IK fiel e alcance |
| Limites, zeros e sinais reais | Sem registro validado | Bloqueiam movimento apresentado como fiel |
| Massas/inércias/transmissões | Sem registro validado | Bloqueiam simulação física e driver real |

O visual existente é um diagnóstico do arquivo. Nenhuma dimensão, origem,
orientação, limite, massa ou relação de transmissão foi inventada neste incremento.

## Gate mecânico

Antes de substituir a geometria do protótipo, registrar por junta: corpo pai e
filho, centro/eixo no F3D, transformação CAD→ROS, sinal, zero e limites com fonte.
Para cada link, registrar a pose da malha no seu referencial e uma comparação
com a montagem. Para cada comprimento, distinguir dimensão externa de distância
entre centros. Confirmar o TCP e os offsets da ferramenta.

Se um dado essencial não puder ser extraído com confiança, interromper o
incremento dependente e solicitar a medição ou exportação específica. Preservar
o modo diagnóstico até a aprovação desses dados. RViz e testes estruturais
aprovados não demonstram fidelidade ao hardware.
