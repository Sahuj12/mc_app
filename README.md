# Monte Carlo Studio

A working, self-contained Monte Carlo simulation web app for quantitative
finance/data science use: run GBM-based price simulations with multiple
shock distributions, view interactive charts and statistical summaries,
save and reopen past runs, and export results.

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in a desktop browser (Chrome, Firefox, Edge,
Safari). Create an account, then run a simulation.

The SQLite database is created automatically at `instance/app.db` on first
run. Delete that file to reset all data.

## Project layout

```
app.py              Flask app factory, wiring, error pages
config.py           All tunable limits in one place (max sims, quotas, etc.)
security.py         Password hashing, encryption-at-rest, reset tokens
db.py               SQLite data access layer (schema + queries)
mc_engine.py         Monte Carlo engine: GBM simulation + validation + stats
datasets.py          CSV upload parsing/validation for bootstrap datasets
run_cache.py          In-memory cache for not-yet-saved run results
auth.py               /register /login /logout /forgot-password /reset-password
sim_routes.py         /dashboard /simulate/* /saved/* /datasets/*
export_routes.py     /export/csv /export/json
templates/            Jinja2 templates (one consistent design system)
static/css/style.css  Single stylesheet used by every page
static/js/            Chart rendering (Chart.js via CDN), PNG export, tooltips
```

## How each requirement is met

**Accounts** — `/register`, `/login`, `/logout`, `/forgot-password` +
`/reset-password/<token>`. Passwords are hashed with PBKDF2-SHA256
(`werkzeug.security`), never stored or logged in plaintext.

**Simulation input** — `/simulate/new` lets you set initial price, drift,
volatility, time horizon, and number of simulations (all required), plus
optional random seed, distribution type (Normal / Student-t / Bootstrap),
and dataset upload. Every field has a hover/tap tooltip explaining it.
Server-side validation (`mc_engine.validate_params`) rejects out-of-range
or malformed input with field-specific error messages, and enforces a hard
ceiling on simulation count (`Config.MAX_SIMULATIONS`) plus a combined
simulations×steps guardrail so no request can exhaust server memory.

**Output & charts** — `/simulate/run` runs a vectorized NumPy GBM simulation
and renders an interactive line chart of sample paths and a histogram of
terminal prices (Chart.js), plus a full statistical summary: mean, median,
std dev, min/max, skewness, excess kurtosis, probability of loss, and
Value-at-Risk / Conditional VaR at 95%/99% — all labeled as descriptive
statistics of the simulated distribution, not investment advice (C2).

**Save / reopen / delete** — `/simulate/save`, `/saved`, `/saved/<id>`,
`/saved/<id>/delete`. To respect limited storage (C3), a saved run keeps
its full summary statistics but only a representative sample of price
paths (`Config.MAX_PATHS_TO_STORE`), not the entire path matrix. Per-user
caps on saved simulations and datasets are enforced (`Config.MAX_SAVED_*`).

**Export** — `/export/csv` and `/export/json` for results + summary stats
(from either an in-progress run or a saved one). Chart PNG export is done
client-side (`static/js/results.js`, canvas → PNG), so exported images are
pixel-identical to what's on screen with no server round-trip.

**Security** — PBKDF2 password hashing; Fernet (AES-128 + HMAC) encryption
at rest for all stored simulation parameters, summaries, sample paths, and
uploaded dataset contents (`security.py`); signed, time-limited password
reset tokens (`itsdangerous`) that can't be forged or replayed after
expiry; server-side session timeout (`Config.SESSION_TIMEOUT_MINUTES`,
enforced in `auth.login_required` on every request).

**Compatibility** — targets desktop browsers only (C1); a banner appears
if the viewport is narrow, and the CSS enforces a desktop minimum width
rather than attempting a phone layout.

**Consistency/maintainability** — one shared `base.html` and one
`style.css` (CSS custom properties for colors/spacing/typography) used by
every page; docstrings and comments throughout explaining *why*, not just
what.
