"""Responsive Tk preview for a camera capture running on a worker thread."""
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import tkinter as tk

from PIL import Image, ImageTk


def show(run):
    window = tk.Tk()
    window.title('ATOM capture | live RGB and homography')
    status = tk.StringVar(value='Starting camera…')
    panels = []
    for column, title in enumerate(('Camera RGB', 'Rectified board')):
        tk.Label(window, text=title).grid(row=0, column=column)
        panel = tk.Label(window, width=64, height=24, bg='#222222')
        panel.grid(row=1, column=column, sticky='nsew', padx=4)
        panels.append(panel)
    tk.Label(window, textvariable=status, justify='left', anchor='w').grid(
        row=2, column=0, columnspan=2, sticky='ew', padx=4)

    latest = None
    lock = Lock()
    visible = True

    def publish(frame, label):
        nonlocal latest
        with lock:
            if not visible:
                return
        raw = Image.fromarray(frame.raw_rgb).resize((576, 432), Image.Resampling.BILINEAR)
        if frame.oriented and frame.homography is not None:
            board = Image.fromarray(frame.rectified_rgb).resize((432, 432), Image.Resampling.BILINEAR)
            matrix = 'H (image → board)\n' + '\n'.join(
                '   '.join(f'{value: .4g}' for value in row) for row in frame.homography)
        else:
            board = Image.new('RGB', (432, 432), '#222222')
            matrix = 'Homography unavailable — board reference not accepted'
        with lock:
            if visible:
                latest = raw, board, f'Frame {frame.sequence} | {label}\n{matrix}'

    with ThreadPoolExecutor(max_workers=1) as worker:
        job = worker.submit(run, publish)

        def close():
            nonlocal visible, latest
            with lock:
                visible = False
                latest = None
            if job.done():
                window.destroy()
            else:
                window.withdraw()

        def poll():
            nonlocal latest
            with lock:
                update, latest = latest, None
            if update is not None and visible:
                for panel, pixels in zip(panels, update[:2]):
                    panel.photo = ImageTk.PhotoImage(pixels, master=window)
                    panel.configure(image=panel.photo, width=pixels.width, height=pixels.height)
                status.set(update[2])
            if job.done():
                if not visible:
                    window.destroy()
                else:
                    error = job.exception()
                    message = (f'Error: {error}' if error else
                               f'Execution finished (exit {job.result()}). See report.json.')
                    status.set(f'{status.get()}\n{message}')
                return
            window.after(40, poll)

        window.protocol('WM_DELETE_WINDOW', close)
        window.after(0, poll)
        window.mainloop()
        return job.result()
