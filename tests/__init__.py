"""
Test package initialization.

CRITICAL: this module must set MC_DATABASE_PATH in the environment BEFORE
any test module imports `config`, `db`, or `app` -- Config.DATABASE_PATH is
read once at import time. Because Python caches modules, this only works
reliably if it happens here, in the package's __init__.py, which unittest's
test discovery (and pytest) both import before any test_*.py submodule.

This guarantees the test suite never reads or writes to your real
development database at instance/app.db.
"""
import os
import tempfile

_TEST_DB_DIR = tempfile.mkdtemp(prefix="mc_app_test_db_")
os.environ["MC_DATABASE_PATH"] = os.path.join(_TEST_DB_DIR, "test.db")
os.environ.setdefault("MC_SECRET_KEY", "test-secret-key-not-for-production")
