"""
Data export blueprint.

Supports exporting either:
  - an ephemeral just-run result (via `token`, from run_cache), or
  - a saved simulation (via `sim_id`, from the database)

as CSV or JSON. Chart image export (PNG/JPEG) is handled entirely
client-side (see static/js/results.js) using the <canvas> element's own
toDataURL/toBlob, since that requires no server round-trip and keeps the
exported image pixel-identical to what the user sees.
"""
from __future__ import annotations

import csv
import io
import json

from flask import Blueprint, request, abort, Response, send_file

import db
from auth import login_required, current_user
from security import decrypt_text
import run_cache

export_bp = Blueprint("export", __name__)


def _resolve_export_data(user_id: int):
    """Return (params_dict, summary_dict, sample_paths) from either a token or sim_id."""
    token = request.args.get("token")
    sim_id = request.args.get("sim_id")

    if token:
        entry = run_cache.get(token, user_id)
        if not entry:
            abort(404, "This run has expired. Please run the simulation again.")
        params = entry["params"]
        params_dict = {
            "initial_price": params.initial_price,
            "drift": params.drift,
            "volatility": params.volatility,
            "time_horizon_years": params.time_horizon_years,
            "num_simulations": params.num_simulations,
            "distribution": params.distribution,
            "student_t_dof": params.student_t_dof,
            "random_seed": params.random_seed,
        }
        return params_dict, entry["summary"], entry["sample_paths_for_storage"]

    if sim_id:
        row = db.get_simulation(int(sim_id), user_id)
        if not row:
            abort(404)
        params_dict = json.loads(decrypt_text(row["encrypted_params"]))
        summary = json.loads(decrypt_text(row["encrypted_summary"]))
        sample_paths = json.loads(decrypt_text(row["encrypted_sample_paths"]))
        return params_dict, summary, sample_paths

    abort(400, "Missing token or sim_id.")


@export_bp.route("/export/json")
@login_required
def export_json():
    user = current_user()
    params_dict, summary, sample_paths = _resolve_export_data(user["id"])
    payload = {
        "parameters": params_dict,
        "summary_statistics": summary,
        "sample_terminal_prices": [p[-1] for p in sample_paths],
    }
    buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
    return send_file(
        buf, mimetype="application/json", as_attachment=True,
        download_name="monte_carlo_results.json",
    )


@export_bp.route("/export/csv")
@login_required
def export_csv():
    user = current_user()
    params_dict, summary, sample_paths = _resolve_export_data(user["id"])

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Section", "Field", "Value"])
    for k, v in params_dict.items():
        writer.writerow(["Parameter", k, v])
    for k, v in summary.items():
        if k == "percentiles":
            for pk, pv in v.items():
                writer.writerow(["Summary/Percentile", pk, pv])
        else:
            writer.writerow(["Summary", k, v])

    writer.writerow([])
    writer.writerow(["Sample path terminal prices"])
    writer.writerow(["path_index", "terminal_price"])
    for i, p in enumerate(sample_paths):
        writer.writerow([i, p[-1]])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    return send_file(
        mem, mimetype="text/csv", as_attachment=True,
        download_name="monte_carlo_results.csv",
    )
