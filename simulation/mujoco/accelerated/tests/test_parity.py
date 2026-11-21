import importlib.util
from pathlib import Path
import sys


sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('atom_gpu_parity',Path(__file__).resolve().parents[1]/'parity.py')
parity=importlib.util.module_from_spec(spec);spec.loader.exec_module(parity)


def test_contact_matching_preserves_forces_under_pair_and_buffer_reordering():
    first=dict(world=0,geoms=[1,2],distance=-.001,margin=0.,normal_force=.2,world_wrench=[0.,0.,.1,0.,0.,0.])
    second=dict(first,geoms=[2,1],world_wrench=[0.,0.,-.1,0.,0.,0.])
    assert parity.contact_summary([first],[second])['passed']
    assert not parity.contact_summary([first],[])['passed']
    changed=dict(second,normal_force=.3)
    assert not parity.contact_summary([first],[changed])['passed']
    grazing=dict(first,distance=-1e-7)
    result=parity.contact_summary([grazing],[])
    assert result['ambiguous_cpu']==[grazing] and result['pairs']==[]


def test_raw_comparison_rejects_nonfinite_and_dimension_mismatch():
    assert not parity.compare([0.],[float('nan')],1e-5,1e-4)['passed']
    assert not parity.compare([0.],[0.,1.],1e-5,1e-4)['passed']
    assert not parity.compare([0.],[1e-3],1e-5,1e-4)['passed']
