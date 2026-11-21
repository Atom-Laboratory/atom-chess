import os
from pathlib import Path
import sys

import numpy as np
import pytest


@pytest.mark.skipif(os.environ.get('ATOM_TEST_CUDA')!='1',reason='Opt-in actual CUDA diagnostic kernel test')
def test_contact_metrics_separate_worlds_and_preserve_forbidden_contacts():
    import warp as wp
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from cuda_rollout import record_contacts
    wp.init()
    with wp.ScopedDevice('cuda:0'):
        geoms=wp.array(np.array([[3,4],[2,0],[1,0]],dtype=np.int32),dtype=wp.vec2i)
        worlds=wp.array(np.array([0,1,1],dtype=np.int32))
        distance=wp.array(np.array([-.001,-.001,-.001],dtype=np.float32))
        ncon=wp.array(np.array([3],dtype=np.int32));body=wp.array(np.array([2,1,1,1,2],dtype=np.int32))
        bad=np.zeros(25,dtype=np.int32);bad[1*5+0]=1
        forbidden_pairs=wp.array(bad);pads=wp.zeros((1,2,2),dtype=wp.int32)
        forbidden=wp.zeros((1,2),dtype=wp.int32);cursor=wp.zeros(1,dtype=wp.int32)
        wp.launch(record_contacts,dim=3,inputs=[geoms,worlds,distance,ncon,body,forbidden_pairs,
            3,2,2,5,pads,forbidden,cursor])
        np.testing.assert_array_equal(pads.numpy(),[[[1,0],[0,1]]])
        np.testing.assert_array_equal(forbidden.numpy(),[[0,1]])
