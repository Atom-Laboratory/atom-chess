"""Named, stylized chess pieces for scene inspection, without grasp physics."""
import xml.etree.ElementTree as ET


def add_pieces(board, square_size):
    """Add the standard starting arrangement in the board's local frame."""
    records = []
    back_rank = ('rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook')
    for color, ranks in (('white', (0, 1)), ('black', (7, 6))):
        rgba = '.92 .9 .82 1' if color == 'white' else '.06 .07 .09 1'
        for rank in ranks:
            for file in range(8):
                kind = back_rank[file] if rank == ranks[0] else 'pawn'
                square = chr(97+file)+str(rank+1)
                name = f'{color}_{kind}_{square}'
                body = ET.SubElement(board, 'body', name=name,
                    pos=f'{(file-3.5)*square_size} {(rank-3.5)*square_size} .008')
                def geom(part, shape, size, pos, **extra):
                    ET.SubElement(body, 'geom', name=name+'_'+part, type=shape,
                                  size=size, pos=pos, rgba=rgba, contype='0', conaffinity='0', **extra)
                geom('base', 'cylinder', '.012 .003', '0 0 .003')
                height = dict(pawn=.018, rook=.026, knight=.028, bishop=.03, queen=.034, king=.038)[kind]
                geom('stem', 'cylinder', '.006 '+str(height/2), f'0 0 {height/2+.006}')
                top = height+.006
                if kind in ('pawn', 'bishop', 'queen'):
                    geom('head', 'sphere', '.008', f'0 0 {top}')
                elif kind == 'rook':
                    geom('head', 'box', '.01 .01 .004', f'0 0 {top}')
                elif kind == 'knight':
                    geom('head', 'box', '.006 .01 .009', f'0 -.004 {top}', euler='.4 0 0')
                else:
                    geom('cross_vertical', 'box', '.002 .002 .008', f'0 0 {top+.004}')
                    geom('cross_horizontal', 'box', '.007 .002 .002', f'0 0 {top+.006}')
                records.append(dict(name=name, color=color, kind=kind, initial_square=square))
    return records
