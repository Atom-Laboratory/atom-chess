from pathlib import Path

import pytest

from atom_learning.environment import load_config


@pytest.fixture
def config():
    return load_config(Path(__file__).parents[1] / 'config/prototype.json')
