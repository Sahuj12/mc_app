"""
Plain-language narrative summaries for simulation results.

Deliberately NOT an LLM call: every sentence here is built directly from
numbers already computed by mc_engine.compute_summary_statistics(), using
conditional templates rather than free-form generation. This keeps the
summary:
  - Exactly consistent with the numbers shown elsewhere on the page
    (no risk of a model mis-describing or hallucinating a statistic)
  - Free and instant (no external API call, no added failure mode)
  - Bounded to descriptive language only -- never advisory/recommending
    language (see constraint C2: this tool is not a financial advisor)
"""
from __future__ import annotations


def _pct(x: float) -> str:
    return f"{x:.1f}%"


def describe_paths(params, summary: dict) -> str:
    """Narrative for the sample price paths chart."""
    drift_pct = params.drift * 100
    vol_pct = params.volatility * 100

    if params.drift > 0.005:
        drift_desc = f"an overall upward drift (an average expected return of {drift_pct:.1f}% per year)"
    elif params.drift < -0.005:
        drift_desc = f"an overall downward drift (an average expected decline of {abs(drift_pct):.1f}% per year)"
    else:
        drift_desc = "roughly flat drift on average (close to 0% expected annual return)"

    if vol_pct >= 40:
        spread_desc = "a very wide spread of outcomes, reflecting the high volatility you entered"
    elif vol_pct >= 15:
        spread_desc = "a moderate spread of outcomes"
    else:
        spread_desc = "a relatively narrow, tightly clustered spread of outcomes, reflecting the low volatility you entered"

    return (
        f"Each line is one independently simulated price path over {params.time_horizon_years:g} year(s), "
        f"starting from {params.initial_price:g}. As a group, the paths show {drift_desc}, and {spread_desc}. "
        f"The paths fan out further from the starting price as time passes -- this widening is expected, "
        f"since each day's random move builds on the last, so uncertainty compounds over the horizon."
    )


def describe_histogram(params, summary: dict) -> str:
    """Narrative for the terminal-price histogram."""
    skew = summary["skewness"]
    prob_loss = summary["prob_of_loss"] * 100

    if skew > 0.3:
        shape_desc = (
            "a right-skewed shape: most outcomes cluster together, with a longer tail of "
            "less-likely but larger upside outcomes. This lopsided shape is a normal, expected "
            "feature of this simulation model (Geometric Brownian Motion), not an anomaly -- "
            "prices are bounded at zero on the downside but can rise without limit on the upside."
        )
    elif skew < -0.3:
        shape_desc = "a left-skewed shape, with a longer tail of less-likely but larger downside outcomes."
    else:
        shape_desc = "a roughly symmetric, bell-like shape."

    return (
        f"This histogram counts up where all {params.num_simulations:,} simulated paths ended after "
        f"{params.time_horizon_years:g} year(s) -- not the paths themselves, just their final prices. "
        f"The distribution has {shape_desc} Across all simulations, {prob_loss:.1f}% ended below the "
        f"starting price of {params.initial_price:g}."
    )


def describe_overall(params, summary: dict) -> str:
    """One-paragraph overall summary, combining the key statistics."""
    var95 = summary["value_at_risk_95_pct"]
    cvar95 = summary["conditional_var_95_pct"]
    mean_return = summary["mean_return_pct"]

    return (
        f"Across {params.num_simulations:,} simulated paths, the average simulated outcome was a "
        f"{'gain' if mean_return >= 0 else 'loss'} of {abs(mean_return):.1f}% relative to the starting "
        f"price. In the worst 5% of simulated outcomes, the loss was {var95:.1f}% or more (95% VaR), "
        f"and averaged {cvar95:.1f}% within just that worst-5% group (95% CVaR / expected shortfall). "
        f"These figures describe the spread of outcomes this specific simulation produced from the "
        f"inputs you chose -- they are statistical descriptions, not predictions or recommendations "
        f"about any real-world decision."
    )


def build_narrative(params, summary: dict) -> dict:
    return {
        "paths": describe_paths(params, summary),
        "histogram": describe_histogram(params, summary),
        "overall": describe_overall(params, summary),
    }
