"""Launch ATOM Chess Simulation Playground, or execute a headless task."""
import argparse
import json
import uuid
import time
from pathlib import Path

from atom_mujoco.playground import Playground
from atom_mujoco.paths import new_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--source', default='e2')
    parser.add_argument('--target', default='e3')
    parser.add_argument('--request', type=Path, help='Versioned JSON from the Chess Core integration adapter')
    parser.add_argument('--controller', default='baseline')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--diagnostic-unchecked', action='store_true',
                        help='Explicit experimental manipulation without swept preflight; never RL qualification')
    parser.add_argument('--execute-trajectory', type=Path,
                        help='Execute an exported C++ P015 trajectory')
    parser.add_argument('--camera-config', type=Path, help='JSON overrides for the virtual RGB camera')
    parser.add_argument('--session-dir', type=Path, help='Directory for this interactive session')
    args = parser.parse_args()
    session_dir = args.session_dir or new_run('playground/sessions')
    if args.execute_trajectory and (not args.headless or args.request):
        parser.error('--execute-trajectory requires --headless and excludes --request')
    playground = Playground(args.bundle, diagnostic_unchecked=args.diagnostic_unchecked)
    if args.headless:
        if args.execute_trajectory:
            from atom_mujoco.trajectory_execution import execute_trajectory
            try:
                result = execute_trajectory(playground, args.execute_trajectory.read_text(encoding='utf-8-sig'))
            except (ValueError, OSError) as error:
                parser.error(str(error))
        else:
            result = (playground.execute_request(json.loads(args.request.read_text())) if args.request
                  else playground.execute(operation='MOVE', source=args.source,
                                          target=args.target, controller=args.controller))
        if args.output:
            playground.save(args.output, result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('history','manifest')}, indent=2))
        return 1 if args.execute_trajectory and result['status'] == 'FAILED' else 0
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    import mujoco.viewer
    import numpy as np
    from atom_mujoco.controls import clean_view_options
    root = tk.Tk()
    root.title('ATOM Chess Simulation Playground')
    selection_panel = ttk.Frame(root, padding=8)
    selection_panel.pack(side='left', anchor='n')
    controls_panel = ttk.Frame(root, padding=8)
    controls_panel.pack(side='left', anchor='n')
    source, target = tk.StringVar(value=args.source.lower()), tk.StringVar(value=args.target.lower())
    selecting = tk.StringVar(value='source')
    for label in ('Source', 'Target'):
        ttk.Radiobutton(selection_panel, text=label, value=label.lower(), variable=selecting).pack(side='top')
    selection_label = ttk.Label(selection_panel)
    selection_label.pack()
    tiles = {}
    slots = playground.physical.confirmed.graveyard_slots

    def refresh_grid():
        snapshot = playground.physical.confirmed
        occupants = dict(snapshot.occupancy)
        occupants.update({f'graveyard:{p.location.slot}':p.identity for p in snapshot.pieces
                          if p.location.kind == 'graveyard'})
        for endpoint, (tile, label, background) in tiles.items():
            identity = occupants.get(endpoint)
            piece = ''
            if identity:
                color, kind, *_ = identity.split('_')
                piece = f' {color[0].upper()}{("N" if kind == "knight" else kind[0].upper())}'
            selected = '#83d9ff' if endpoint == source.get() else '#ffd77a' if endpoint == target.get() else background
            tile.configure(text=label+piece, background=selected, activebackground=selected)
        selection_label.configure(text=f'Blue source: {source.get()}   |   Gold target: {target.get()}')

    def pick(endpoint):
        if manual_mode.get():
            status.configure(text='Switch off manual control before selecting a chess move.')
            return
        if not endpoint.startswith('graveyard:'):
            identity = playground.physical.confirmed.occupancy[endpoint]
            if identity:
                record = next(p for p in playground.sim.manifest['pieces'] if p['name']==identity)
                side = 'white' if len(playground.chess_history)%2==0 else 'black'
                if record['color']==side:
                    source.set(endpoint)
                    selecting.set('target')
                    refresh_grid()
                    return
        if selecting.get() == 'source':
            source.set(endpoint)
            selecting.set('target')
        else:
            target.set(endpoint)
            selecting.set('source')
        refresh_grid()

    def add_tile(frame, row, col, endpoint, label, background, available=True):
        tile = tk.Button(frame, width=6, foreground='#171717', command=lambda: pick(endpoint),
                         state='normal' if available else 'disabled')
        tile.grid(row=row, column=col)
        tiles[endpoint] = tile, label, background

    board = ttk.LabelFrame(selection_panel, text='Confirmed board')
    board.pack()
    for row, rank in enumerate('87654321'):
        for col, file in enumerate('abcdefgh'):
            square = file+rank
            add_tile(board,row,col,square,square.upper(),'#dfc599' if (row+col)%2==0 else '#ad8862')
    graveyards = ttk.Frame(selection_panel)
    graveyards.pack()
    for color in ('white', 'black'):
        frame = ttk.LabelFrame(graveyards,text=f'{color.title()} Graveyard')
        frame.pack(side='left',padx=3)
        for index in range(16):
            number = f'{index+1:02}'
            slot = f'{color}_{number}'
            rank = ('1' if index < 8 else '2') if color == 'white' else ('8' if index < 8 else '7')
            home = chr(97+index%8)+rank
            add_tile(frame,index//8,index%8,'graveyard:'+slot,home.upper(),'#ddd',slot in slots)
    legacy = sorted(slot for slot in slots if 'graveyard:'+slot not in tiles)
    if legacy:
        frame = ttk.LabelFrame(selection_panel,text='Other configured slots')
        frame.pack()
        for index, slot in enumerate(legacy):
            add_tile(frame,index//8,index%8,'graveyard:'+slot,slot,'#ddd')
    refresh_grid()
    ttk.Label(controls_panel,text='Controller: Deterministic Baseline\nTrained RL Policy: unavailable (no validated checkpoint)\n'
              +('DIAGNOSTIC: collision preflight bypassed' if args.diagnostic_unchecked else 'Swept preflight required')).pack(pady=8)
    status = ttk.Label(controls_panel,text='Ready. Verification uses simulation oracle, not a camera.',wraplength=360)
    status.pack(padx=12,pady=8)
    manual_mode = tk.BooleanVar(value=False)
    manual_pause = tk.BooleanVar(value=False)
    def change_mode():
        try:
            if manual_mode.get():
                playground.manual.enter()
                keyboard.focus_set()
            else:
                playground.manual.leave()
            button.configure(state='disabled' if manual_mode.get() else 'normal')
        except ValueError as error:
            manual_mode.set(playground.manual.active)
            status.configure(text=str(error))
    ttk.Checkbutton(controls_panel,text='Manual control',variable=manual_mode,
                    command=change_mode).pack()
    keyboard = ttk.Button(controls_panel, text='Click here to capture keyboard', takefocus=True,
                          command=lambda: keyboard.focus_set())
    keyboard.pack()
    keyboard.bind('<FocusIn>', lambda event: keyboard.configure(text='Keyboard active'))
    def release_keyboard(event):
        playground.manual.pressed.clear()
        keyboard.configure(text='Click here to capture keyboard')
    keyboard.bind('<FocusOut>', release_keyboard)
    def key_event(event, down):
        key = event.keysym.lower()
        if manual_mode.get() and key in playground.manual.keys:
            playground.manual.key(key, down)
            return 'break'
    keyboard.bind('<KeyPress>',lambda event:key_event(event,True))
    keyboard.bind('<KeyRelease>',lambda event:key_event(event,False))

    jog_panel = ttk.Frame(controls_panel)
    jog_panel.pack()
    def press_jog(key):
        if manual_mode.get():
            keyboard.focus_set()
            playground.manual.key(key, True)
    for row, controls in enumerate((
        (('J1 − (←)', 'left'), ('J1 + (→)', 'right')),
        (('Z down (↓)', 'down'), ('Z up (↑)', 'up')),
        (('J2 − (PgUp)', 'prior'), ('J2 + (PgDn)', 'next')),
        (('Open (O)', 'o'), ('Close (C)', 'c')),
    )):
        for column, (label, key) in enumerate(controls):
            jog_button = ttk.Button(jog_panel, text=label, takefocus=False)
            jog_button.grid(row=row, column=column, sticky='ew')
            jog_button.bind('<ButtonPress-1>', lambda event, k=key: press_jog(k))
            jog_button.bind('<ButtonRelease-1>', lambda event, k=key: playground.manual.key(k, False))
    ttk.Checkbutton(controls_panel,text='Pause manual physics',variable=manual_pause,
                    command=lambda:setattr(playground.manual,'paused',manual_pause.get())).pack()
    def stop_manual():
        playground.manual.stop()
        status.configure(text='Simulation stopped. Explicit reset required; no hardware stop implied.')
    ttk.Button(controls_panel,text='Stop manual simulation',command=stop_manual).pack()
    def reset_experiment():
        if any(op.status in ('pending','executing') for op in playground.physical.operations.values()):
            status.configure(text='Cannot reset an active operation.')
            return
        playground.reset()
        refresh_grid()
        manual_mode.set(False)
        manual_pause.set(False)
        button.configure(state='normal')
        status.configure(text='New experiment initialized. Previous physical scene replaced.')
    ttk.Button(controls_panel,text='Reset experiment to initial scene',command=reset_experiment).pack()
    with mujoco.viewer.launch_passive(playground.sim.model, playground.sim.data,
                                     show_left_ui=False,show_right_ui=False) as viewer:
        original_advance, original_reset = playground.sim.advance, playground.sim.reset
        def locked_advance(*a, **kw):
            with viewer.lock():
                return original_advance(*a, **kw)
        def locked_reset(*a, **kw):
            with viewer.lock():
                return original_reset(*a, **kw)
        playground.sim.advance, playground.sim.reset = locked_advance, locked_reset
        settings=playground.sim.manifest['scene']['camera']
        with viewer.lock():
            viewer.cam.lookat[:]=settings['lookat']
            viewer.cam.distance=settings['distance']
            viewer.cam.azimuth=settings['azimuth']
            viewer.cam.elevation=settings['elevation']
        def sync_view():
            with viewer.lock():
                clean_view_options(viewer.opt)
                scene = viewer.user_scn
                scene.ngeom = 0
                for endpoint, rgba in ((source.get(), [.15,.7,1.,.8]), (target.get(), [1.,.68,.1,.8])):
                    if endpoint not in tiles or (endpoint.startswith('graveyard:') and endpoint[10:] not in slots):
                        continue
                    position = playground.feedback.endpoint_position(endpoint)
                    position[2] += .001
                    mujoco.mjv_initGeom(scene.geoms[scene.ngeom], mujoco.mjtGeom.mjGEOM_BOX,
                                        np.array([.016,.016,.0005]), position, np.eye(3).ravel(),
                                        np.array(rgba,dtype=np.float32))
                    scene.ngeom += 1
            viewer.sync()
        render_clock = [time.perf_counter()]
        display_clock = [0.]
        def render(phase,state):
            elapsed = time.perf_counter() - render_clock[0]
            if elapsed < playground.sim.dt:
                time.sleep(playground.sim.dt - elapsed)
            render_clock[0] = time.perf_counter()
            if time.perf_counter() - display_clock[0] < 1/30:
                return
            display_clock[0] = time.perf_counter()
            sync_view()
            status.configure(text=f"{phase} | t={state['time_s']:.2f}s | q={state['position'].round(3)}")
            root.update_idletasks()
        playground.on_step=render
        def execute():
            button.configure(state='disabled')
            try:
                origin, destination = source.get(), target.get()
                if any(endpoint.startswith('graveyard:') for endpoint in (origin,destination)):
                    request = dict(schema=2,operation='PLAN',transfers=[dict(source=origin,target=destination)])
                else:
                    request = None
                if request is None:
                    from atom_mujoco.chess_commands import execute_chess_move
                    result = execute_chess_move(playground, origin, destination)
                else:
                    result=playground.execute_request(request)
                output=session_dir/('playground-'+uuid.uuid4().hex+'.json')
                session_dir.mkdir(parents=True, exist_ok=True)
                playground.save(output,result)
                status.configure(text=f"{result['status']}: {result['error_code']}\nSaved {output}")
                sync_view()
            except (ValueError,OSError) as error:
                status.configure(text=str(error))
            finally:
                refresh_grid()
                button.configure(state='normal')
        button=ttk.Button(controls_panel,text='Confirm MOVE',command=execute)
        button.pack(pady=8)
        def inspect():
            window=tk.Toplevel(root)
            window.title('Trajectory and physical state')
            text=tk.Text(window,width=110,height=35)
            text.pack(fill='both',expand=True)
            text.insert('end',json.dumps(dict(trajectory=playground.planned_trajectory,
                        occupancy=dict(playground.physical.confirmed.occupancy),
                        revision=playground.physical.confirmed.revision,
                        reconciliation_required=playground.physical.reconciliation_required),indent=2))
            text.configure(state='disabled')
        ttk.Button(controls_panel,text='Inspect trajectory / confirmed occupancy',command=inspect).pack(pady=4)
        def load_plan():
            path=filedialog.askopenfilename(title='Load Chess Core request',filetypes=[('JSON requests','*.json')])
            if not path:
                return
            button.configure(state='disabled')
            try:
                result=playground.execute_request(json.loads(Path(path).read_text()))
                output=session_dir/('playground-'+uuid.uuid4().hex+'.json')
                session_dir.mkdir(parents=True, exist_ok=True)
                playground.save(output,result)
                status.configure(text=f"{result['status']}: {result['error_code']}\nSaved {output}")
            except (ValueError,OSError) as error:
                status.configure(text=str(error))
            finally:
                refresh_grid()
                button.configure(state='disabled' if manual_mode.get() else 'normal')
        ttk.Button(controls_panel,text='Execute Chess Core request file',command=load_plan).pack(pady=4)
        def load_trajectory():
            path = filedialog.askopenfilename(title='Load C++ P015 trajectory',
                                               filetypes=[('JSON trajectory', '*.json')])
            if not path:
                return
            button.configure(state='disabled')
            try:
                from atom_mujoco.trajectory_execution import execute_trajectory
                result = execute_trajectory(playground, Path(path).read_text(encoding='utf-8-sig'))
                output = session_dir / ('p015-' + uuid.uuid4().hex + '.json')
                session_dir.mkdir(parents=True, exist_ok=True)
                playground.save(output, result)
                status.configure(text=f"{result['status']}: {result['error_code']}\nSaved {output}")
            except (ValueError, OSError) as error:
                status.configure(text=str(error))
            finally:
                refresh_grid()
                button.configure(state='disabled' if manual_mode.get() else 'normal')
        ttk.Button(controls_panel, text='Execute C++ trajectory (P015)',
                   command=load_trajectory).pack(pady=4)

        camera_windows = []
        def show_camera():
            from atom_mujoco.virtual_camera import VirtualCamera
            overrides = (json.loads(args.camera_config.read_text(encoding='utf-8-sig'))
                         if args.camera_config else None)
            camera = VirtualCamera(playground.sim, overrides)
            window = tk.Toplevel(root)
            window.title('Virtual RGB camera - perception input, unverified')
            label = ttk.Label(window)
            label.pack()
            entry = [window, camera]
            camera_windows.append(entry)
            def close():
                camera_windows.remove(entry)
                camera.close()
                window.destroy()
            window.protocol('WM_DELETE_WINDOW', close)
            def capture():
                if entry not in camera_windows:
                    return
                rgb = camera.frame()
                ppm = b'P6\n640 480\n255\n'+rgb.tobytes()
                label.image = tk.PhotoImage(data=ppm, format='PPM')
                label.configure(image=label.image)
                window.after(200, capture)
            capture()
        ttk.Button(controls_panel, text='Open virtual RGB camera', command=show_camera).pack(pady=4)
        def refresh():
            if not viewer.is_running():
                root.destroy()
                return
            if playground.manual.active:
                try:
                    state=playground.manual.tick()
                    if state is not None:
                        status.configure(text=f"MANUAL | q={state['position'].round(3)} | "
                            f"reconciliation required | {playground.manual.observation_error or 'observation available'}")
                except (ValueError,RuntimeError) as error:
                    playground.manual.stop()
                    status.configure(text=str(error))
            sync_view()
            root.after(max(1,int(playground.sim.dt*1000)),refresh)
        root.after(40,refresh)
        root.mainloop()


if __name__ == '__main__':
    raise SystemExit(main())
