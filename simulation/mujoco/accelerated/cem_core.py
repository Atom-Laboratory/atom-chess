"""Bounded CEM distribution and physical lexicographic ranking."""
import numpy as np


LOWER=np.array([1.5,.1,.1]);UPPER=np.array([4.,.5,.5])
INITIAL=np.array([2.5,.25,.25])


def rank(record):
    outcome=record.get('outcome',{})
    valid=bool(record.get('geometry_valid') and not outcome.get('forbidden_contact',True))
    return (valid,bool(valid and outcome.get('success')),float(outcome.get('maximum_rise_m',0.)) if valid else -1.,
            -float(record.get('duration_s',1e6)))


class Distribution:
    def __init__(self,seed):
        self.rng=np.random.default_rng(seed);self.mean=INITIAL.copy();self.std=(UPPER-LOWER)*.2
        self.best=INITIAL.copy();self.generation=0

    def ask(self,count):
        if type(count) is not int or not 4<=count<=64:raise ValueError('Population must be 4..64')
        values=np.clip(self.rng.normal(self.mean,self.std,size=(count,3)),LOWER,UPPER)
        values[0]=self.best
        return values

    def update(self,parameters,records):
        if len(parameters)!=len(records) or len(records)<4:raise ValueError('One physical record per population member required')
        order=sorted(range(len(records)),key=lambda i:rank(records[i]),reverse=True)
        elite=parameters[order[:max(2,len(order)//4)]]
        self.best=parameters[order[0]].copy()
        self.mean=.3*self.mean+.7*elite.mean(axis=0)
        self.std=np.maximum(.3*self.std+.7*elite.std(axis=0),.03*(UPPER-LOWER))
        self.generation+=1
        return order

    def state(self):
        return dict(mean=self.mean.tolist(),std=self.std.tolist(),best=self.best.tolist(),
                    generation=self.generation,rng=self.rng.bit_generator.state)

    def restore(self,state):
        for name in ('mean','std','best'):
            value=np.asarray(state[name],dtype=float)
            if value.shape!=(3,) or not np.isfinite(value).all():raise ValueError('Invalid CEM checkpoint')
            setattr(self,name,value)
        if (np.any(self.std<=0) or np.any(self.mean<LOWER) or np.any(self.mean>UPPER)
                or np.any(self.best<LOWER) or np.any(self.best>UPPER)):
            raise ValueError('Out-of-bounds CEM checkpoint')
        self.rng.bit_generator.state=state['rng'];self.generation=int(state['generation'])
