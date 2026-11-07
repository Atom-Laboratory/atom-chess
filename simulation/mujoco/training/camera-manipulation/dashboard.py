"""Live Tk dashboard fed by PPO rollout telemetry."""
from collections import deque
import math
import json
from pathlib import Path
import sys
import tkinter as tk


class TrainingDashboard:
    def __init__(self, path):
        self.window = tk.Tk()
        self.window.title('ATOM | PPO live training')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.canvas = tk.Canvas(self.window, width=900, height=625, bg='#121820',
                                highlightthickness=0)
        self.canvas.pack()
        self.closed = False
        self.stream = path.open(encoding='utf-8')
        self.status = 'Waiting for training'
        self.canvas.create_text(24, 605, anchor='nw', tags='status')
        self.reward_history = deque(maxlen=180)
        self.loss_history = {key: deque(maxlen=100) for key in (
            'policy_gradient_loss', 'value_loss', 'entropy_loss', 'loss')}
        self.last_update = None
        self.label(24, 24, self.status)
        self.window.after(100, self.poll)

    def poll(self):
        for _ in range(100):
            offset = self.stream.tell()
            line = self.stream.readline()
            if not line.endswith('\n'):
                self.stream.seek(offset)
                break
            data = json.loads(line)
            if 'status' in data:
                self.status = data['status']
                self.canvas.delete('status')
                self.label(24, 605, self.status, '#8fa4b8', tags='status')
            else:
                self.update(**data)
        self.window.after(100, self.poll)

    def label(self, x, y, text, color='#e5edf5', size=11, tags=()):
        self.canvas.create_text(x, y, anchor='nw', text=text, fill=color,
                                font=('Consolas', size), tags=tags)

    def chart(self, y, label, history, color, height=55):
        self.label(24, y, label)
        if not history:
            self.label(315, y, 'Waiting for samples', '#8fa4b8')
            return
        self.label(315, y, f'Latest {history[-1]:+.5g}', color)
        if len(history) < 2:
            return
        low, high = min(0., min(history)), max(0., max(history))
        span = high-low or 1.
        top = y+19
        zero = top+height*high/span
        self.canvas.create_line(24, zero, 876, zero, fill='#344353', dash=(3, 3))
        points = []
        for index, value in enumerate(history):
            points.extend((24+852*index/(len(history)-1), top+height*(high-value)/span))
        self.canvas.create_line(*points, fill=color, width=2)

    def update(self, step, reward, info, metrics, activation):
        if self.closed:
            return
        if reward is not None and math.isfinite(reward):
            self.reward_history.append(reward)
        update = metrics.get('train/n_updates')
        if update is not None and update != self.last_update:
            self.last_update = update
            for key, history in self.loss_history.items():
                value = metrics.get('train/'+key)
                if value is not None and math.isfinite(value):
                    history.append(float(value))
        self.canvas.delete('all')
        self.label(24, 14, f'PPO step {step:,}  |  {info.get("phase", "-")}  |  target {info.get("target") or "-"}', size=15)
        self.label(24, 43, 'Policy graph | grouped forward activations (RMS)')
        positions = {'Input': (28, 99), 'Features': (195, 99), 'Actor': (370, 70),
                     'Critic': (370, 128), 'Action': (545, 70), 'Value': (545, 128)}
        edges = [('Input', 'Features'), ('Features', 'Actor'), ('Features', 'Critic'),
                 ('Actor', 'Action'), ('Critic', 'Value')]
        for start, end in edges:
            x, y = positions[start]
            end_x, end_y = positions[end]
            self.canvas.create_line(x+140, y+20, end_x, end_y+20, arrow='last', fill='#5bbfba', width=2)
        for name, (x, y) in positions.items():
            rms = activation.get(name)
            activity = 0 if rms is None or not math.isfinite(rms) else min(1., rms)
            color = f'#204{int(5+activity*10):x}58'
            self.canvas.create_rectangle(x, y, x+140, y+42, fill=color, outline='#70b8c0')
            self.label(x+7, y+3, 'RGB + task' if name == 'Input' else name)
            if rms is not None:
                self.label(x+7, y+21, f'{rms:.3f}', '#b6e4e4')
        components = info.get('reward_components') or {}
        penalties = [(key, value) for key, value in components.items() if value < 0]
        bonuses = [(key, value) for key, value in components.items() if value > 0]
        self.label(24, 182, 'Penalties: '+('  '.join(f'{k} {v:+.3g}' for k, v in penalties) or 'none'), '#ff9d98')
        self.label(24, 201, 'Bonuses: '+('  '.join(f'{k} {v:+.3g}' for k, v in bonuses) or 'none'), '#8ddcb1')
        self.label(24, 220, f'Failure: {info.get("failure") or "-"}  |  contact intervals: {info.get("contact_steps") or 0}')
        self.chart(245, 'Step reward', self.reward_history, '#8ddcb1', height=56)
        for index, (key, history) in enumerate(self.loss_history.items()):
            self.chart(328+index*70, key, history, '#edc480', height=43)
        self.label(24, 605, self.status, '#8fa4b8', tags='status')

    def close(self):
        if not self.closed:
            self.closed = True
            self.stream.close()
            self.window.destroy()


if __name__ == '__main__':
    TrainingDashboard(Path(sys.argv[1])).window.mainloop()
