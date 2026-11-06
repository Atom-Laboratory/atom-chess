"""Optional live training UI. Displays pixels without adding oracle policy inputs."""
import json
from pathlib import Path
import time


class RunRecorder:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.episode_return = 0.
        self.episodes = 0
        self.successes = 0

    def step(self, step, reward, done, info):
        self.episode_return += float(reward)
        if done:
            self.episodes += 1
            self.successes += int(info.get('success', False))
            event = {key:info[key] for key in ('success','disturbed','lift_m','held',
                     'bystander_displacement_m','reward_source','stage','episode') if key in info}
            event.update(step=int(step), episode_index=self.episodes,
                         episode_return=self.episode_return)
            with (self.directory/'episodes.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event)+'\n')
            self.episode_return = 0.
        if done or step % 32 == 0:
            self.progress(step, 'training')

    def progress(self, step, status):
        payload = dict(step=int(step), status=status, episodes=self.episodes,
                       training_successes=self.successes,
                       training_success_rate=self.successes/max(1,self.episodes))
        temporary = self.directory/'progress.tmp'
        temporary.write_text(json.dumps(payload,indent=2)+'\n', encoding='utf-8')
        temporary.replace(self.directory/'progress.json')


class TrainingDisplay:
    def __init__(self, env, speed=2., device='unknown'):
        import tkinter as tk
        from PIL import Image, ImageTk
        import mujoco.viewer
        from .controls import clean_view_options
        self.Image, self.ImageTk = Image, ImageTk
        self.env, self.speed, self.device = env, speed, device
        self.episodes = self.successes = 0
        self.stopped = self.paused = False
        self.step = 0
        self.last_frame = 0.
        self.root = tk.Tk()
        self.root.title('ATOM RL — live policy camera')
        self.status = tk.StringVar(value='Preparing training...')
        self.picture = tk.Label(self.root)
        self.picture.pack()
        tk.Label(self.root,textvariable=self.status,justify='left').pack(padx=12,pady=8)
        tk.Label(self.root,text='RGB policy input • oracle reward • simulation only').pack()
        self.pause_button = tk.Button(self.root,text='Pause training',command=self.toggle_pause)
        self.pause_button.pack(fill='x',padx=12,pady=4)
        tk.Button(self.root,text='Stop and save checkpoint',command=self.stop).pack(fill='x',padx=12,pady=4)
        self.root.protocol('WM_DELETE_WINDOW',self.stop)
        self.viewer = mujoco.viewer.launch_passive(env.sim.model,env.sim.data)
        self.viewer.cam.lookat[:] = env.origin+[0,0,.025]
        self.viewer.cam.distance = .55
        self.viewer.cam.elevation = -35
        with self.viewer.lock():
            clean_view_options(self.viewer.opt)
        self.update(env.observation(),dict(stage=env.stage))

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.configure(text='Resume training' if self.paused else 'Pause training')

    def stop(self):
        self.stopped = True
        self.paused = False

    def pump(self):
        if not self.viewer.is_running():
            self.stop()
        if not self.stopped:
            self.root.update_idletasks()
            self.root.update()
            # Do not apply viewer perturbations to the learning environment.
            self.viewer.sync(state_only=True)

    def update(self, obs, info):
        if self.stopped:
            return
        elapsed = time.perf_counter()-self.last_frame
        time.sleep(max(0., self.env.sim.dt*5/self.speed-elapsed))
        self.last_frame = time.perf_counter()
        rgb = obs.transpose(1,2,0)
        self.photo = self.ImageTk.PhotoImage(self.Image.fromarray(rgb).resize((288,288)))
        self.picture.configure(image=self.photo)
        self.status.set(f"Stage: {self.env.stage} | Device: {self.device} | Steps: {self.step}\n"
                        f"Episodes: {self.episodes} | Training successes: {self.successes}\n"
                        f"Lift: {info.get('lift_m',0)*1000:.1f} mm | Grip: {info.get('held',False)}\n"
                        f"Success: {info.get('success',False)} | Disturbed: {info.get('disturbed',False)}")
        self.pump()
        while self.paused and not self.stopped:
            self.pump()
            time.sleep(.03)

    def close(self):
        self.stopped = True
        self.viewer.close()
        self.root.destroy()
