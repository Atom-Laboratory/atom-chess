"""Physical plan validation only; chess rules belong to the upstream Chess Core."""
from .physical_state import endpoint


def validate_plan(request, snapshot):
    if (not isinstance(request, dict) or set(request) != {'schema', 'operation', 'transfers'}
            or type(request['schema']) is not int or request['schema'] != 2
            or request['operation'] != 'PLAN' or not isinstance(request['transfers'], list)
            or not 1 <= len(request['transfers']) <= 4):
        raise ValueError('Invalid complete physical plan envelope')
    occupied = {p.location: p.identity for p in snapshot.pieces}
    reservations = []
    for transfer in request['transfers']:
        if not isinstance(transfer, dict) or set(transfer) != {'source', 'target'}:
            raise ValueError('Invalid transfer payload')
        source, target = endpoint(transfer['source']), endpoint(transfer['target'])
        for loc in (source, target):
            if loc.kind == 'graveyard' and loc.slot not in snapshot.graveyard_slots:
                raise ValueError('Unknown Graveyard slot')
        if source == target or source not in occupied or target in occupied:
            raise ValueError('Plan occupancy conflict; removal must precede attacker transfer')
        occupied[target] = occupied.pop(source)
        reservations.append(target)
    return tuple(reservations)
