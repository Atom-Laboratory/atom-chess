"""Fixed RGB camera for perception development in the current scene."""
import mujoco
from pathlib import Path

DEFAULT_REFERENCE_LAYOUT = Path(__file__).resolve().parents[2] / "configs/perception/h-file-layout.json"


def camera_settings(board_center, overrides=None):
    """Resolve the shared perception camera and an optional experiment override."""
    settings = dict(lookat=list(board_center), distance=1.05, azimuth=180.,
                    elevation=-75., width=1920, height=1440)
    if overrides:
        unknown = overrides.keys() - settings.keys()
        if unknown:
            raise ValueError(f'Unknown camera settings: {sorted(unknown)}')
        settings.update(overrides)
    return settings


def make_camera(settings):
    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(camera)
    camera.lookat[:] = settings['lookat']
    for field in ('distance', 'azimuth', 'elevation'):
        setattr(camera, field, settings[field])
    return camera


def add_camera_override(parser):
    import json
    from pathlib import Path

    parser.add_argument('--camera-config', type=Path,
                        help='JSON file overriding the shared perception camera')

    def resolve(args, board_center):
        overrides = (json.loads(args.camera_config.read_text(encoding='utf-8-sig'))
                     if args.camera_config else None)
        return camera_settings(board_center, overrides)

    return resolve


class VirtualCamera:
    def __init__(self, sim, overrides=None):
        self.sim = sim
        settings = camera_settings(sim.manifest['scene']['board_center_m'], overrides)
        self.renderer = mujoco.Renderer(
            sim.model, height=min(settings['height'], sim.model.vis.global_.offheight),
            width=min(settings['width'], sim.model.vis.global_.offwidth))
        self.camera = make_camera(settings)

    def frame(self):
        self.renderer.update_scene(self.sim.data, camera=self.camera)
        return self.renderer.render().copy()

    def close(self):
        self.renderer.close()
