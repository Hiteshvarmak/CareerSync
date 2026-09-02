import os
import tempfile

_tmp = tempfile.gettempdir()
os.environ.setdefault("CAREERPILOT_DB_URL", f"sqlite:///{_tmp}/careerpilot_test.db")
os.environ.setdefault("CAREERPILOT_CHROMA_DIR", f"{_tmp}/careerpilot_chroma_test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import pytest

from backend.db import init_db


@pytest.fixture(autouse=True)
def _init_test_db():
    init_db()
    yield
