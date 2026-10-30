from pathlib import Path
import pytest
from atom_mujoco.model import build_bundle
from atom_mujoco.backend import Simulation


@pytest.fixture(scope='session')
def bundle(tmp_path_factory):
    root = Path(__file__).resolve().parents[2]
    output = tmp_path_factory.mktemp('mujoco')/'bundle'
    build_bundle(root/'src/urdf/atom.urdf.xacro', output)
    return output


@pytest.fixture
def sim(bundle):
    return Simulation(bundle)
