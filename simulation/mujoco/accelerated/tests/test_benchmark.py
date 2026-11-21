import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('atom_gpu_benchmark',Path(__file__).resolve().parents[1]/'benchmark.py')
benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)


@pytest.mark.parametrize('field,value',[('worlds',[16,1]),('worlds',[1,1]),('worlds',[65]),
    ('steps',127),('repeats',1),('max_worlds',2048),('max_gpu_mib',16384)])
def test_benchmark_rejects_invalid_budgets_before_gpu_import(field,value):
    args=SimpleNamespace(worlds=[1,16],max_worlds=64,steps=128,repeats=3,threads=6,max_gpu_mib=2048)
    setattr(args,field,value)
    with pytest.raises(ValueError):benchmark.validate(args)
