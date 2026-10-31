"""Visible bidirectional controls; simulation and viewer share one locked owner."""
from collections import deque
import time

import mujoco
import numpy as np


def jog(target, lower, upper, index, direction, fraction=.01):
    result = np.array(target, copy=True)
    result[index] = np.clip(result[index] + direction*fraction*(upper[index]-lower[index]),
                            lower[index], upper[index])
    return result


def run_viewer(sim):
    import tkinter as tk
    from tkinter import ttk
    import mujoco.viewer
    panel = tk.Tk()
    panel.title('ATOM controls — experimental physics')
    panel.geometry('580x520')
    requests = deque()
    values = [tk.DoubleVar(value=float(x)) for x in sim.target]
    paused = tk.BooleanVar(value=False)
    closed = False
    def close():
        nonlocal closed
        closed = True
    panel.protocol('WM_DELETE_WINDOW', close)
    ttk.Label(panel, text='Targets: J1/J2 in radians; Z/fingers in metres').pack(pady=8)
    def change(index, sign):
        target = jog([v.get() for v in values], sim.lower, sim.upper, index, sign)
        values[index].set(float(target[index]))
    for i, name in enumerate(sim.names):
        row = ttk.Frame(panel)
        row.pack(fill='x', padx=10, pady=4)
        ttk.Label(row, text=name, width=31).pack(side='left')
        ttk.Button(row, text='−', width=3, command=lambda i=i: change(i, -1)).pack(side='left')
        ttk.Scale(row, from_=float(sim.lower[i]), to=float(sim.upper[i]), variable=values[i]).pack(side='left', fill='x', expand=True)
        ttk.Button(row, text='+', width=3, command=lambda i=i: change(i, 1)).pack(side='left')
    def fingers(value):
        for i in range(3, len(values)):
            values[i].set(float(value))
    if len(values) == 5:
        row = ttk.Frame(panel)
        row.pack(pady=8)
        ttk.Button(row, text='Open gripper [O]', command=lambda: fingers(.02)).pack(side='left')
        ttk.Button(row, text='Close gripper [C]', command=lambda: fingers(-.01)).pack(side='left')
    row = ttk.Frame(panel)
    row.pack(pady=8)
    for label, event in [('Reset [R]', 'R'), ('Hold [Space]', ' '), ('Camera [V]', 'V')]:
        ttk.Button(row, text=label, command=lambda event=event: requests.append(ord(event))).pack(side='left')
    ttk.Checkbutton(panel, text='Pause physics [P]', variable=paused).pack()
    ttk.Label(panel, text='Viewer keys: Q/A first joint • W/S up/down • E/D last arm joint\nO/C open/close • V restore camera • close either window to exit').pack(pady=10)
    status = ttk.Label(panel, text='', wraplength=550)
    status.pack(padx=10, pady=6)
    def set_values(target):
        for var, value in zip(values, target):
            var.set(float(value))
    print('ATOM controls: sliders and +/- move both ways; O/C opens/closes gripper.', flush=True)
    try:
        with mujoco.viewer.launch_passive(sim.model, sim.data,
                                         key_callback=requests.append,
                                         show_left_ui=False, show_right_ui=False) as window:
            def camera():
                settings = sim.manifest['scene']['camera']
                window.cam.lookat[:] = settings['lookat']
                window.cam.distance = settings['distance']
                window.cam.azimuth = settings['azimuth']
                window.cam.elevation = settings['elevation']
            with window.lock():
                camera()
                window.opt.geomgroup[3] = 0
            while window.is_running() and not closed:
                start = time.monotonic()
                panel.update_idletasks()
                panel.update()
                with window.lock():
                    while requests:
                        key = requests.popleft()
                        if key == ord('R'):
                            sim.reset()
                            set_values(sim.target)
                        elif key == 32:
                            set_values(np.clip(sim.data.qpos, sim.lower, sim.upper))
                        elif key == ord('V'):
                            camera()
                        elif key == ord('P'):
                            paused.set(not paused.get())
                        elif key in (ord('O'), ord('C')):
                            fingers(.02 if key == ord('O') else -.01)
                        else:
                            for i, pair in enumerate(('QA', 'WS', 'ED')):
                                if key in map(ord, pair):
                                    change(i, 1 if key == ord(pair[0]) else -1)
                    if not paused.get():
                        sim.advance([value.get() for value in values])
                    state = sim.observe()
                # sync acquires the viewer lock internally; never nest it.
                window.sync()
                contacts = state['contacts']
                status.configure(text=f"Time {state['time_s']:.2f}s | "
                                 f"Position {np.round(state['position'], 3)} | "
                                 f"Contacts {len(contacts) if contacts is not None else 'disabled'}")
                time.sleep(max(0, sim.dt-(time.monotonic()-start)))
    finally:
        panel.destroy()
