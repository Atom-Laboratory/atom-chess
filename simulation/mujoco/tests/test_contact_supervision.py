import mujoco
import pytest

from atom_mujoco.contact_supervision import NonTargetContacts


def model_for_contacts(robot_x, selected_x, neighbor_x):
    model = mujoco.MjModel.from_xml_string(f"""
    <mujoco><option gravity="0 0 0"/>
      <worldbody>
        <body name="robot" pos="{robot_x} 0 0">
          <joint type="slide" axis="1 0 0"/>
          <geom name="robot_geom" type="sphere" size=".01"/>
        </body>
        <body name="selected" pos="{selected_x} 0 0">
          <freejoint/><geom name="selected_geom" type="sphere" size=".01"/>
        </body>
        <body name="neighbor" pos="{neighbor_x} 0 0">
          <freejoint/>
          <geom name="neighbor_geom" type="sphere" size=".01"/>
        </body>
      </worldbody>
    </mujoco>""")
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return model, data


@pytest.mark.parametrize('positions,forbidden', [
    ((0., 1., .015), True),
    ((0., .015, 1.), False),
    ((1., 0., .015), True),
])
def test_non_target_contacts_include_carried_piece_and_allow_target(positions, forbidden):
    model, data = model_for_contacts(*positions)
    guard = NonTargetContacts(model, [model.geom('robot_geom').id],
                              ['selected', 'neighbor'], 'selected')
    assert guard.check(data) is forbidden
    if forbidden:
        assert guard.event['distance_m'] <= 0
        guard.reset()
        assert guard.event is None


def test_substep_stop_returns_before_full_control_interval(sim):
    calls = []

    def stop():
        calls.append(float(sim.data.time))
        return len(calls) == 2

    start = sim.data.time
    sim.advance(sim.target, stop_when=stop)
    assert len(calls) == 2
    assert sim.data.time-start == pytest.approx(2*sim.model.opt.timestep)

def test_contact_observation_continues_until_toppling():
    model, data = model_for_contacts(0., 1., .015)
    guard = NonTargetContacts(model, [model.geom('robot_geom').id],
                              ['selected', 'neighbor'], 'selected')
    assert guard.observe(data) is False
    assert guard.event is not None
    selected = model.body('selected').id
    address = model.jnt_qposadr[model.body_jntadr[selected]]
    data.qpos[address+3:address+7] = [2**-.5, 2**-.5, 0., 0.]
    mujoco.mj_forward(model, data)
    assert guard.observe(data) is True
    assert guard.topple_event['piece'] == 'selected'


def test_neighbor_displacement_charges_only_new_excursions_and_excludes_target():
    model, data = model_for_contacts(0., 1., 2.)
    guard = NonTargetContacts(model, [model.geom('robot_geom').id],
                              ['selected', 'neighbor'], 'selected')
    guard.start_displacement(data)
    selected, neighbor = (model.jnt_qposadr[model.body_jntadr[model.body(name).id]]
                          for name in ('selected', 'neighbor'))
    data.qpos[selected] += .010
    data.qpos[neighbor] += .002
    mujoco.mj_forward(model, data)
    assert not guard.observe(data)
    assert guard.displacement_delta_mm == pytest.approx(1.75)
    guard.begin_step()
    data.qpos[neighbor] -= .001
    mujoco.mj_forward(model, data)
    guard.observe(data)
    assert guard.displacement_delta_mm == 0.
    data.qpos[neighbor] += .002
    mujoco.mj_forward(model, data)
    guard.observe(data)
    assert guard.displacement_delta_mm == pytest.approx(1.)
    assert guard.displacements_mm() == {'neighbor': pytest.approx(3.)}
