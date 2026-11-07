"""Chess Core task bridge. No chess legality is implemented in Python."""
import json
import os
from pathlib import Path
import subprocess


def plan_move(history, move):
    repo = Path(__file__).resolve().parents[4]
    configured = os.environ.get('ATOM_CHESS_BRIDGE')
    if configured:
        command = [configured]
    elif os.name == 'nt':
        binary = repo / 'build/chess-ui/software/integration/chess_move_request'
        drive = binary.drive[0].lower()
        linux = '/mnt/'+drive+binary.as_posix()[2:]
        command = ['wsl', '-d', 'Ubuntu', '--', linux]
    else:
        command = [str(repo / 'build/chess-ui/software/integration/chess_move_request')]
    result = subprocess.run(command + list(history) + [move], capture_output=True,
                            text=True, timeout=15)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or 'Chess Core bridge failed')
    return json.loads(result.stdout)


def fen_occupancy(fen):
    """Decode the placement field exported by Chess Core."""
    fields = fen.split()
    ranks = fields[0].split('/') if fields else []
    if len(ranks) != 8:
        raise ValueError('Expected eight ranks in Chess Core FEN')
    occupied = {}
    for row, rank in enumerate(ranks):
        column = 0
        for symbol in rank:
            if symbol in '12345678':
                column += int(symbol)
            elif symbol in 'pnbrqkPNBRQK' and column < 8:
                occupied[chr(97+column)+str(8-row)] = symbol
                column += 1
            else:
                raise ValueError('Invalid Chess Core FEN placement')
        if column != 8:
            raise ValueError('Expected eight files in Chess Core FEN rank')
    return occupied


def execute_chess_move(playground, source, target):
    if playground.manual.active or playground.physical.reconciliation_required:
        raise ValueError('Autonomous chess requires a reconciled scene and manual mode off')
    proposal = source+target
    playground.monitor.emit('chess', 'running', 'Chess Core validation and TaskPlanner: '+proposal)
    try:
        plan = plan_move(playground.chess_history, proposal)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        playground.monitor.emit('chess', 'failed', str(error))
        raise
    playground.monitor.emit('chess', 'completed', f"Validated, {len(plan['steps'])} physical steps")
    # Verify the complete observed physical occupancy against the logical FEN.
    symbols = {'pawn':'p','knight':'n','bishop':'b','rook':'r','queen':'q','king':'k'}
    kinds = {p['name']: p for p in playground.sim.manifest['pieces']}
    expected = fen_occupancy(plan['fen'])
    actual = {}
    for square,identity in playground.physical.confirmed.occupancy.items():
        if identity:
            record = kinds[identity]
            char = symbols[record['kind']]
            actual[square] = char.upper() if record['color']=='white' else char
    if actual != expected:
        raise ValueError('Logical/physical board disagreement requires reconciliation')
    transfers = []
    for step in plan['steps']:
        destination = step['target']
        if destination == 'home':
            identity = playground.physical.confirmed.occupancy[step['source']]
            destination = 'graveyard:'+kinds[identity]['graveyard_slot']
        transfers.append(dict(source=step['source'], target=destination))
    result = playground.execute_request(dict(schema=2, operation='PLAN', transfers=transfers))
    if result['status']=='COMPLETED_SIMULATION_ORACLE':
        playground.chess_history.append(proposal)
    return result
