"""Launch ATOM Chess Simulation Playground, or execute a headless task."""
import argparse
import json
import uuid
from pathlib import Path

from atom_mujoco.playground import Playground


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
    args = parser.parse_args()
    playground = Playground(args.bundle, diagnostic_unchecked=args.diagnostic_unchecked)
    if args.headless:
        result = (playground.execute_request(json.loads(args.request.read_text())) if args.request
                  else playground.execute(operation='MOVE', source=args.source,
                                          target=args.target, controller=args.controller))
        if args.output:
            playground.save(args.output, result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('history','manifest')}, indent=2))
        return
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    import mujoco.viewer
    from atom_mujoco.controls import clean_view_options
    root = tk.Tk()
    root.title('ATOM Chess Simulation Playground')
    source, target = tk.StringVar(value=args.source), tk.StringVar(value=args.target)
    for label, variable, options in [('Source',source,[f+str(r) for r in range(1,9) for f in 'abcdefgh']),
                                     ('Target',target,[f+str(r) for r in range(1,9) for f in 'abcdefgh'])]:
        ttk.Label(root,text=label).pack()
        ttk.Combobox(root,textvariable=variable,values=options,state='readonly',width=40).pack()
    ttk.Label(root,text='Controller: Deterministic Baseline\nTrained RL Policy: unavailable (no validated checkpoint)\n'
              +('DIAGNOSTIC: collision preflight bypassed' if args.diagnostic_unchecked else 'Swept preflight required')).pack(pady=8)
    status = ttk.Label(root,text='Ready. Verification uses simulation oracle, not a camera.',wraplength=500)
    status.pack(padx=12,pady=8)
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
        def render(phase,state):
            with viewer.lock():
                clean_view_options(viewer.opt)
            viewer.sync()
            status.configure(text=f"{phase} | t={state['time_s']:.2f}s | q={state['position'].round(3)}")
            root.update_idletasks()
        playground.on_step=render
        def execute():
            button.configure(state='disabled')
            try:
                result=playground.execute_request(dict(schema=1,operation='MOVE',source=source.get(),target=target.get()))
                output=args.bundle.parent/('playground-'+uuid.uuid4().hex+'.json')
                playground.save(output,result)
                status.configure(text=f"{result['status']}: {result['error_code']}\nSaved {output}")
                with viewer.lock():
                    clean_view_options(viewer.opt)
                viewer.sync()
            finally:
                button.configure(state='normal')
        button=ttk.Button(root,text='Execute MOVE',command=execute)
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
        ttk.Button(root,text='Inspect trajectory / confirmed occupancy',command=inspect).pack(pady=4)
        def load_plan():
            path=filedialog.askopenfilename(title='Load Chess Core request',filetypes=[('JSON requests','*.json')])
            if not path:
                return
            button.configure(state='disabled')
            try:
                result=playground.execute_request(json.loads(Path(path).read_text()))
                output=args.bundle.parent/('playground-'+uuid.uuid4().hex+'.json')
                playground.save(output,result)
                status.configure(text=f"{result['status']}: {result['error_code']}\nSaved {output}")
            except (ValueError,OSError) as error:
                status.configure(text=str(error))
            finally:
                button.configure(state='normal')
        ttk.Button(root,text='Execute Chess Core request file',command=load_plan).pack(pady=4)
        def refresh():
            if not viewer.is_running():
                root.destroy()
                return
            with viewer.lock():
                clean_view_options(viewer.opt)
            viewer.sync()
            root.after(40,refresh)
        root.after(40,refresh)
        root.mainloop()


if __name__ == '__main__':
    main()
