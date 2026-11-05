"""Fixed RGB camera for perception development in the current scene."""
import mujoco


class VirtualCamera:
    def __init__(self, sim):
        self.sim = sim
        self.renderer = mujoco.Renderer(sim.model, height=480, width=640)
        self.camera = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(self.camera)
        self.camera.lookat[:] = sim.manifest['scene']['board_center_m']
        self.camera.distance = 1.05
        self.camera.azimuth = 90
        self.camera.elevation = -90

    def frame(self):
        self.renderer.update_scene(self.sim.data, camera=self.camera)
        return self.renderer.render().copy()

    def close(self):
        self.renderer.close()
