"""Bounded latest-frame viewer for actual simulation state and actor RGB."""
from pathlib import Path
import subprocess
import sys
import time

import mujoco
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from atom_mujoco.virtual_camera import make_camera


class NativeWatch:
    """Use MuJoCo's display loop with a private copy of the training state."""

    def __init__(self, env, *, show_colliders=False):
        from mujoco import viewer

        self.env = env
        self.data = mujoco.MjData(env.sim.model)
        self.handle = viewer.launch_passive(env.sim.model, self.data,
                                            show_left_ui=False, show_right_ui=False)
        self.last = 0.
        self.trail = []
        self.step, self.total, self.episode = 0, 0, 1
        self.stage = 'PREPARING'
        with self.handle.lock():
            self.handle.cam.lookat[:] = env.base.camera.lookat
            self.handle.cam.distance = .7
            self.handle.cam.elevation = -40.
            self.handle.cam.azimuth = 135.
            self.handle.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
            self.handle.opt.geomgroup[3] = show_colliders

    def update(self, info, *, force=False):
        now = time.monotonic()
        if not self.handle.is_running() or (not force and now-self.last < 1/30):
            return
        self.last = now
        with self.handle.lock():
            mujoco.mj_copyData(self.data, self.env.sim.model, self.env.sim.data)
        threshold = 1000*self.env.feedback.reach_threshold
        step = self.env.steps if self.stage == 'EVALUATION' else self.step
        total = self.env.horizon if self.stage == 'EVALUATION' else self.total
        label = (f'{self.stage} / {self.env.objective.upper()} | Episode {self.episode} | '
                 f'{step}/{total} decisions')
        status = info.get('validation', {}).get('status', '')
        failure = info.get('failure') or ''
        gap = info.get('pad_distance_m', self.env.last_info.get('pad_distance_m'))
        gap_text = f'{1000*gap:.1f}' if gap is not None else '?'
        result = 'GOAL REACHED' if info.get('success') else failure or 'IN PROGRESS'
        self.handle.set_texts((mujoco.mjtFontScale.mjFONTSCALE_100,
                               mujoco.mjtGridPos.mjGRID_TOPLEFT, label,
                               f'{result} | {status} | Return {self.env.episode_return:.2f}\n'
                               f'Pad gap {gap_text} mm | Reach threshold {threshold:.1f} mm\n'
                               f'Bilateral grip {info.get("bilateral_contact", False)} | '
                               f'Lifted {info.get("lifted", False)}'))
        self.handle.sync(state_only=True)

    def wait_until_closed(self):
        while self.handle.is_running():
            time.sleep(.1)

    def close(self):
        self.handle.close()


def display(path):
    import tkinter as tk
    from PIL import ImageTk

    window = tk.Tk()
    window.title(f'ATOM autonomous manipulation | {path.parent.name}')
    for column, title in enumerate(('MuJoCo actual state', 'Actor RGB', 'AC:Vision rectified board')):
        tk.Label(window, text=title).grid(row=0, column=column, padx=8)
    panel = tk.Label(window, background='#192331')
    panel.grid(row=1, column=0, columnspan=3)
    status = tk.Label(window, justify='left', anchor='w', font=('Consolas', 10))
    status.grid(row=2, column=0, columnspan=3, sticky='ew', padx=10, pady=10)

    modified = 0

    def poll():
        nonlocal modified
        try:
            stamp = path.stat().st_mtime_ns
            if stamp != modified:
                with Image.open(path) as frame:
                    panel.photo = ImageTk.PhotoImage(frame.copy(), master=window)
                    status.configure(text=frame.info.get('status', ''))
                panel.configure(image=panel.photo)
                modified = stamp
        except (FileNotFoundError, PermissionError):
            pass
        window.after(60, poll)

    window.after(0, poll)
    window.mainloop()


class Watch:
    def __init__(self, env, output, *, show_colliders=False):
        self.env = env
        self.path = output/'watch-latest.png'
        self.temporary = output/'watch-next.png'
        self.renderer = mujoco.Renderer(env.sim.model, height=360, width=480)
        try:
            self.process = subprocess.Popen(
                [sys.executable, '-B', str(Path(__file__).resolve()), str(self.path.resolve())],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            self.renderer.close()
            raise
        settings = dict(env.base.config['camera'])
        settings.update(distance=.7, elevation=-40., azimuth=135.)
        self.camera = make_camera(settings)
        self.option = mujoco.MjvOption()
        self.option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
        if show_colliders:
            self.option.geomgroup[3] = 1
        self.last = 0.
        self.trail = []
        self.step, self.total, self.episode = 0, 0, 1
        self.latest_text = 'Starting'

    def update(self, info, *, force=False):
        now = time.monotonic()
        if self.process.poll() is not None or not force and now-self.last < .2:
            return
        self.last = now
        self.trail = (self.trail+info.get('executed_path', [])[-1:])[-128:]
        self.renderer.update_scene(self.env.sim.data, camera=self.camera, scene_option=self.option)
        scene = self.renderer.scene
        for point in self.trail:
            if scene.ngeom >= scene.maxgeom:
                break
            mujoco.mjv_initGeom(scene.geoms[scene.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE,
                               np.repeat(self.env.base.piece_height/30, 3), np.asarray(point),
                               np.eye(3).reshape(-1), np.array([.1, .9, .9, .8]))
            scene.ngeom += 1
        state = self.renderer.render().copy()
        frame = self.env.last_frame
        raw = Image.fromarray(frame.raw_rgb).resize((480, 360))
        board = Image.fromarray(frame.rectified_rgb).resize((360, 360))
        text = (f'Episode {self.episode} | {self.step}/{self.total} decisions | '
                f'{info.get("phase", "FREE_MOTION")} | actor frame {frame.sequence}\n'
                f'Choice {info.get("choice", {})}\nValidation {info.get("validation", {})}\n'
                f'Return {self.env.episode_return:.3f} | '
                f'Physical result {info.get("success")} | failure {info.get("failure")}\n'
                f'Reward {info.get("reward_components", {})}\n'
                f'Contact {info.get("forbidden_contact") or info.get("unexpected_contact")} | '
                f'visual lift {info.get("visual_lift_confirmed")}\n'
                'Cyan trail: measured executed TCP. Rejected targets do not move the rendered robot.')
        self.latest_text = text
        image = Image.new('RGB', (1320, 360))
        image.paste(Image.fromarray(state), (0, 0))
        image.paste(raw, (480, 0))
        image.paste(board, (960, 0))
        metadata = PngInfo()
        metadata.add_text('status', text)
        image.save(self.temporary, pnginfo=metadata, compress_level=1)
        try:
            self.temporary.replace(self.path)
        except PermissionError:
            # The Windows reader may briefly hold the previous snapshot open.
            pass

    def close(self):
        self.renderer.close()


if __name__ == '__main__':
    display(Path(sys.argv[1]))
