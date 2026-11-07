"""Live or replayed PPO dashboard in its own Tk process."""
from collections import deque
import json
import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

from run_progress import progress_text


BG, PANEL, TEXT, MUTED = '#101823', '#182435', '#ecf4fc', '#a9bfd4'
GRID, ACCENT = '#344961', '#65e3cb'
LOSSES = (
    ('loss', 'Total PPO loss', 'Combined objective · last minibatch', '#f2b769', 1.),
    ('policy_gradient_loss', 'Policy loss', 'Clipped policy objective · mean', '#7fdcff', .001),
    ('value_loss', 'Value loss', 'Critic return prediction error · mean', '#c1a6ff', 1.),
    ('entropy_loss', 'Entropy loss', 'Negative policy entropy · mean', '#77e4af', 1.),
)
DIAGNOSTICS = (
    ('train/approx_kl', 'Approx. KL'), ('train/clip_fraction', 'Clipped fraction'),
    ('train/explained_variance', 'Explained variance'), ('train/std', 'Action σ'),
    ('train/learning_rate', 'Learning rate'), ('train/clip_range', 'Clip range'),
    ('rollout/ep_rew_mean', 'Mean episode return'), ('rollout/ep_len_mean', 'Mean episode length'),
    ('time/fps', 'Steps / second'),
)


def number(value):
    return '—' if value is None else f'{value:.5g}'


class TrainingDashboard:
    def __init__(self, path):
        self.window = tk.Tk()
        self.window.title('ATOM | PPO training')
        self.window.geometry('1160x790')
        self.window.minsize(1050, 730)
        self.window.configure(background=BG)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.stream = path.open(encoding='utf-8')
        self.status = 'Waiting for training'
        self.progress = None
        self.training_progress = None
        self.step = 0
        self.info = {}
        self.graph = []
        self.parameters = None
        self.activation = {}
        self.selected = None
        self.metrics = {}
        self.last_update = None
        self.update_step = None
        self.loss_history = {key: deque(maxlen=240) for key, *_ in LOSSES}
        self.reward_history = deque(maxlen=360)
        self.header = tk.Label(self.window, bg=BG, fg=TEXT, font=('Segoe UI', 16, 'bold'),
                               anchor='w', padx=16, pady=6)
        self.header.pack(fill='x')
        self.stage_detail = tk.Label(self.window, bg=BG, fg=MUTED, anchor='w', padx=16)
        self.stage_bar = ttk.Progressbar(self.window, mode='determinate')
        self.tabs = ttk.Notebook(self.window)
        self.tabs.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.loss = self.make_tab('PPO losses')
        self.network = self.make_tab('Policy network')
        self.network.bind('<Button-1>', self.select_layer)
        self.reward = self.make_tab('Reward')
        self.signed_log = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.loss, text='Signed-log axes', variable=self.signed_log,
                        command=self.draw).place(relx=1., x=-17, y=10, anchor='ne')
        self.tabs.bind('<<NotebookTabChanged>>', self.draw)
        self.poll_timer = self.window.after(100, self.poll)

    def make_tab(self, name):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text=name)
        canvas = tk.Canvas(tab, bg=BG, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        canvas.bind('<Configure>', self.draw)
        return canvas

    def poll(self):
        changed = False
        for _ in range(300):
            offset = self.stream.tell()
            line = self.stream.readline()
            if not line.endswith('\n'):
                self.stream.seek(offset)
                break
            self.ingest(json.loads(line))
            changed = True
        if changed:
            self.draw()
        self.poll_timer = self.window.after(100, self.poll)

    def ingest(self, data):
        if 'status' in data:
            self.status = data['status']
        if 'progress' in data:
            self.progress = data['progress']
            if self.progress['unit'] == 'steps':
                self.training_progress = self.progress
        if 'graph' in data:
            self.graph = data['graph']
            self.parameters = data.get('trainable_parameters')
        if 'update' in data:
            self.optimization(**data['update'])
        if 'step' in data:
            self.step = data['step']
            self.info = data['info']
            self.activation = data['activation']
            if data['reward'] is not None:
                self.reward_history.append((self.step, data['reward']))
            if 'metrics' in data:  # Replay older dashboard logs.
                self.optimization(self.step, data['metrics'])

    def optimization(self, step, metrics):
        count = metrics.get('train/n_updates')
        if count is None or count == self.last_update:
            return
        self.last_update = int(count)
        self.update_step = step
        self.metrics = metrics
        for key, history in self.loss_history.items():
            value = metrics.get('train/'+key)
            if value is not None:
                ema = .2*value+.8*history[-1][2] if history else value
                history.append((step, value, ema))

    @staticmethod
    def label(canvas, x, y, text, color=TEXT, size=10, weight='normal', **kwargs):
        canvas.create_text(x, y, anchor='nw', text=text, fill=color,
                           font=('Segoe UI', size, weight), **kwargs)

    def draw(self, _event=None):
        canvas = self.tabs.nametowidget(self.tabs.select()).winfo_children()[0]
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 2 or height < 2:
            return
        self.draw_progress()
        canvas.delete('all')
        if canvas is self.loss:
            self.draw_losses(width, height)
        elif canvas is self.network:
            self.draw_network(width, height)
        else:
            self.draw_reward(width, height)

    def draw_progress(self):
        if self.progress is None:
            self.header.configure(text=f'ATOM / PPO    ·    Step {self.step:,}    ·    {self.status}')
            return
        self.header.configure(text=f'ATOM / PPO    ·    {progress_text(self.progress)}')
        detail = self.progress['detail']
        if self.progress['unit'] != 'steps' and self.training_progress is not None:
            training = progress_text(self.training_progress)
            detail = f'{training}    ·    {detail}' if detail else training
        if detail:
            self.stage_detail.configure(text=detail)
            if not self.stage_detail.winfo_manager():
                self.stage_detail.pack(fill='x', before=self.tabs)
        else:
            self.stage_detail.pack_forget()
        total = self.progress['total']
        if total is None:
            self.stage_bar.pack_forget()
        else:
            self.stage_bar.configure(maximum=total, value=self.progress['completed'])
            if not self.stage_bar.winfo_manager():
                self.stage_bar.pack(fill='x', padx=16, pady=(3, 6), before=self.tabs)

    def chart(self, canvas, x, y, width, height, title, subtitle, history, color,
              threshold=None, *, show_ema=True):
        canvas.create_rectangle(x, y, x+width, y+height, fill=PANEL, outline=GRID)
        self.label(canvas, x+12, y+7, title, size=12, weight='bold')
        self.label(canvas, x+12, y+29, subtitle, MUTED)
        if not history:
            self.label(canvas, x+12, y+58, 'Waiting for samples', MUTED)
            return
        steps, raw, smooth = zip(*history)
        summary = f'Latest {number(raw[-1])}'
        if show_ema:
            summary += f'    EMA {number(smooth[-1])}'
        summary += f'    Range {number(min(raw))} … {number(max(raw))}'
        self.label(canvas, x+12, y+50, summary, color, size=9)
        left, right = x+79, x+width-18
        top, bottom = y+78, y+height-33

        def transform(value):
            return math.copysign(math.log1p(abs(value)/threshold), value) if threshold else value

        values = tuple(map(transform, (*raw, *smooth)))
        low, high = min(values), max(values)
        pad = (high-low)*.08 or max(abs(high)*.03, 1e-5)
        low, high = low-pad, high+pad
        first, last = steps[0], steps[-1]

        def position(step, value):
            return (left+(right-left)*(step-first)/max(1, last-first),
                    top+(bottom-top)*(high-transform(value))/(high-low))

        for fraction in (0., .5, 1.):
            tick = high-fraction*(high-low)
            value = math.copysign(threshold*math.expm1(abs(tick)), tick) if threshold else tick
            yy = top+fraction*(bottom-top)
            canvas.create_line(left, yy, right, yy, fill=GRID)
            self.label(canvas, x+9, yy-8, f'{value:.3g}', MUTED, size=8)
        if low < 0 < high:
            yy = position(first, 0)[1]
            canvas.create_line(left, yy, right, yy, fill=MUTED, dash=(3, 5))
        self.label(canvas, left, bottom+6, f'{first:,}', MUTED, size=8)
        self.label(canvas, (left+right)/2-37, bottom+6, 'Training step', MUTED, size=8)
        if last > first:
            canvas.create_text(right, bottom+6, text=f'{last:,}', anchor='ne', fill=MUTED)
            canvas.create_line(*(point for pair in zip(steps, raw) for point in position(*pair)),
                               fill=MUTED if show_ema else color)
            if show_ema:
                canvas.create_line(*(point for pair in zip(steps, smooth) for point in position(*pair)),
                                   fill=color, width=2)
        px, py = position(last, raw[-1])
        canvas.create_oval(px-3, py-3, px+3, py+3, fill=color, outline='')

    def draw_losses(self, width, height):
        canvas = self.loss
        update = 'Waiting for PPO optimizer' if self.update_step is None else (
            f'Optimizer updates {self.last_update:,}   ·   Metrics at step {self.update_step:,}')
        self.label(canvas, 16, 11, update, size=13, weight='bold')
        self.label(canvas, 16, 37, 'Thin line: raw value    ·    Colored line: EMA (α = 0.2)    ·    Latest 240 samples', MUTED)
        for index, (key, title) in enumerate(DIAGNOSTICS):
            column, row = index%5, index//5
            self.label(canvas, 16+column*(width-32)/5, 63+row*24,
                       f'{title}  {number(self.metrics.get(key))}', MUTED, size=9)
        card_width, card_height = (width-48)/2, (height-148)/2
        for index, (key, name, detail, color, threshold) in enumerate(LOSSES):
            x = 16+index%2*(card_width+16)
            y = 119+index//2*(card_height+13)
            self.chart(canvas, x, y, card_width, card_height, name, detail,
                       self.loss_history[key], color, threshold if self.signed_log.get() else None)

    def draw_network(self, width, height):
        canvas = self.network
        self.label(canvas, 16, 12, 'Policy forward pass', size=14, weight='bold')
        detail = (f'{self.parameters:,} trainable parameters · including action log σ   |   '
                  'Click a layer for output statistics. Bars show nonzero activation.'
                  if self.parameters is not None else 'Layer data becomes available when the policy is attached.')
        self.label(canvas, 16, 41, detail, MUTED)
        if not self.graph:
            if self.activation:
                values = '   ·   '.join(f'{name} RMS {number(value)}'
                                        for name, value in self.activation.items())
                self.label(canvas, 16, 81, 'Recorded summary from an earlier dashboard', ACCENT)
                self.label(canvas, 16, 106, values, width=width-32)
            return
        spacing = (width-32)/5
        box_width, box_height = spacing-22, 52
        columns = [[node for node in self.graph if node['column'] == column] for column in range(5)]
        positions = {}
        for column, nodes in enumerate(columns):
            self.label(canvas, 16+column*spacing, 75,
                       ('OBSERVATION', 'IMAGE ENCODER', 'FUSION', 'ACTOR / CRITIC', 'HEADS')[column], MUTED)
            for index, node in enumerate(nodes):
                center = 110+(height-220)*(index+.5)/len(nodes)
                positions[node['id']] = (16+column*spacing, center-box_height/2)
        for node in self.graph:
            x, y = positions[node['id']]
            for parent in node['parents']:
                px, py = positions[parent]
                line = ACCENT if self.selected in (parent, node['id']) else GRID
                if px == x:
                    canvas.create_line(px+box_width/2, py+box_height, x+box_width/2, y,
                                       arrow='last', fill=line, width=2)
                else:
                    canvas.create_line(px+box_width, py+box_height/2, x, y+box_height/2,
                                       arrow='last', fill=line, width=2)
        for node in self.graph:
            key = node['id']
            x, y = positions[key]
            sample = self.activation.get(key, {})
            tag = 'node-'+key
            canvas.create_rectangle(x, y, x+box_width, y+box_height, fill=PANEL,
                                    outline=ACCENT if self.selected == key else GRID,
                                    tags=tag)
            self.label(canvas, x+8, y+4, node['label'], weight='bold', tags=tag)
            value = f'RMS {number(sample["rms"])}   ·   {sample["active"]:.0%} active' if sample else node['detail']
            self.label(canvas, x+8, y+24, value, MUTED, size=9, tags=tag)
            if sample and sample['active']:
                canvas.create_rectangle(x+1, y+box_height-4, x+(box_width-1)*sample['active'],
                                        y+box_height-1, fill=ACCENT, outline='', tags=tag)
        node = next((node for node in self.graph if node['id'] == self.selected), self.graph[0])
        sample = self.activation.get(node['id'], {})
        shape = ' × '.join(map(str, sample.get('shape', ()))) or '—'
        self.label(canvas, 16, height-84, f'{node["label"]}  ·  {node["detail"]}', ACCENT, size=12)
        self.label(canvas, 16, height-56,
                   f'Output shape {shape}    |    Parameters {node["parameters"]:,}    |    '
                   f'RMS {number(sample.get("rms"))}    |    Peak |x| {number(sample.get("peak"))}',
                   MUTED)

    def select_layer(self, _event):
        for tag in self.network.gettags('current'):
            if tag.startswith('node-'):
                self.selected = tag.removeprefix('node-')
                self.draw()
                break

    def draw_reward(self, width, height):
        canvas, info = self.reward, self.info
        title = f'{info.get("phase") or "Waiting"}  ·  Target {info.get("target") or "—"}  ·  Episode step {info.get("episode_steps") or "—"}'
        self.label(canvas, 16, 12, title, size=13, weight='bold')
        self.label(canvas, 16, 38, f'Failure: {info.get("failure") or "—"}   ·   Contact intervals: {info.get("contact_steps") or 0}   ·   Toppled: {"yes" if info.get("topple_event") else "no"}', MUTED)
        reward = [(step, value, value) for step, value in self.reward_history]
        self.chart(canvas, 16, 72, width-32, max(180, height//2-60), 'Step reward',
                   'Sampled environment reward before PPO timeout bootstrapping', reward, ACCENT,
                   show_ema=False)
        top = max(282, height//2+27)
        for index, (key, name) in enumerate((('reward_components', 'Current step'),
                                            ('episode_reward_components', 'Episode totals'))):
            x = 16+index*(width/2)
            self.label(canvas, x, top, name, size=12, weight='bold')
            components = info.get(key) or {}
            for row, (name, value) in enumerate(sorted(components.items(), key=lambda item: -abs(item[1]))):
                self.label(canvas, x, top+25+row*18, f'{name.replace("_", " ")}   {value:+.5g}',
                           ACCENT if value >= 0 else '#ff9d98', size=9)

    def close(self):
        self.window.after_cancel(self.poll_timer)
        self.stream.close()
        self.window.destroy()


if __name__ == '__main__':
    TrainingDashboard(Path(sys.argv[1])).window.mainloop()
