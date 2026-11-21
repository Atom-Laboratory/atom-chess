"""Privileged passive full-state physics recordings for replay, not observations."""
import hashlib
import json

import mujoco
import numpy as np


class PhysicsRecording:
    def __init__(self,simulation,*,max_transitions=100000):
        if type(max_transitions) is not int or not 1<=max_transitions<=1000000:
            raise ValueError('Recording budget must be 1..1000000 transitions')
        self.max_transitions=max_transitions
        self.sim=simulation;self.signature=int(mujoco.mjtState.mjSTATE_INTEGRATION)
        self.width=mujoco.mj_stateSize(simulation.model,self.signature)
        self.before=[];self.after=[];self.phases=[];self.phase='INITIALIZATION'
        self.pending=None

    def state(self):
        result=np.empty(self.width)
        mujoco.mj_getState(self.sim.model,self.sim.data,result,self.signature)
        return result

    def before_step(self):
        if len(self.before)>=self.max_transitions:raise RuntimeError('Physics recording budget exhausted')
        if self.pending is not None:raise RuntimeError('Unfinished recorded physics transition')
        self.pending=self.state()

    def after_step(self):
        if self.pending is None:raise RuntimeError('Recorded physics output without input')
        self.before.append(self.pending);self.after.append(self.state());self.phases.append(self.phase)
        self.pending=None

    def save(self,path):
        if path.exists():raise FileExistsError('Use a new physics recording path')
        np.savez_compressed(path,before=np.asarray(self.before).reshape(-1,self.width),
            after=np.asarray(self.after).reshape(-1,self.width),phase=np.asarray(self.phases,dtype=str),
            signature=self.signature,model_sha256=self.sim.manifest['model_sha256'])
        manifest=dict(schema=1,transitions=len(self.before),signature=self.signature,state_width=self.width,
            model_sha256=self.sim.manifest['model_sha256'],mujoco_version=mujoco.__version__,
            numeric_dtype='float64',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            source='privileged evaluation/replay only; excluded from policy observations and targets',
            unfinished_transition=self.pending is not None)
        manifest['max_transitions']=self.max_transitions
        path.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        return manifest
