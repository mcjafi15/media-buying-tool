import pytest
from pathlib import Path
import core.db as db_module


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Patches DB_PATH to a temp file and initializes schema."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    return tmp_path / "test.db"
