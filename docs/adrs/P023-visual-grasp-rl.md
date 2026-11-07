# P023 — Experimental visual grasp learning

Train PPO with SB3 CnnPolicy on a local pawn lift task. The policy receives only
96x96 RGB pixels. Four actions are bounded joint-reference increments for J1,
Z, J2 and the coupled fingers. The existing MotionController and Simulation
validate targets and rate-limit actuators. Reset uses the legacy IK solely to
stage a randomized approach near the E2 pawn. No IK runs during learned steps.
The episode has a 100-step horizon at 5 control intervals per action.
Reward and evaluation use simulation oracle distance, bilateral contact, lift
and bystander displacement. Oracle values are not policy inputs. This first
curriculum does not complete a chess transfer or qualify deployment. The model
uses fingertip-only contact geometry. Report success on held-out seeds separately
from rollout reward. Store model, config and evaluation in a fresh run directory.
RL is isolated from the main task console until evaluated. No hardware dispatch.

References: the SB3 2.9 custom environment guide specifies Gymnasium reset/step and uint8 RGB image observations. PPO CnnPolicy supplies the image encoder and policy/value networks. https://stable-baselines3.readthedocs.io/en/v2.9.0/guide/custom_env.html

## Context
The user requested actual learning after repeated grasp failures. The existing
deterministic collision preflight is still failing; this experiment does not
waive that requirement for production chess tasks.

## Alternatives
Full-game end-to-end learning was rejected because it obscures manipulation
failures and requires a much larger curriculum. State-vector policy inputs
were rejected for this experiment because the intended observation is camera
RGB. Scripted grasping remains a separate baseline, not a learned policy.

## Consequences
The experiment runs only in an isolated simulation and cannot commit physical
board state or dispatch hardware. Simulator oracle rewards do not establish
acvision integration. A 2048-step trial scored 0/5 lifts and disturbed bystanders
in every evaluation. Deployment remains disabled pending successful evaluation.
