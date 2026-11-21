"""Bounded shared BC/PPO macro-parameter pilot, using isolated GPU physics worlds."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback

import numpy as np
import torch

from atom_mujoco.backend import Simulation
from demonstrations import digest, validate_actor
from parameter_policy import ParameterPolicy, context, expert_latent, physical_reward, ppo_update, to_parameters


SOURCES = ('parameter_policy.py', 'evaluate_parameters.py', 'demonstrations.py', 'cem.py', 'cem_core.py',
           'batch.py', 'tapes.py', 'outcomes.py', 'cuda_rollout.py', 'replay.py', 'requirements-windows-py312.lock')


def demonstration_context(directory, reference, config_path, sim):
    report = json.loads((directory / 'report.json').read_text())
    if (report['status'] != 'PHYSICAL_DEMONSTRATION_EXPORTED' or not report['outcome']['success']
            or report['config_sha256'] != digest(config_path) or report['model_sha256'] != sim.manifest['model_sha256']
            or report['reference_report_sha256'] != digest(reference / 'local-report.json')
            or report['handoff_sha256'] != digest(reference / 'handoff.json')):
        raise ValueError('Matching verified demonstration/reference required')
    actor_path = directory / 'actor.npz'
    if digest(actor_path) != report['artifacts_sha256']['actor.npz']:
        raise ValueError('Actor archive hash mismatch')
    with np.load(actor_path, allow_pickle=False) as archive:
        fields = {key: archive[key] for key in archive.files}
    validate_actor(fields, report['frames'], sim.model.nu)
    return context({key: fields[key][0] for key in ('source_xy_m', 'issued_command', 'squares')}, sim.lower, sim.upper)


def checkpoint(path, policy, optimizer, identity, completed, best_reward, stale):
    torch.save(dict(policy=policy.state_dict(), optimizer=optimizer.state_dict(), identity=identity,
        completed_updates=completed, best_training_reward=best_reward, stagnant_updates=stale,
        rng_cpu=torch.get_rng_state(), rng_cuda=torch.cuda.get_rng_state_all() if next(policy.parameters()).is_cuda else []), path)


def restore(path, policy, optimizer, identity, device):
    saved = torch.load(path, map_location=device, weights_only=True)
    if saved['identity'] != identity:
        raise ValueError('Policy checkpoint input/source identity mismatch')
    policy.load_state_dict(saved['policy']); optimizer.load_state_dict(saved['optimizer'])
    torch.set_rng_state(saved['rng_cpu'].cpu())
    if saved['rng_cuda']:
        torch.cuda.set_rng_state_all([state.cpu() for state in saved['rng_cuda']])
    return saved['completed_updates'], saved['best_training_reward'], saved['stagnant_updates']


def worker(args):
    deadline = time.monotonic() + args.max_wall_s
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim = Simulation(config['bundle'])
    if len(sim.manifest['pieces']) != 1:
        raise ValueError('Only isolated Stage A research policy training is qualified')
    if digest(args.training_reference / 'local-report.json') == digest(args.validation_reference / 'local-report.json'):
        raise ValueError('Validation must use an excluded reference, not correlated frames')
    training = demonstration_context(args.training_demo, args.training_reference, args.config, sim)
    validation = demonstration_context(args.validation_demo, args.validation_reference, args.config, sim)
    train_report = json.loads((args.training_demo / 'report.json').read_text())
    expert = json.loads(args.expert.read_text())
    if (digest(args.expert) != train_report['candidate_report_sha256']
            or expert['status'] != 'CEM_CPU_VERIFIED_CANDIDATE' or not expert['canonical_winner']['success']):
        raise ValueError('Training demonstration must bind a canonical-verified CEM expert')
    device = torch.device(args.device)
    if device.type == 'cuda' and not torch.cuda.is_available():
        raise ValueError('Requested PyTorch CUDA device is unavailable')
    policy = ParameterPolicy().to(device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=.0003)
    identity = dict(schema='stage-a-camera-command-macro-v1', model_sha256=sim.manifest['model_sha256'],
        config_sha256=digest(args.config), training_demo_sha256=digest(args.training_demo / 'report.json'),
        validation_demo_sha256=digest(args.validation_demo / 'report.json'), expert_sha256=digest(args.expert), seed=args.seed,
        sources={name: digest(Path(__file__).with_name(name)) for name in ('train_parameters.py', *SOURCES)},
        device=args.device, torch_version=str(torch.__version__), mujoco_version=__import__('mujoco').__version__)
    completed, best_reward, stale = 0, -1e9, 0
    train_tensor = torch.as_tensor(training[None, :], device=device)
    val_tensor = torch.as_tensor(validation[None, :], device=device)
    if args.resume:
        completed, best_reward, stale = restore(args.resume, policy, optimizer, identity, device)
    else:
        bc_optimizer = torch.optim.Adam(policy.actor.parameters(), lr=.003)
        target = expert_latent([expert['best']['parameters']], device=device)
        with (args.output / 'bc-metrics.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream); writer.writerow(['epoch', 'actor_latent_mse'])
            for epoch in range(args.bc_epochs):
                loss = torch.nn.functional.mse_loss(policy.actor(train_tensor), target)
                bc_optimizer.zero_grad(); loss.backward(); bc_optimizer.step()
                writer.writerow([epoch + 1, float(loss.detach())])
    checkpoint(args.output / 'initial-policy.pt', policy, optimizer, identity, completed, best_reward, stale)

    def evaluate(name, parameters, references, verify_cpu=False):
        remaining = deadline - time.monotonic()
        batch_budget = min(args.batch_wall_s, remaining - 30.)
        if batch_budget < 10.:
            raise RuntimeError('Global wall budget exhausted before dispatch; saved checkpoints remain resumable')
        request = args.output / (name + '-actions.json')
        request.write_text(json.dumps(dict(cases=[dict(reference=str(r), parameters=p.tolist())
            for r, p in zip(references, parameters)]), indent=2), encoding='utf-8')
        output = args.output / name
        command = [str(args.gpu_python), '-u', '-B', str(Path(__file__).with_name('evaluate_parameters.py')),
            '--config', str(args.config), '--actions', str(request), '--max-gpu-mib', str(args.max_gpu_mib),
            '--max-wall-s', str(batch_budget), '--output', str(output)]
        if verify_cpu:
            command.append('--verify-cpu')
        started = time.perf_counter()
        with (args.output / (name + '-launch.log')).open('w', encoding='utf-8') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=batch_budget + 15, check=True)
        report = json.loads((output / 'report.json').read_text())
        if len(report['records']) != len(parameters):
            raise RuntimeError('GPU batch returned mismatching macro episode count')
        return report, time.perf_counter() - started

    with torch.no_grad():
        parameters = to_parameters(policy.actor(torch.cat((train_tensor, val_tensor)))).cpu().numpy()
    before, _ = evaluate('before', parameters, [args.training_reference, args.validation_reference], True)
    episode_budget = args.population * args.updates
    samples = 0
    rows = []
    with (args.output / 'training-metrics.csv').open('w', newline='', encoding='utf-8') as stream, \
         (args.output / 'episodes.csv').open('w', newline='', encoding='utf-8') as episode_stream:
        episode_writer = csv.writer(episode_stream)
        episode_writer.writerow(['update', 'episode', 'load_factor', 'closing_speed_fraction', 'lift_rate_fraction', 'reward',
            'geometry_valid', 'physical_success', 'forbidden_contact', 'duration_s', 'minimum_held_rise_m', 'maximum_hold_slip_m'])
        writer = None
        for iteration in range(args.updates):
            update = completed + iteration + 1
            observations = train_tensor.repeat(args.population, 1)
            with torch.no_grad():
                latent = policy.distribution(observations).sample()
                old_log_prob = policy.log_prob(observations, latent)
                parameters = to_parameters(latent).cpu().numpy()
            report, evaluation_wall = evaluate(f'update-{update}', parameters, [args.training_reference] * args.population)
            rewards = np.array([physical_reward(record) for record in report['records']], dtype=np.float32)
            started = time.perf_counter()
            losses = ppo_update(policy, optimizer, observations, latent, old_log_prob,
                                torch.as_tensor(rewards, device=device), epochs=args.ppo_epochs)
            update_wall = time.perf_counter() - started
            samples += args.population
            success = sum(record.get('outcome', {}).get('success', False) for record in report['records'])
            row = dict(update=update, macro_episodes_this_run=samples, maximum_macro_episode_budget=episode_budget,
                physical_successes=success, population=args.population, reward_mean=float(rewards.mean()),
                evaluation_wall_s=evaluation_wall, policy_update_wall_s=update_wall, **losses)
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(row)); writer.writeheader()
            writer.writerow(row); stream.flush(); rows.append(row)
            for record, reward in zip(report['records'], rewards):
                outcome = record.get('outcome', {})
                episode_writer.writerow([update, record['index'], *record['parameters'], float(reward), record['geometry_valid'],
                    outcome.get('success', False), outcome.get('forbidden_contact'), record.get('duration_s'),
                    outcome.get('minimum_held_rise_m'), outcome.get('maximum_hold_slip_m')])
            episode_stream.flush()
            if row['reward_mean'] > best_reward + 1e-6:
                best_reward, stale = row['reward_mean'], 0
            else:
                stale += 1
            checkpoint(args.output / f'checkpoint-{update}.pt', policy, optimizer, identity, update, best_reward, stale)
            print(f'[ATOM PPO MACRO] update {update} | {samples}/{episode_budget} episodes | held lifts {success}/{args.population}'
                  f' | reward {rewards.mean():.4f} | loss {losses.get("loss", float("nan")):.4f}', flush=True)
            if stale >= args.stagnation_updates:
                print('[ATOM PPO MACRO] stopped on training-only stagnation budget', flush=True)
                break
    with torch.no_grad():
        parameters = to_parameters(policy.actor(torch.cat((train_tensor, val_tensor)))).cpu().numpy()
    after, _ = evaluate('after', parameters, [args.training_reference, args.validation_reference], True)
    checkpoint(args.output / 'policy.pt', policy, optimizer, identity, completed + len(rows), best_reward, stale)
    report = dict(schema=1, experiment='EXP-0008', status='STAGE_A_PARAMETER_POLICY_PILOT_COMPLETED', identity=identity,
        scope='shared contextual-bandit PPO over three planner parameters; not sequential visual servoing or hardware admission',
        algorithm='BC mean warm-start + clipped PPO, gamma=0, tanh Normal, actor/critic 12-64-64-(3/1)',
        actor_features=['camera-derived source XY', 'issued entry command', 'logical source/target squares'],
        learned_parameters=sum(p.numel() for p in policy.parameters()), device=str(device),
        resumed_from=str(args.resume) if args.resume else None, completed_updates=completed + len(rows),
        updates_this_run=len(rows), training_macro_episodes=samples, training_episode_budget=episode_budget,
        evaluation_macro_episodes=4, before=before['records'], after=after['records'],
        checkpoint_sha256=digest(args.output / 'policy.pt'),
        limitations=['One training reference and one excluded validation reference; no reliability/generalization claim.',
            'Frozen signed camera geometry; simulator truth only reset/reward/safety/evaluation.',
            'No low-level trajectory policy, occupied-board entry, placement or camera-only success verification.',
            'GPU physics subprocess and CPU/optional-CUDA PyTorch updates; no end-to-end acceleration claim.'])
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'training_reference', 'validation_reference', 'training_demo', 'validation_demo', 'expert', 'gpu_python'):
        parser.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    parser.add_argument('--updates', type=int, default=3)
    parser.add_argument('--population', type=int, default=8)
    parser.add_argument('--bc-epochs', type=int, default=100)
    parser.add_argument('--ppo-epochs', type=int, default=4)
    parser.add_argument('--stagnation-updates', type=int, default=3)
    parser.add_argument('--seed', type=int, default=970400)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--max-gpu-mib', type=int, default=2048)
    parser.add_argument('--batch-wall-s', type=float, default=180.)
    parser.add_argument('--max-wall-s', type=float, default=600.)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--headless', action='store_true', help='Skip accepted final policy demonstration/Watch replay')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not (1 <= args.updates <= 20 and 4 <= args.population <= 64 and args.population * args.updates <= 1024
            and 1 <= args.bc_epochs <= 1000 and 1 <= args.ppo_epochs <= 10 and 1 <= args.stagnation_updates <= 20
            and 10 <= args.batch_wall_s <= 300):
        parser.error('Finite update/population/optimizer/stagnation/process budgets required')
    if args.worker:
        try:
            worker(args)
        except Exception as error:
            (args.output / 'failure.json').write_text(json.dumps(dict(status='FAILED', error=str(error), traceback=traceback.format_exc()), indent=2))
            raise
        return
    from experiment import bounded_run
    names = ('config', 'training_reference', 'validation_reference', 'training_demo', 'validation_demo', 'expert', 'gpu_python')
    arguments = [item for name in names for item in ('--' + name.replace('_', '-'), str(getattr(args, name).resolve(strict=True)))]
    for name in ('updates', 'population', 'bc_epochs', 'ppo_epochs', 'stagnation_updates', 'seed', 'device', 'max_gpu_mib', 'batch_wall_s'):
        arguments += ['--' + name.replace('_', '-'), str(getattr(args, name))]
    if args.resume:
        arguments += ['--resume', str(args.resume.resolve(strict=True))]
    arguments += ['--max-wall-s', str(max(1., args.max_wall_s - 20.))]
    output, report = bounded_run(__file__, arguments, experiment='EXP-0008', output=args.output,
        sources=[Path(__file__).with_name(n) for n in SOURCES], max_wall_s=args.max_wall_s,
        request=dict(population=args.population, updates=args.updates, maximum_training_episodes=args.population * args.updates))
    print(json.dumps(dict(status=report['status'], output=str(output))), flush=True)
    if not args.headless:
        from experiment import bounded_run as export
        candidate = output / 'after' / 'case-0'
        if candidate.exists() and json.loads((candidate / 'report.json').read_text())['status'] == 'FROZEN_CANDIDATE_EVALUATION_PASSED':
            source_files = [Path(__file__).with_name(n) for n in ('cem.py', 'cem_core.py', 'batch.py', 'tapes.py', 'outcomes.py', 'replay.py')]
            demonstration, _ = export(Path(__file__).with_name('demonstrations.py'),
                ['--config', str(args.config.resolve()), '--reference', str(args.training_reference.resolve()),
                 '--candidate', str(candidate), '--headless'], experiment='EXP-0007', output=output / 'policy-demonstration',
                sources=source_files, max_wall_s=120., request=dict(kind='accepted-final-policy-demonstration'))
            from watch_demonstration import launch
            launch(args.config, demonstration, output=output / 'watch', max_wall_s=180.)
        else:
            print('[ATOM PPO MACRO] No accepted final training action to Watch; inspect physical failures.', flush=True)


if __name__ == '__main__':
    main()
