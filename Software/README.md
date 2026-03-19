<div>

  <h1>Taxonomia</h1>
vision/
board_state/
engine/
motion/
robot/
integration/
config/
tests/

vision/
Tudo que envolve câmera, calibração, homografia, detecção de peças.

board_state/
Representação do tabuleiro. Conversão entre coordenadas de casa (E2) e coordenadas reais (x, y).

engine/
Interface com Stockfish. Nada de lógica física aqui. Só comunicação e interpretação de movimentos.

motion/
Planejamento de trajetórias. Conversão de coordenadas do mundo para pontos que a garra precisa visitar.

robot/
Drivers do SCARA. Comunicação serial, controle de motores, cinemática direta e inversa.

integration/
Onde o sistema todo conversa. Máquina de estados do robô. Aqui você decide: capturar imagem → validar → mover → confirmar.

config/
Parâmetros físicos:

– Altura da câmera
– Matriz de transformação câmera→garra
– Dimensões do tabuleiro
– Limites do SCARA

Nada de valores mágicos espalhados pelo código.

tests/
Testes unitários.
Teste de homografia.
Teste de cinemática inversa.
Teste de conversão casa→coordenada.

Agora algo que pouca gente faz e deveria fazer: versionar calibrações.

Crie uma pasta:

calibration_data/
</div>
