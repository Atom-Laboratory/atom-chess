# S026 — Normalize visual features before actor and critic fusion

## Context

The version 3 watched pilot completed 1,024 decisions. Its final evaluation
had two reach successes in four episodes, with no bilateral grip or lift.
Recorded CNN projection RMS increased from about 3.9 to 11.9. The first actor
and critic tanh layers reached RMS near 1.0, while explained variance stayed
near zero. This is measured activation saturation, alongside failed tasks.
Four episodes do not establish a reliable improvement over the initial
one-in-four reach evaluation.

## Decision

Append LayerNorm to the existing SB3 image extractor before concatenation
with normalized host/task inputs. Normalize image feature scale before
fusion, use the existing actor/critic implementation and expose normalization
in the actual dashboard graph. Track a separate policy version. Older policy
archives remain usable with their original architecture and cannot silently
initialize this architecture through the new runner.

Use the original 0.0003 learning rate as the next controlled baseline,
with a configurable target KL of 0.03 limiting PPO policy changes. Preserve
the failed 0.001 pilot and its metrics. Compare fresh and trained versions
on the same held-out seeds before considering extended training.

Make the Watch display the objective, approach threshold, grip/lift evidence
and explicit reached/failed outcome. A reach event must not appear as a
successful pickup. Grasp and lift remain separate qualifications.

## Alternatives

More updates at the measured saturated activations leave the numerical
problem unaddressed. Changing the learning algorithm and environment together
would obscure the effect of this correction. Removing the camera would
change the deployment observation contract.

## Consequences

LayerNorm changes the actor architecture and checkpoint keys, requiring a
fresh initial policy for this comparison. Test normalized feature statistics,
finite gradients and state-dependent critic outputs. Actual manipulation
improvement still requires held-out simulation results.

## Execution boundary regression

The first normalized run stopped at decision 228 with a joint-limit exception
while executing an interpolated command. Its exact rejected command was not
persisted, so the numerical cause remains a diagnosis to validate. The old expression reproduces
floating-point overshoot for legal endpoints, such as 2.0000000000000004
against a 2.0 upper limit. Interpolate using nonnegative endpoint weights
and constrain arithmetic rounding to those validated endpoints. Joint limits
and endpoint validation stay strict. Test all control interval counts and
both bounds. Persist the pending action and interpolation interval with
failure tracebacks for future diagnosis. Preserve the interrupted run and
verified recovery weights.
