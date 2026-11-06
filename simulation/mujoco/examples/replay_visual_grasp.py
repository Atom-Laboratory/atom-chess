"""Inspect an experimental PPO checkpoint in the MuJoCo viewer."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import mujoco.viewer
from stable_baselines3 import PPO
from atom_mujoco.visual_grasp_env import VisualGraspEnv
from atom_mujoco.controls import clean_view_options


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--run',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=10000)
    args=parser.parse_args()
    report=json.loads((args.run/'report.json').read_text())
    for path,key in ((args.bundle/'model.xml','model_sha256'),
                     (args.run/'policy.zip','checkpoint_sha256')):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=report[key]:
            parser.error('Model or checkpoint differs from recorded evaluation')
    env=VisualGraspEnv(args.bundle)
    try:
        policy=PPO.load(args.run/'policy.zip',device='cpu')
        obs,_=env.reset(seed=args.seed)
        with mujoco.viewer.launch_passive(env.sim.model,env.sim.data) as viewer:
            viewer.cam.lookat[:]=env.origin
            viewer.cam.distance=.6
            viewer.cam.elevation=-35
            while viewer.is_running():
                start=time.perf_counter()
                action,_=policy.predict(obs,deterministic=True)
                with viewer.lock():
                    obs,reward,terminated,truncated,info=env.step(action)
                    clean_view_options(viewer.opt)
                viewer.sync()
                time.sleep(max(0,env.sim.dt*5-(time.perf_counter()-start)))
                if terminated or truncated:
                    print(json.dumps(info,indent=2))
                    while viewer.is_running():
                        viewer.sync()
                        time.sleep(.05)
                    break
    finally:
        env.close()


if __name__=='__main__':
    main()
