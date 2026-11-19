"""Regenerate the canonical isolated reach fixture and run its short comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-bin', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'))
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    module = here.parents[1]
    repo = module.parents[1]
    canonical = here/'canonical-reach.json'
    protocol = json.loads(canonical.read_text(encoding='utf-8'))
    native = args.native_bin.resolve()
    for filename in ('perception_image.exe', 'motion_runtime.dll', 'acvision_runtime.dll'):
        if not (native/filename).is_file():
            parser.error(f'Missing native build output: {native/filename}')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'protocol.json').write_bytes(canonical.read_bytes())

    def run(*arguments):
        subprocess.run([sys.executable, '-u', '-B', *map(str, arguments)], cwd=repo, check=True)

    base, reference, fixture = (output/name for name in ('base', 'reference', 'fixture'))
    layout = module/'configs/perception/h-file-layout.json'
    run('-m', 'atom_mujoco.cli', 'build', '--urdf', repo/'simulation/src/urdf/atom.urdf.xacro',
        '--output', base, '--parameters', module/'playground/configs/playground-reachable-board.json',
        '--interactive', '--wrist', '--full-gripper-collision')
    run(module/'examples/validate_board_reference/run.py', '--bundle', base,
        '--assets', repo/'docs/camera-rl/aruco-assets-v4', '--layout', layout,
        '--executable', native/'perception_image.exe', '--output', reference)
    env = protocol['environment']
    run(module/'examples/prepare_camera_task/run.py', '--bundle', base,
        '--reference-scene', reference/'reference-scene.xml', '--layout', layout,
        '--output', fixture, '--piece', env['piece'], '--source', env['source'], '--target', env['target'])
    config = output/'environment.json'
    env.update(bundle=str(fixture), layout=str(fixture/'reference-layout.json'),
               vision_library=str(native/'acvision_runtime.dll'), motion_library=str(native/'motion_runtime.dll'))
    config.write_text(json.dumps(env, indent=2), encoding='utf-8')
    training = protocol['training']
    if args.device:
        training['device'] = args.device
    (output/'preparation.json').write_text(json.dumps(dict(
        canonical_sha256=hashlib.sha256(canonical.read_bytes()).hexdigest(),
        model_sha256=hashlib.sha256((fixture/'model.xml').read_bytes()).hexdigest(),
        training=training), indent=2), encoding='utf-8')
    if not args.prepare_only:
        flags = [value for key, val in training.items() for value in ('--'+key.replace('_', '-'), str(val))]
        run(here/'run.py', '--config', config, '--output', output/'training',
            '--headless', '--evaluate-before', *flags)


if __name__ == '__main__':
    main()
