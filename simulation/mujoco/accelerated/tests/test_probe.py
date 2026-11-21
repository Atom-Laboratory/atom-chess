import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def probe_module():
    path = Path(__file__).resolve().parents[1]/'probe.py'
    spec = importlib.util.spec_from_file_location('gpu_probe_contract', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('field,value', [('worlds',1025),('worlds',0),('steps',10001),
    ('max_wall_s',float('inf')),('max_wall_s',1801),('max_gpu_mib',8193)])
def test_probe_rejects_unbounded_resource_requests_before_gpu_import(field,value):
    args = SimpleNamespace(worlds=1,steps=500,max_wall_s=180.,max_gpu_mib=2048)
    setattr(args,field,value)
    with pytest.raises(ValueError, match='required'):
        probe_module().validate_args(args)
