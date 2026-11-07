# P028 — Parallel PPO collection

Run independent MuJoCo environments in spawned processes and collect their
transitions into a shared PPO rollout. Keep separate episode accounting per
worker. The optional display mirrors worker zero in the parent process.
Compare throughput with one worker before choosing a larger worker count.
Multiple independent PPO runs remain useful for seed comparisons.
