"""Recorded-control replay kernels; diagnostics are excluded from actor inputs."""
import warp as wp


@wp.kernel
def apply_tape(tape:wp.array2d[wp.float32],ctrl:wp.array2d[wp.float32],cursor:wp.array[wp.int32]):
    world,actuator=wp.tid()
    ctrl[world,actuator]=tape[cursor[0],actuator]


@wp.kernel
def apply_candidates(tapes:wp.array3d[wp.float32],ctrl:wp.array2d[wp.float32],cursor:wp.array[wp.int32]):
    world,actuator=wp.tid()
    ctrl[world,actuator]=tapes[world,cursor[0],actuator]


@wp.kernel
def record_state(qpos:wp.array2d[wp.float32],qvel:wp.array2d[wp.float32],
                 out_qpos:wp.array3d[wp.float32],out_qvel:wp.array3d[wp.float32],
                 overflow:wp.array[wp.int32],flags:wp.array[wp.int32],cursor:wp.array[wp.int32],nq:int,nv:int):
    world,index=wp.tid()
    if index<nq:out_qpos[cursor[0],world,index]=qpos[world,index]
    if index<nv:out_qvel[cursor[0],world,index]=qvel[world,index]
    if index==0:wp.atomic_or(flags,world,overflow[world])


@wp.kernel
def record_contacts(geom:wp.array[wp.vec2i],worldid:wp.array[wp.int32],dist:wp.array[wp.float32],
                    nacon:wp.array[wp.int32],bodyid:wp.array[wp.int32],forbidden_pairs:wp.array[wp.int32],
                    pad1:int,pad2:int,selected:int,ngeom:int,
                    pads:wp.array3d[wp.int32],forbidden:wp.array2d[wp.int32],cursor:wp.array[wp.int32]):
    index=wp.tid()
    if index<nacon[0]:
        a,b=geom[index][0],geom[index][1]
        if dist[index]<=0.:
            world=worldid[index]
            if (a==pad1 and bodyid[b]==selected) or (b==pad1 and bodyid[a]==selected):
                wp.atomic_or(pads,cursor[0],world,0,1)
            if (a==pad2 and bodyid[b]==selected) or (b==pad2 and bodyid[a]==selected):
                wp.atomic_or(pads,cursor[0],world,1,1)
            if forbidden_pairs[a*ngeom+b]!=0:wp.atomic_or(forbidden,cursor[0],world,1)


@wp.kernel
def next_step(cursor:wp.array[wp.int32]):
    cursor[0]=cursor[0]+1
