"""Training-only physical supervision, excluded from actor features."""
import math
import numpy as np


class NonTargetContacts:
    def __init__(self, model, robot_geoms, piece_names, selected_piece,
                 topple_angle_rad=math.pi/3):
        self.model = model
        self.robot = set(robot_geoms)
        self.selected = model.body(selected_piece).id
        self.tracked = {model.body(name).id for name in piece_names}
        self.forbidden = self.tracked-{self.selected}
        self.neighbors = sorted(self.forbidden)
        self.cosine_limit = math.cos(topple_angle_rad)
        self.reset()

    def reset(self):
        self.event = None
        self.topple_event = None
        self.step_events = {}
        self.origins = None
        self.peaks_mm = np.zeros(len(self.neighbors))
        self.displacement_delta_mm = 0.

    def start_displacement(self, data):
        self.origins = data.xpos[self.neighbors].copy()

    def begin_step(self):
        self.step_events = {}
        self.displacement_delta_mm = 0.

    def displacements_mm(self):
        return {self.model.body(body).name: float(peak)
                for body, peak in zip(self.neighbors, self.peaks_mm) if peak > 0.}

    def observe(self, data):
        if self.origins is not None:
            distances = 1000*np.linalg.norm(data.xpos[self.neighbors]-self.origins, axis=1)
            # Ignore sub-millimeter settling noise before shaping the reward.
            peaks = np.maximum(self.peaks_mm, distances)
            self.displacement_delta_mm += float(np.sum(
                np.maximum(peaks-.25, 0.)-np.maximum(self.peaks_mm-.25, 0.)))
            self.peaks_mm = peaks
        for contact in data.contact:
            if contact.dist > 0:
                continue
            first, second = int(contact.geom1), int(contact.geom2)
            first_body = int(self.model.geom_bodyid[first])
            second_body = int(self.model.geom_bodyid[second])
            first_active = first in self.robot or first_body == self.selected
            second_active = second in self.robot or second_body == self.selected
            if ((first_body in self.forbidden and second_active)
                    or (second_body in self.forbidden and first_active)):
                record = dict(geoms=[self.model.geom(first).name, self.model.geom(second).name],
                              distance_m=float(contact.dist), time_s=float(data.time))
                self.step_events[tuple(sorted((first, second)))] = record
                if self.event is None:
                    self.event = record
        for body in self.tracked:
            cosine = float(data.xmat[body, 8])
            if cosine < self.cosine_limit and self.topple_event is None:
                self.topple_event = dict(piece=self.model.body(body).name,
                                         angle_rad=math.acos(max(-1., min(1., cosine))),
                                         time_s=float(data.time))
        return self.topple_event is not None

    def check(self, data):
        self.observe(data)
        return self.event is not None
