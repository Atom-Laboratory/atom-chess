# M001 — CAD oficial e parâmetros desconhecidos

Data: 30/10/2026. Estado: aceito, registrando confirmação anterior do responsável.

Decisão: SCARA Robot.f3d é referência oficial; limites/origens do URDF são dados
de um protótipo de software. Não deduzir comprimento entre eixos pelo bounding
box de STL nem assumir STEP antigo equivalente. Não inventar massas ou TCP.

Consequência: preservar visualização diagnóstica; bloquear dependências físicas
até medições/exportação rastreável. Uma aproximação futura deve indicar fonte,
incerteza e objetivo, e não ser promovida a especificação do hardware.
