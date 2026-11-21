import importlib.util
from pathlib import Path

import numpy as np
import pytest


spec=importlib.util.spec_from_file_location('bounded_cem',Path(__file__).resolve().parents[1]/'cem_core.py')
cem=importlib.util.module_from_spec(spec);spec.loader.exec_module(cem)


def test_distribution_bounds_and_rng_checkpoint_reproduce_next_population():
    value=cem.Distribution(123)
    population=value.ask(16)
    assert np.all(population>=cem.LOWER) and np.all(population<=cem.UPPER)
    state=value.state();continued=cem.Distribution(7);continued.restore(state)
    np.testing.assert_array_equal(value.ask(16),continued.ask(16))


def test_physical_constraints_outrank_height_or_reward():
    safe=dict(geometry_valid=True,duration_s=10.,outcome=dict(forbidden_contact=False,success=True,maximum_rise_m=.04))
    bad=dict(geometry_valid=True,duration_s=.1,outcome=dict(forbidden_contact=True,success=False,maximum_rise_m=100.))
    missed=dict(geometry_valid=True,duration_s=1.,outcome=dict(forbidden_contact=False,success=False,maximum_rise_m=.1))
    assert cem.rank(safe)>cem.rank(missed)>cem.rank(bad)
    distribution=cem.Distribution(1);values=distribution.ask(4)
    order=distribution.update(values,[bad,missed,safe,bad])
    assert order[0]==2
    np.testing.assert_array_equal(distribution.best,values[2])


def test_reference_targets_are_bound_to_the_signed_camera_plan(tmp_path):
    import json
    import sys
    from types import SimpleNamespace
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from cem import validated_reference
    from atom_mujoco.approach_planner import plan_identity
    plan=dict(status='PLANNED',model_sha256='test-model',piece='piece',source='e2',source_xy_m=[.1,.2])
    plan['signature']=plan_identity(plan)
    handoff=dict(plan=plan,arrival_perception=dict(source_localized=True))
    reference=dict(lift_success=True,lift_hold=dict(confirmed=True),stages=[dict(name='DESCEND',target=[.1,.2,.04,0.,-.01])])
    (tmp_path/'handoff.json').write_text(json.dumps(handoff))
    (tmp_path/'local-report.json').write_text(json.dumps(reference))
    config=dict(piece='piece',source='e2');sim=SimpleNamespace(manifest=dict(model_sha256='test-model'))
    assert validated_reference(config,sim,tmp_path)==reference
    reference['stages'][0]['target'][0]=.3
    (tmp_path/'local-report.json').write_text(json.dumps(reference))
    with pytest.raises(ValueError,match='camera-derived source'):validated_reference(config,sim,tmp_path)
