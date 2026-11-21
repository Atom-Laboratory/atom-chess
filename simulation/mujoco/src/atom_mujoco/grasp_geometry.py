"""Static experimental grasp geometry and preload, independent of rendering."""
import mujoco
import numpy as np

from .collision import pregrasp_opening


def grasp_geometry(sim, identity, surface_z, part, closing_load_factor=None, *,
                   head_edge_fraction=None, command=None):
    if part not in ('stem', 'head'):
        raise ValueError('Expected stem or head diagnostic')
    stem = sim.model.geom(identity+'_stem')
    selected = sim.model.geom(identity+'_'+part)
    kind = int(sim.model.geom_type[selected.id])
    if kind not in (int(mujoco.mjtGeom.mjGEOM_CYLINDER), int(mujoco.mjtGeom.mjGEOM_SPHERE)):
        raise ValueError('Diagnostic requires a cylindrical or spherical selected part')
    radius = float(selected.size[0])
    effective_radius, height_offset, capacity, horizontal_factor = radius, 0., None, 1.
    if head_edge_fraction is not None:
        if (part != 'head' or kind != int(mujoco.mjtGeom.mjGEOM_SPHERE)
                or not np.isfinite(head_edge_fraction) or not 0 <= head_edge_fraction < 1
                or closing_load_factor is None or command is None):
            raise ValueError('Upper head edge requires sphere, fraction in [0, 1), load factor and command')
        scratch = mujoco.MjData(sim.model)
        scratch.qpos[:] = sim.model.qpos0
        scratch.qpos[sim.qadr] = sim.validate(command)
        mujoco.mj_forward(sim.model, scratch)
        half_heights = []
        for index in (1, 2):
            pad = sim.model.geom(f'finger_{index}_pad')
            rotation = scratch.geom_xmat[pad.id].reshape(3, 3)
            if (sim.model.geom_type[pad.id] != mujoco.mjtGeom.mjGEOM_BOX
                    or abs(rotation[2, 2]) > 1e-6 or max(abs(rotation[2])) < 1-1e-6):
                raise ValueError('Upper head edge requires upright box pads with horizontal closing normals')
            half_heights.append(float(abs(rotation[2])@pad.size))
        if not np.isclose(*half_heights, rtol=0, atol=1e-9):
            raise ValueError('Matching vertical pad extents required')
        cosine = np.sqrt(1-head_edge_fraction**2)
        effective_radius = radius*cosine
        height_offset = half_heights[0]+head_edge_fraction*radius
    radius_delta = effective_radius-float(stem.size[0])
    interference = .0005
    load = None
    if closing_load_factor is not None:
        if not np.isfinite(closing_load_factor) or closing_load_factor < 1:
            raise ValueError('Closing load factor must be finite and at least one')
        pads = [sim.model.geom(f'finger_{i}_pad').id for i in (1, 2)]
        friction = float(sim.model.geom_friction[[selected.id, *pads], 0].min())
        gain = float(sim.model.actuator_gainprm[3:5, 0].min())
        weight = float(sim.model.body_mass[sim.model.body(identity).id]*np.linalg.norm(sim.model.opt.gravity))
        force_limit = float(np.abs(sim.model.actuator_forcerange[3:5]).min())
        if friction <= 0 or gain <= 0:
            raise ValueError('Positive compiled friction and finger gains required')
        capacity = friction
        if head_edge_fraction is not None:
            capacity = friction*cosine-head_edge_fraction
            horizontal_factor = cosine+friction*head_edge_fraction
        if capacity <= 0:
            raise ValueError('Contact latitude cannot support weight under the compiled friction bound')
        normal_load = closing_load_factor*weight/(2*capacity)
        horizontal_load = normal_load*horizontal_factor
        if horizontal_load > force_limit:
            raise ValueError('Requested preload exceeds compiled finger force limits')
        interference = max(interference, horizontal_load/gain)
        load = dict(factor=closing_load_factor, weight_N=weight, friction_lower_bound=friction,
                    finger_gain_N_per_m=gain, estimated_normal_load_N=normal_load,
                    vertical_capacity_per_normal_N=capacity, estimated_horizontal_load_N=horizontal_load)
    result = dict(part=part, geom=selected.name, radius_m=radius,
        head_edge_fraction=head_edge_fraction, effective_radius_m=float(effective_radius),
        pad_center_height_offset_m=float(height_offset),
        tcp_z_m=surface_z+float(selected.pos[2])+height_offset,
        aperture_m=pregrasp_opening(sim, identity)+radius_delta,
        closing_target_m=pregrasp_opening(sim, identity, side_gap_m=-interference)+radius_delta,
        closing_interference_m=interference, model_load_estimate=load,
        assumptions='experimental Coulomb/static-servo approximation; not measured hardware force')
    if not sim.lower[3] <= result['closing_target_m'] <= sim.upper[3]:
        raise ValueError('Requested preload exceeds finger travel')
    return result
