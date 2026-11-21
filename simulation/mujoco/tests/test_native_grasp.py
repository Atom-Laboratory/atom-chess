"""Opt-in physical regression on a prepared camera/native isolated fixture."""
import importlib.util
import json
import os
from pathlib import Path

import pytest

from atom_mujoco.approach_handoff import approach_handoff
from atom_mujoco.autonomous_scene import AutonomousScene


@pytest.mark.parametrize('seed', [970100, 970101, 970102])
def test_isolated_native_grasp_and_lift_retains_contacts(tmp_path, seed):
    config = os.environ.get('ATOM_NATIVE_GRASP_CONFIG')
    if not config:
        pytest.skip('Set ATOM_NATIVE_GRASP_CONFIG to the qualified experimental solver fixture')
    script = Path(__file__).resolve().parents[1]/'examples/qualify_hybrid_approach/local_diagnostic.py'
    spec = importlib.util.spec_from_file_location('native_grasp_diagnostic', script)
    diagnostic = importlib.util.module_from_spec(spec); spec.loader.exec_module(diagnostic)
    scene = AutonomousScene(Path(config))
    try:
        assert len(scene.sim.manifest['pieces']) == 1, 'This regression is isolated, not crowded qualification'
        scene.reset(seed=seed)
        handoff = {'horizon':64}
        approach_handoff(scene, handoff)
        result = diagnostic.run_local_diagnostic(scene, handoff['plan'], handoff['execution'], tmp_path,
            observer=lambda *args: None, max_decisions=2000, grasp_part='head', closing_load_factor=2.5,
            lift_speed_fraction=.25, target_finger_clearance_m=0., lift_rise_heights=1.5)
        (tmp_path/'report.json').write_text(json.dumps(result, indent=2))
        assert result['status'] == 'SIMULATED_LIFT_DIAGNOSTIC', json.dumps(result)
        assert result['grasp_hold']['confirmed'] and result['grasp_success'] and result['lift_success']
        assert result['measured_lift_m'] >= scene.piece_height
        assert all(result['final_pad_contacts'])
        assert not result['training_eligible'] and not result['visual_grasp_verified']
    finally:
        scene.close()
