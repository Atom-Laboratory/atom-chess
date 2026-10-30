"""Opt-in graphics validation for machines with an OpenGL context."""
import os
import mujoco
import numpy as np
import pytest


@pytest.mark.skipif(os.environ.get('ATOM_TEST_RENDER') != '1', reason='Set ATOM_TEST_RENDER=1 on an OpenGL machine')
def test_rendered_arm_changes_when_physics_moves(sim):
    with mujoco.Renderer(sim.model, height=240, width=320) as renderer:
        camera = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(camera)
        camera.lookat[:] = [.15, .08, 0]
        camera.distance, camera.azimuth, camera.elevation = 1.3, 120, -25
        renderer.update_scene(sim.data, camera=camera)
        before = renderer.render().copy()
        for _ in range(150):
            sim.advance([-.6, .15, .6])
        renderer.update_scene(sim.data, camera=camera)
        after = renderer.render().copy()
    assert np.ptp(before) > 0
    # Visible blue model pixels, beyond merely a nonempty floor/background image.
    assert ((before[:,:,2] > before[:,:,0]+30) & (before[:,:,2] > 70)).sum() > 100
    assert np.count_nonzero(np.any(before != after, axis=2)) > 500
