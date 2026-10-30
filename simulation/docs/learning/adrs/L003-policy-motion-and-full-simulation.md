# L003 — Política, acmotion e validação completa no Gazebo

Data: 30/10/2026. Estado: aceito para requisitos e limites; implementação de
integração/garra dinâmica pendente de dados mecânicos.

Contexto: responsável pergunta como treinar tarefas, transferir ao robô e integrar
acmotion; pede Gazebo com toda a mecânica móvel e peças no tabuleiro.

Decisão: documentar pipeline real de main sem fazer merge da branch; política
futura executará na SBC através de estratégia validada de movimento, preservando
MotionExecution/ACM1/ESP32. Não substituir transporte por inferência nem assumir
ACK/DONE como observação de juntas ou confirmação de preensão.

MuJoCo permanece para estudo/treinamento; Gazebo passa a requisito explícito de
integração ROS, complementando S003. Não afirmar que robô inteiro está simulado:
faltam J3, garra articulada, colisões e dinâmica calibrada. Implementação física
completa condicionada a extrair juntas e acoplamentos do CAD. Registrar inventário
de dependências em gazebo-readiness.md.

Adicionar agora 32 peças estilizadas na disposição inicial, nomeadas por cor,
tipo e casa. Elas são visuais fixos na cena upright-chess-v3; manifest explicita
pieces_physics=fixed-visual-only. Não são corpos agarráveis, dados de percepção
ou estado legal de partida. Não alterar nq/nu ou contatos para aparentar preensão.

Alternativa rejeitada: treinar antes de completar mecanismo de preensão, ou
definir uma rede por lance como pressuposto. Habilidades e política condicionada
à meta serão escolhas do responsável após controle convencional validado.
