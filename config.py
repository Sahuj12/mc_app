"""
Application configuration.

All "business rule" limits (max simulations, session timeout, storage caps)
live here so they can be tuned in one place without hunting through the
codebase. Values are deliberately conservative defaults suitable for a
single small server instance (see constraint C3: limited data storage).
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # --- Core Flask config -------------------------------------------------
    SECRET_KEY = os.environ.get("MC_SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "app.db")

    # Fernet key used to encrypt data at rest (simulation payloads, uploaded
    # datasets). In production this MUST come from a secret manager / env var
    # and never be committed to source control.
    ENCRYPTION_KEY = os.environ.get("MC_ENCRYPTION_KEY", None)

    # --- Session / security --------------------------------------------------
    SESSION_TIMEOUT_MINUTES = 30
    PASSWORD_RESET_TOKEN_MAX_AGE_SECONDS = 30 * 60  # 30 minutes
    MIN_PASSWORD_LENGTH = 8

    # --- Simulation limits -----------------------------------------------
    MAX_SIMULATIONS = 10_000          # hard ceiling on number of paths
    MIN_SIMULATIONS = 100
    MAX_TIME_HORIZON_YEARS = 10
    MIN_TIME_HORIZON_YEARS = 0.01
    TRADING_DAYS_PER_YEAR = 252
    # Guardrail so nobody can request e.g. 10,000 sims * 10 years daily steps
    # (25.2M points) and exhaust server memory. Chosen to keep peak arrays
    # comfortably under ~200MB of float64.
    MAX_TOTAL_DATA_POINTS = 6_000_000

    MAX_INITIAL_PRICE = 1_000_000_000
    MIN_INITIAL_PRICE = 0.0001
    MIN_VOLATILITY = 0.0
    MAX_VOLATILITY = 5.0  # 500% annualized vol -- generous but bounded
    MIN_DRIFT = -1.0
    MAX_DRIFT = 1.0

    # For the results chart we only ever draw a sample of paths -- plotting
    # 10,000 lines is both unreadable and slow in-browser.
    MAX_PATHS_TO_PLOT = 200
    # Likewise, we only persist a sample of paths for a saved run (not the
    # full path matrix) to respect storage constraints (C3). Full terminal
    # values / summary stats are always stored in full.
    MAX_PATHS_TO_STORE = 100

    # --- Uploaded dataset limits -------------------------------------------
    MAX_UPLOAD_BYTES = 2 * 1024 * 1024   # 2 MB
    MAX_UPLOAD_ROWS = 100_000
    ALLOWED_UPLOAD_EXTENSIONS = {"csv"}

    # --- Storage quotas (C3: limited data storage) --------------------------
    MAX_SAVED_SIMULATIONS_PER_USER = 25
    MAX_SAVED_DATASETS_PER_USER = 10
