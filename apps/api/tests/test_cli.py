import os
import subprocess
import sys

# A fresh interpreter: the test session has already imported every model.
# Resolving each foreign key fails if a referenced table was never imported.
PROBE = """
from lib_management import cli
from lib_management.config import Settings
from lib_management.identity.models import Account
cli._session_factory(Settings())
for table in Account.metadata.tables.values():
    for key in table.foreign_keys:
        key.column
"""


def test_cli_session_factory_registers_every_model():
    env = {**os.environ, "DB_PASSWORD": "unit-fixture"}
    result = subprocess.run(
        [sys.executable, "-c", PROBE], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
