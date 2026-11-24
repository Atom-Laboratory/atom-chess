"""Shared terminal and dashboard progress for a single execution."""
import time


def progress_text(state):
    text = state['stage']
    if state['total'] is not None:
        done, total = state['completed'], state['total']
        text += f' | {done}/{total} {state["unit"]} ({done/total:.1%})'
    return text


class RunProgress:
    def __init__(self):
        self.dashboard = None
        self.state = {}
        self.last_terminal = self.last_dashboard = float('-inf')

    def stage(self, name, *, total=None, unit=None, detail=None):
        self.state = dict(stage=name, completed=0, total=total, unit=unit, detail=detail)
        self.publish(force=True)

    def advance(self, completed, detail=None, *, force=False):
        self.state.update(completed=completed, detail=detail)
        self.publish(force=force)

    def publish(self, *, force=False):
        now = time.monotonic()
        if force or now-self.last_terminal >= 2.:
            detail = self.state['detail']
            suffix = f' | {detail}' if detail else ''
            print(f'[ATOM] {progress_text(self.state)}{suffix}', flush=True)
            self.last_terminal = now
        if self.dashboard is not None and (force or now-self.last_dashboard >= .25):
            self.dashboard.write(progress=self.state.copy())
            self.last_dashboard = now
