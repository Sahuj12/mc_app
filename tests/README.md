# Test Suite

Automated tests verifying the requirements in `../REQUIREMENTS_TRACEABILITY_MATRIX.md`.
Built on Python's built-in `unittest` (no installation required), and fully
compatible with `pytest` if you have it installed (pytest auto-discovers
`unittest.TestCase` classes).

## Running the tests

From the project root (the `mc_app/` folder, alongside `app.py`):

```bash
# Using the standard library (always available, no install needed):
python -m unittest discover -v

# Or, if you have pytest installed:
pytest tests/ -v
```

Both commands run the exact same tests.

## Test isolation

`tests/__init__.py` points the app at a temporary, throwaway SQLite database
(via the `MC_DATABASE_PATH` environment variable) before any other module is
imported. **Running tests never touches or modifies your real development
database** at `instance/app.db`. The temp database is created fresh in your
system's temp directory each time you run the suite and can be safely ignored
or deleted afterward.

## File map

| File | Requirements covered |
|---|---|
| `test_auth.py` | REQ-ACC-01 .. REQ-ACC-04 (accounts, login/logout, password reset) |
| `test_input_validation.py` | REQ-IN-01, REQ-IN-02, REQ-IN-04, REQ-IN-05 |
| `test_simulation_engine.py` | REQ-OUT-01, distribution options (REQ-IN-02) |
| `test_datasets.py` | REQ-IN-03 (dataset upload) |
| `test_output_and_charts.py` | REQ-OUT-02, REQ-OUT-03 |
| `test_save_reopen_delete.py` | REQ-SAVE-01 .. REQ-SAVE-04, storage quotas (C3) |
| `test_export.py` | REQ-EXP-01, REQ-EXP-02 |
| `test_security.py` | NFR-SEC-01, NFR-SEC-02, NFR-SEC-03 |
| `test_usability.py` | NFR-USE-01, NFR-COMPAT-01, NFR-MAINT-02 |
| `test_reliability.py` | NFR-REL-01 |

See `REQUIREMENTS_TRACEABILITY_MATRIX.md` in the project root for the full
mapping, including the handful of requirements (cross-browser rendering,
coding-standard adherence) that are inherently manual/review-based rather
than automatable.
