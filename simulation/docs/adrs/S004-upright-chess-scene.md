# S004 — Montagem vertical, tabuleiro e garra visual no MuJoCo

Data: 30/10/2026. Estado: aceito.

Contexto: usuário observou o braço deitado e solicitou tabuleiro e garra ausente.
O URDF usa Y como vertical; MuJoCo usa Z. As três malhas da garra já existem,
mas não são links do URDF. Não há juntas/limites de abertura nem TCP calibrados.

Decisão: aplicar Rx(+90°) e translação [0,0,0.035] m ao conjunto do robô, sem
alterar URDF ou malhas. Mapeamento mundo URDF→cena: [x,y,z]→[x,-z,y+0.035].
Offset de altura apoia a base visual cujo mínimo Y é -35 mm no STL, assumindo
a escala 0.001 herdada. Isso não identifica centros articulares por bounding box.

Incluir gripper_back/hand1/hand2 como geometrias visuais fixas em arm2_link,
offset [-0.26,0,0] m igual ao visual de arm2, usando as coordenadas da montagem
original em zero. É montagem provisória; não é extração da revisão F3D oficial.
Não adicionar articulação, inércia, massa ou TCP fictícios à garra. Ela acompanha
a última junta, porém não abre, fecha ou prende peças.

Tabuleiro de referência com 64 casas de 0.04 m, centro [0.34,-0.22,0.012] m,
espessura/base gráfica e sites nomeados square_center_a1...h8. Esses valores são
escolhas de cenário, não dimensões físicas confirmadas. a1 é casa escura no
canto de menores X/Y. Sem peças, contato ou vínculo com núcleo de xadrez.

SCENE no gerador e manifest guardam transformação, parâmetros de cenário e
câmera. Bundle novo upright-chess-v2 mantém experimentos antigos intactos;
launcher padrão passa a usá-lo. Alterar o mundo muda posições/orientações globais
das observações: consumidores devem ler o manifest, não reutilizar metas
cartesianas antigas sem transformar. Ordem/unidades/metas articulares preservadas.

Validação: render real inspecionado; testes de FK no mundo transformado, vertical,
64 casas, rigidez da garra em relação ao braço e tabuleiro estático. Perfil
dinâmico sintético e contatos desativados permanecem como em S003.
