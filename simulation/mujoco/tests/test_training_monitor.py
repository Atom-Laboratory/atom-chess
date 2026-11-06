import json
import numpy as np
from atom_mujoco.training_monitor import RunRecorder


def test_run_recorder_persists_episodes_and_atomic_status(tmp_path):
    recorder = RunRecorder(tmp_path)
    recorder.step(1, .5, False, {})
    recorder.step(2, 1., True, dict(success=True, disturbed=False, episode={'r':1.5,'l':2}, terminal_observation=np.zeros((3,96,96),dtype=np.uint8)))
    recorder.step(3, -5., True, dict(success=False, disturbed=True))
    events = [json.loads(line) for line in (tmp_path/'episodes.jsonl').read_text().splitlines()]
    assert [event['episode_return'] for event in events] == [1.5,-5.]
    assert events[0]['success'] and events[1]['disturbed']
    assert 'terminal_observation' not in events[0]
    recorder.progress(3,'stopped')
    state = json.loads((tmp_path/'progress.json').read_text())
    assert state['status']=='stopped' and state['training_success_rate']==.5
    assert not (tmp_path/'progress.tmp').exists()


def test_display_pause_and_stop_state_without_desktop():
    from types import SimpleNamespace
    from atom_mujoco.training_monitor import TrainingDisplay
    labels = []
    display = TrainingDisplay.__new__(TrainingDisplay)
    display.stopped = display.paused = False
    display.pause_button = SimpleNamespace(configure=lambda **kw: labels.append(kw['text']))
    display.toggle_pause()
    assert display.paused and labels[-1]=='Resume training'
    display.toggle_pause()
    assert not display.paused and labels[-1]=='Pause training'
    display.toggle_pause()
    display.stop()
    assert display.stopped and not display.paused
    display.viewer = SimpleNamespace(is_running=lambda:False)
    display.pump()  # Closed viewer requests stop without touching a destroyed UI.
