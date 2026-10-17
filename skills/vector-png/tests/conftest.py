"""Optional workspace temp root for constrained test environments."""
import os
from pathlib import Path
import uuid

import pytest


@pytest.fixture
def tmp_path(tmp_path_factory):
    root = os.environ.get('VECTOR_PNG_TEST_TMP_ROOT')
    if not root:
        return tmp_path_factory.mktemp('vector-png')
    path = Path(root).resolve() / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path
