#Como rodar o teste da câmera

###1. Instalando o OpenCV Windows

  1.1 Acesse -https://github.com/opencv/opencv/releases- e baixe o arquivo opencv-4.13.0-windows.exe;
  1.2 Execute o instalador e indique um local no qual os arquivos do OpenCV serão instalados (É recomendável instalar diretamente no HD/SSD de sua preferência).

###2. Configurando a pasta bin para as variáveis de ambiente do sistema
  2.1. No meu iniciar, pesquise por "Editar as variáveis de ambiente do sistema;
  2.2. Siga o caminho - Variáveis de Ambiente>Path>Novo>[Caminho escolhido no passo 1.2]
<img src="https://imgur.com/a/l8v7gRu" width="70">
  2.3. **Reinicie o computador**.

###3. Instalando e configurando o Visual Studio
  3.1. Acesse -https://visualstudio.microsoft.com/pt-br/-, baixe e instale o Visual Studio Community Edition;
  3.2. **Importante:** Durante a instalação, selecione a opção "Desenvolvimento Desktop com C++;
<img src="https://imgur.com/JdRB9Gg" width="70">
  3.3. Crie um novo projeto, selecionando "Projeto vazio" e digite o nome do projeto (ex.: Atom-OpenCV-Test);
  3.4. Na aba superior, certifique-se de que a plataforma selecionada está x64;
  3.5. Na aba de menus, clique em "Projeto" e então em "Propriedades";
  3.6. Clique em Diretórios VC++;
    3.6.1. Clique Em "Diretórios de Inclusão, na seta que aparecerá à direita, e "editar";
    3.6.2. Digite o caminho C:\opencv\build\include (O caminho pode variar até '\opencv\' de acordo com a instalação realizada no passo 1.2);
    3.6.3. Repita os dois passos anteriores, mas agora para a opção "Diretórios de Biblioteca", usando o caminho C:\opencv\build\x64\vc16\lib (O caminho pode variar até '\opencv\' de acordo com a instalação realizada no passo 1.2);
  3.7. Clique em "Vinculador", "Entrada" e "Dependências Adicionais";
    3.7.1. Clique na seta que aperecerá à direita, e então adicione o linker "opencv_world4130d.lib".
  3.8. No Gerenciador de soluções, clique com o botão direito no nome do projeto > Abrir no gerenciador de arquivos;
  3.9. Arraste as pastas 'src', 'include' e 'examples' para a pasta do projeto;
  3.10. Rode o arquivo 'camera-test' via depurador local do Windows.



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
