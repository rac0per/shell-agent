import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_memory.db")
