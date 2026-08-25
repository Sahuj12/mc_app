"""
Monte Carlo simulation engine.

Implements Geometric Brownian Motion (GBM) price-path simulation with a
choice of shock distributions:

  - normal      : standard GBM, shocks ~ N(0, 1)
  - student_t   : heavier-tailed shocks, Student's t scaled to unit variance
  - bootstrap   : shocks resampled (with replacement) from a user-supplied
                  historical daily-returns dataset (non-parametric)

This module is intentionally free of any Flask/DB imports so it can be
unit-tested and reasoned about in isolation.

IMPORTANT: This is a statistical/analytical tool. It reports probabilities
and distributions implied by the user's own chosen inputs; it does not
recommend, predict, or advise on any real-world financial decision
(see constraint C2). See ValidationError for the difference between
"invalid input" and "implausible but syntactically valid input" (A2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import stats

from config import Config


class ValidationError(Exception):
    """Raised when user-supplied simulation parameters fail validation.

    Carries a dict of field_name -> message so the UI can show inline
    errors next to the offending field.
    """

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))


@dataclass
class SimulationParams:
    initial_price: float
    drift: float                 # annualized expected return, e.g. 0.07 for 7%
    volatility: float             # annualized volatility, e.g. 0.2 for 20%
    time_horizon_years: float
    num_simulations: int
    distribution: str = "normal"  # "normal" | "student_t" | "bootstrap"
    student_t_dof: float = 5.0    # degrees of freedom, only used if student_t
    random_seed: Optional[int] = None
    steps_per_year: int = Config.TRADING_DAYS_PER_YEAR
    bootstrap_returns: Optional[np.ndarray] = field(default=None, repr=False)  # daily log returns

    @property
    def num_steps(self) -> int:
        return max(1, round(self.time_horizon_years * self.steps_per_year))


def validate_params(raw: dict, bootstrap_returns: Optional[np.ndarray] = None) -> SimulationParams:
    """
    Validate raw (typically request.form) input and return a SimulationParams
    instance, or raise ValidationError with field-level messages.
    """
    errors: dict[str, str] = {}

    def _to_float(key, label):
        val = raw.get(key)
        try:
            return float(val)
        except (TypeError, ValueError):
            errors[key] = f"{label} must be a number."
            return None

    def _to_int(key, label):
        val = raw.get(key)
        try:
            return int(float(val))
        except (TypeError, ValueError):
            errors[key] = f"{label} must be a whole number."
            return None

    initial_price = _to_float("initial_price", "Initial price")
    drift = _to_float("drift", "Expected return (drift)")
    volatility = _to_float("volatility", "Volatility")
    time_horizon = _to_float("time_horizon_years", "Time horizon")
    num_simulations = _to_int("num_simulations", "Number of simulations")

    if initial_price is not None and not (Config.MIN_INITIAL_PRICE <= initial_price <= Config.MAX_INITIAL_PRICE):
        errors["initial_price"] = (
            f"Initial price must be between {Config.MIN_INITIAL_PRICE} and {Config.MAX_INITIAL_PRICE:,}."
        )

    if drift is not None and not (Config.MIN_DRIFT <= drift <= Config.MAX_DRIFT):
        errors["drift"] = f"Expected return must be between {Config.MIN_DRIFT} and {Config.MAX_DRIFT} (as a decimal, e.g. 0.07 = 7%)."

    if volatility is not None and not (Config.MIN_VOLATILITY <= volatility <= Config.MAX_VOLATILITY):
        errors["volatility"] = f"Volatility must be between {Config.MIN_VOLATILITY} and {Config.MAX_VOLATILITY} (as a decimal, e.g. 0.2 = 20%)."

    if time_horizon is not None and not (Config.MIN_TIME_HORIZON_YEARS <= time_horizon <= Config.MAX_TIME_HORIZON_YEARS):
        errors["time_horizon_years"] = f"Time horizon must be between {Config.MIN_TIME_HORIZON_YEARS} and {Config.MAX_TIME_HORIZON_YEARS} years."

    if num_simulations is not None and not (Config.MIN_SIMULATIONS <= num_simulations <= Config.MAX_SIMULATIONS):
        errors["num_simulations"] = f"Number of simulations must be between {Config.MIN_SIMULATIONS} and {Config.MAX_SIMULATIONS:,}."

    distribution = (raw.get("distribution") or "normal").strip().lower()
    if distribution not in ("normal", "student_t", "bootstrap"):
        errors["distribution"] = "Distribution must be one of: normal, student_t, bootstrap."

    student_t_dof = 5.0
    if distribution == "student_t":
        student_t_dof = _to_float("student_t_dof", "Degrees of freedom") or 5.0
        if student_t_dof <= 2:
            errors["student_t_dof"] = "Degrees of freedom must be greater than 2 (for finite variance)."

    if distribution == "bootstrap" and (bootstrap_returns is None or len(bootstrap_returns) < 30):
        errors["distribution"] = "Bootstrap distribution requires an uploaded dataset with at least 30 return observations."

    random_seed = None
    seed_raw = (raw.get("random_seed") or "").strip()
    if seed_raw:
        try:
            random_seed = int(seed_raw)
            if not (0 <= random_seed <= 2**32 - 1):
                errors["random_seed"] = "Random seed must be a non-negative integer (max 4294967295)."
        except ValueError:
            errors["random_seed"] = "Random seed must be an integer."

    # Cross-field guardrail: total simulated data points must stay bounded
    # regardless of individually-valid inputs (protects server memory).
    if not errors and time_horizon is not None and num_simulations is not None:
        steps = max(1, round(time_horizon * Config.TRADING_DAYS_PER_YEAR))
        total_points = steps * num_simulations
        if total_points > Config.MAX_TOTAL_DATA_POINTS:
            max_sims_at_this_horizon = max(Config.MIN_SIMULATIONS, Config.MAX_TOTAL_DATA_POINTS // steps)
            errors["num_simulations"] = (
                f"Number of simulations \u00d7 daily steps is too large ({total_points:,} data points). "
                f"At this time horizon, reduce simulations to about {max_sims_at_this_horizon:,} or fewer, "
                f"or shorten the time horizon."
            )

    if errors:
        raise ValidationError(errors)

    return SimulationParams(
        initial_price=initial_price,
        drift=drift,
        volatility=volatility,
        time_horizon_years=time_horizon,
        num_simulations=num_simulations,
        distribution=distribution,
        student_t_dof=student_t_dof,
        random_seed=random_seed,
        bootstrap_returns=bootstrap_returns,
    )


def _generate_shocks(params: SimulationParams, rng: np.random.Generator) -> np.ndarray:
    """Return an (num_simulations, num_steps) array of unit-variance shocks."""
    shape = (params.num_simulations, params.num_steps)

    if params.distribution == "normal":
        return rng.standard_normal(shape)

    if params.distribution == "student_t":
        dof = params.student_t_dof
        raw = rng.standard_t(dof, size=shape)
        # scale to unit variance: Var(t_dof) = dof / (dof - 2)
        scale = np.sqrt(dof / (dof - 2))
        return raw / scale

    if params.distribution == "bootstrap":
        returns = params.bootstrap_returns
        mu = returns.mean()
        sigma = returns.std(ddof=1)
        if sigma == 0:
            sigma = 1e-12
        standardized = (returns - mu) / sigma
        idx = rng.integers(0, len(standardized), size=shape)
        return standardized[idx]

    raise ValueError(f"Unknown distribution: {params.distribution}")  # pragma: no cover


def run_simulation(params: SimulationParams) -> dict:
    """
    Run the GBM Monte Carlo simulation described by `params`.

    Returns a dict with:
      - paths: full (num_simulations, num_steps + 1) ndarray of price paths
               (including the initial price as column 0)
      - terminal_prices: 1D ndarray, final price of every simulated path
      - summary: dict of summary statistics
    """
    rng = np.random.default_rng(params.random_seed)

    dt = 1.0 / params.steps_per_year
    shocks = _generate_shocks(params, rng)

    # GBM log-return per step: (drift - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z
    drift_term = (params.drift - 0.5 * params.volatility ** 2) * dt
    diffusion_term = params.volatility * np.sqrt(dt) * shocks

    log_returns = drift_term + diffusion_term
    cumulative_log_returns = np.cumsum(log_returns, axis=1)

    paths = np.empty((params.num_simulations, params.num_steps + 1), dtype=np.float64)
    paths[:, 0] = params.initial_price
    paths[:, 1:] = params.initial_price * np.exp(cumulative_log_returns)

    terminal_prices = paths[:, -1]
    summary = compute_summary_statistics(terminal_prices, params.initial_price)

    return {"paths": paths, "terminal_prices": terminal_prices, "summary": summary}


def compute_summary_statistics(terminal_prices: np.ndarray, initial_price: float) -> dict:
    """Compute descriptive + risk statistics on the distribution of terminal prices."""
    returns = terminal_prices / initial_price - 1.0
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_values = {f"p{p}": float(np.percentile(terminal_prices, p)) for p in percentiles}

    # Historical/empirical Value-at-Risk and Conditional VaR on simple returns,
    # reported as *statistical descriptions of the simulated distribution*,
    # not as investment advice (see C2).
    var_95 = float(-np.percentile(returns, 5))
    var_99 = float(-np.percentile(returns, 1))
    tail_95 = returns[returns <= np.percentile(returns, 5)]
    cvar_95 = float(-tail_95.mean()) if len(tail_95) else float("nan")

    skew = float(stats.skew(terminal_prices))
    kurt = float(stats.kurtosis(terminal_prices))  # excess kurtosis

    return {
        "mean": float(np.mean(terminal_prices)),
        "median": float(np.median(terminal_prices)),
        "std_dev": float(np.std(terminal_prices, ddof=1)),
        "min": float(np.min(terminal_prices)),
        "max": float(np.max(terminal_prices)),
        "skewness": skew,
        "excess_kurtosis": kurt,
        "prob_of_loss": float(np.mean(terminal_prices < initial_price)),
        "mean_return_pct": float(np.mean(returns) * 100),
        "value_at_risk_95_pct": var_95 * 100,
        "value_at_risk_99_pct": var_99 * 100,
        "conditional_var_95_pct": cvar_95 * 100,
        "percentiles": pct_values,
    }


def parse_bootstrap_returns_from_prices(prices: np.ndarray) -> np.ndarray:
    """Given a series of historical prices, return daily log returns for bootstrap sampling."""
    prices = np.asarray(prices, dtype=np.float64)
    prices = prices[prices > 0]
    if len(prices) < 2:
        raise ValueError("Need at least 2 positive price observations to compute returns.")
    return np.diff(np.log(prices))
