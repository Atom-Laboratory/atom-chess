"""Privileged training feedback with no access from observation construction."""
import mujoco
import numpy as np

from .scene_feedback import SceneFeedback


class ManipulationFeedback:
    def __init__(self, base):
        self.base = base
        self.sim = base.sim
        self.scene = SceneFeedback(self.sim)
        self.piece = base.config['piece']
        self.body = self.sim.model.body(self.piece).id
        self.pads = [self.sim.model.geom(f'finger_{index}_pad').id for index in (1, 2)]
        self.geoms = [index for index in range(self.sim.model.ngeom)
                      if self.sim.model.geom_bodyid[index] == self.body
                      and self.sim.model.geom_contype[index]]
        reach_squares = float(base.config.get('autonomous', {}).get('reach_distance_squares', 1.))
        if not np.isfinite(reach_squares) or not 0 < reach_squares <= 2:
            raise ValueError('Reach threshold must be within two positive board squares')
        self.reach_threshold = reach_squares*self.sim.manifest['scene']['square_size_m']

    def proximity(self):
        distances = [min(mujoco.mj_geomDistance(self.sim.model, self.sim.data, pad, geom,
                                               self.sim.model.stat.extent*2, None)
                         for geom in self.geoms) for pad in self.pads]
        return -float(np.mean(np.maximum(distances, 0))/self.base.piece_height)

    def reset(self):
        self.origin_z = float(self.sim.data.xpos[self.body, 2])
        self.previous = self.proximity()
        self.initial_distance = -self.previous*self.base.piece_height
        self.best_distance = self.initial_distance
        self.events = set()
        self.hold = 0

    def evaluate(self, action, validation, objective, failure):
        base = self.base
        guard = base.contact_guard
        potential = self.proximity()
        distance = -potential*base.piece_height
        self.best_distance = min(self.best_distance, distance)
        components = dict(time=-.01, motion=-.001*float(np.square(action).sum()),
                          proximity=potential-self.previous)
        self.previous = potential
        if validation['status'] != 'ACCEPTED':
            rejected = validation.get('failure', {})
            depth = max(0., -float(rejected.get('distance_m', 0.)))
            components['rejected_action'] = -1.-min(5., depth/base.piece_height)
        bilateral = self.scene.grip_contacts(self.piece)
        stable = bool(self.scene.settled(self.piece))
        rise = float(self.sim.data.xpos[self.body, 2]-self.origin_z)
        lifted = bool(bilateral and rise > base.piece_height)
        accepted = validation['status'] == 'ACCEPTED'
        self.hold = self.hold+1 if accepted and lifted and stable and not failure else 0
        events = dict(bilateral_contact=bilateral, lifted=lifted)
        weights = dict(bilateral_contact=base.config['reward_weights']['grasp'],
                       lifted=base.config['reward_weights']['lift'])
        for name, occurred in events.items():
            if occurred and name not in self.events:
                components[name] = weights[name]
                self.events.add(name)
        neighbors = guard.displacements_mm()
        peak = max(neighbors.values(), default=0.)
        success = dict(reach=distance <= self.reach_threshold,
                       grasp=bilateral and stable,
                       lift=self.hold >= base.dwell)[objective]
        success = bool(accepted and success and peak <= .25 and not failure)
        if guard.step_events:
            components['non_target_contact'] = -base.contact_penalty
        if guard.displacement_delta_mm:
            components['neighbor_displacement'] = -base.displacement_penalty_per_mm*guard.displacement_delta_mm
        if guard.topple_event:
            components['topple'] = -float(base.config.get('topple_penalty', 50.))
        if failure:
            components['failure'] = -5.
        if success:
            components['success'] = base.config['reward_weights']['success']
        return components, dict(success=success, bilateral_contact=bilateral,
                                 lifted=lifted, rise_m=rise, stable=stable,
                                 stable_hold_decisions=self.hold,
                                 pad_distance_m=distance, best_pad_distance_m=self.best_distance,
                                 initial_pad_distance_m=self.initial_distance,
                                 reach_threshold_m=self.reach_threshold,
                                 neighbor_displacements_mm=neighbors,
                                 physical_confirmation='simulation_only',
                                 visual_grasp_confirmed=None, visual_lift_confirmed=None)
