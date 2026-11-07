# S020 — Separate PPO updates from live rollout samples

## Context

The dashboard previously plotted losses by display sample index and sampled
optimizer metrics through the throttled rollout stream. Its static graph
summarized the actor and critic without showing their actual layers.

## Decision

Publish each optimizer update at its training timestep, including the final
update. Plot raw loss and its exponential moving average on per-metric axes.
Allow a signed-log scale for comparing trends with large outliers. Describe
the instantiated PPO graph and measure activations from sampled forward passes.
Keep rollout rendering and telemetry consumption in separate processes.

## Alternatives

One shared loss axis obscures small losses and hides units. Per-neuron hooks
would make the visualization crowded and add unnecessary runtime overhead.

## Consequences

The graph summarizes actual layer outputs. Each rollout packet carries
sampled activation statistics. Optimizer update packets are independent of
the display refresh rate. The observation, reward, policy and checkpoint
formats are unchanged.
