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


def execute_chess_move(playground, source, target):
    if playground.manual.active or playground.physical.reconciliation_required:
        raise ValueError('Autonomous chess requires a reconciled scene and manual mode off')
    proposal = source+target
    plan = plan_move(playground.chess_history, proposal)
    # Verify the complete observed physical occupancy against the logical FEN.
    symbols = {'pawn':'p','knight':'n','bishop':'b','rook':'r','queen':'q','king':'k'}
    kinds = {p['name']: p for p in playground.sim.manifest['pieces']}
    expected = {}
    for rank_index,row in enumerate(plan['fen'].split()[0].split('/')):
        file = 0
        for char in row:
            if char.isdigit():
                file += int(char)
            else:
                expected[chr(97+file)+str(8-rank_index)] = char
                file += 1
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
