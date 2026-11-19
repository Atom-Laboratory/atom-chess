"""Bounded orchestration trace, independent of the GUI."""
from collections import deque
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class ModuleEvent:
    timestamp_s: float
    module: str
    status: str
    detail: str


class ModuleMonitor:
    def __init__(self):
        self.events = deque(maxlen=200)
        self.latest = {}
        self.on_event = None

    def emit(self, module, status, detail):
        if status not in ('running', 'completed', 'failed', 'waiting'):
            raise ValueError('Unknown module status')
        event = ModuleEvent(time.monotonic(), module, status, str(detail))
        self.events.append(event)
        self.latest[module] = event
        if self.on_event:
            self.on_event(event)
