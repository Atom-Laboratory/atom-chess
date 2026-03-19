<div><h1>Como rodar o teste da câmera</h1> 

<h2>1. Instalando o OpenCV Windows</h2> 

  <p>1.1 Acesse -https://github.com/opencv/opencv/releases- e baixe o arquivo opencv-4.13.0-windows.exe;</p> 
  <p>1.2 Execute o instalador e indique um local no qual os arquivos do OpenCV serão instalados (É recomendável instalar diretamente no HD/SSD de sua preferência).</p> 

<h2>2. Configurando a pasta bin para as variáveis de ambiente do sistema</h2>
  <p>2.1. No meu iniciar, pesquise por "Editar as variáveis de ambiente do sistema;</p>
  <p>2.2. Siga o caminho - Variáveis de Ambiente>Path>Novo>[Caminho escolhido no passo 1.2]</p>
  <p>2.3. **Reinicie o computador**.</p>

<h3>3. Instalando e configurando o Visual Studio</h3>
  <p>3.1. Acesse -https://visualstudio.microsoft.com/pt-br/-, baixe e instale o Visual Studio Community Edition;</p>
  <p>3.2. **Importante:** Durante a instalação, selecione a opção "Desenvolvimento Desktop com C++;</p>
  <p>3.3. Crie um novo projeto, selecionando "Projeto vazio" e digite o nome do projeto (ex.: Atom-OpenCV-Test);</p>
  <p>3.4. Na aba superior, certifique-se de que a plataforma selecionada está x64;</p>
  <p>3.5. Na aba de menus, clique em "Projeto" e então em "Propriedades";</p>
  <p>3.6. Clique em Diretórios VC++;</p>
    <p>&nbsp&nbsp&nbsp&nbsp&nbsp3.6.1. Clique Em "Diretórios de Inclusão, na seta que aparecerá à direita, e "editar";</p>
    <p>&nbsp&nbsp&nbsp&nbsp&nbsp3.6.2. Digite o caminho C:\opencv\build\include (O caminho pode variar até '\opencv\' de acordo com a instalação realizada no passo 1.2);</p>
    <p>&nbsp&nbsp&nbsp&nbsp&nbsp3.6.3. Repita os dois passos anteriores, mas agora para a opção "Diretórios de Biblioteca", usando o caminho C:\opencv\build\x64\vc16\lib (O caminho pode variar até '\opencv\' de acordo com a instalação realizada no passo 1.2);</p>
  <p>3.7. Clique em "Vinculador", "Entrada" e "Dependências Adicionais";</p>
    <p>&nbsp&nbsp&nbsp&nbsp&nbsp3.7.1. Clique na seta que aperecerá à direita, e então adicione o linker "opencv_world4130d.lib".</p>
  <p>3.8. No Gerenciador de soluções, clique com o botão direito no nome do projeto > Abrir no gerenciador de arquivos;</p>
  <p>3.9. Arraste as pastas 'src', 'include' e 'examples' para a pasta do projeto;</p>
  <p>3.10. Rode o arquivo 'camera-test' via depurador local do Windows.</p>
</div>
<hr>

<div>