"""Prepare a versioned autonomous curriculum while retaining source physics."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from atom_mujoco.chess_commands import fen_occupancy


def prepare(source, output, *, isolated=False, start_radius=(2., 3.), reach_squares=1., reach_xyz=False):
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    config = json.loads(source.read_text(encoding='utf-8'))
    if output.exists():
        raise FileExistsError('Use a fresh curriculum directory')
    if isolated:
        example = Path(__file__).resolve().parents[2]/'examples/prepare_camera_task/run.py'
        spec = importlib.util.spec_from_file_location('prepare_camera_fixture', example)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.prepare(config['bundle'], Path(config['bundle'])/'model.xml', config['layout'],
                       output/'bundle', piece=config['piece'], source=config['source'],
                       target=config['target'], camera=config['camera'])
        derived = json.loads((output/'bundle/environment.json').read_text(encoding='utf-8'))
        for key in ('bundle', 'layout', 'obstacle_pieces'):
            config[key] = derived[key]
        occupied = fen_occupancy(config['board_fen'])
        selected = occupied[config['source']]
        ranks = []
        for rank in range(8, 0, -1):
            row, empty = '', 0
            for file in 'abcdefgh':
                if file+str(rank) == config['source']:
                    row += (str(empty) if empty else '')+selected
                    empty = 0
                else:
                    empty += 1
            ranks.append(row+(str(empty) if empty else ''))
        config['board_fen'] = '/'.join(ranks)+' w - - 0 1'
    else:
        output.mkdir(parents=True)
    config['autonomous'] = dict(reach_distance_squares=reach_squares,
                                start_radius_squares=list(start_radius) if start_radius else None,
                                stage='isolated_reach' if isolated else 'full_board_reach')
    if reach_xyz:
        config['autonomous'].update(action_mode='reach_xyz', xyz_action_scale=.25,
            workspace_radius_squares=2.5, fixed_wrist_rad=0., fixed_elbow_down=True,
            reward_profile='dense_progress_v2', reach_progress_weight=10., reach_timeout_penalty=0.,
            observation_profile='vision_features_v1',
            stage='isolated_xyz_reach' if isolated else 'neighbor_xyz_reach')
    (output/'environment.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    (output/'provenance.json').write_text(json.dumps(dict(source=str(source),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        isolated=isolated, physics='source model properties and collision geometry retained'), indent=2), encoding='utf-8')
    print(output/'environment.json', flush=True)
    return output/'environment.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--isolated', action='store_true')
    parser.add_argument('--start-radius-squares', type=float, nargs=2, default=(2., 3.))
    parser.add_argument('--parked', action='store_true', help='Use the original parked start')
    parser.add_argument('--reach-distance-squares', type=float, default=1.)
    parser.add_argument('--reach-xyz', action='store_true', help='Version 4 three-action local reach curriculum')
    args = parser.parse_args()
    if not 0 < args.reach_distance_squares <= 2 or not 0 < args.start_radius_squares[0] < args.start_radius_squares[1] <= 16:
        parser.error('Expected a positive reach threshold and ordered positive start radii')
    prepare(args.config, args.output, isolated=args.isolated,
            start_radius=None if args.parked else args.start_radius_squares,
            reach_squares=args.reach_distance_squares, reach_xyz=args.reach_xyz)


if __name__ == '__main__':
    main()
