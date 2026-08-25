"""
Simulation blueprint: the core analytical workflow of the app.

Routes
------
GET  /dashboard                 overview + quick links
GET  /simulate/new               simulation input form
POST /simulate/run                validate inputs, run MC, show results
POST /simulate/save               persist an ephemeral run to the DB
GET  /saved                      list saved simulations
GET  /saved/<id>                  reopen a saved simulation
POST /saved/<id>/delete           delete a saved simulation
GET  /datasets                   list uploaded datasets
POST /datasets/upload             upload a new CSV dataset
POST /datasets/<id>/delete        delete a dataset
"""
from __future__ import annotations

import json

import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, abort
)

import db
from auth import login_required, current_user
from config import Config
from mc_engine import validate_params, run_simulation, ValidationError, parse_bootstrap_returns_from_prices
from datasets import parse_uploaded_csv, DatasetError
from security import encrypt_text, decrypt_text
from narrative import build_narrative
import run_cache

simulate_bp = Blueprint("simulate", __name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@simulate_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    recent_sims = db.list_simulations_for_user(user["id"])[:5]
    recent_datasets = db.list_datasets_for_user(user["id"])[:5]
    sim_count = db.count_simulations_for_user(user["id"])
    dataset_count = db.count_datasets_for_user(user["id"])
    return render_template(
        "dashboard.html",
        user=user,
        recent_sims=recent_sims,
        recent_datasets=recent_datasets,
        sim_count=sim_count,
        dataset_count=dataset_count,
        max_sims=Config.MAX_SAVED_SIMULATIONS_PER_USER,
        max_datasets=Config.MAX_SAVED_DATASETS_PER_USER,
    )


# ---------------------------------------------------------------------------
# New simulation / run
# ---------------------------------------------------------------------------
@simulate_bp.route("/simulate/new", methods=["GET"])
@login_required
def new_simulation():
    user = current_user()
    saved_datasets = db.list_datasets_for_user(user["id"])
    return render_template(
        "simulate.html",
        saved_datasets=saved_datasets,
        config=Config,
        form_values={},
        errors={},
    )


def _build_chart_payload(result: dict, params) -> dict:
    """Downsample paths for plotting and build a histogram of terminal prices."""
    paths = result["paths"]
    terminal_prices = result["terminal_prices"]

    n_plot = min(Config.MAX_PATHS_TO_PLOT, paths.shape[0])
    plot_idx = np.linspace(0, paths.shape[0] - 1, n_plot, dtype=int)
    sample_paths = paths[plot_idx]

    # Subsample the time axis too if there are many steps, to keep the
    # payload sent to the browser small.
    n_steps = sample_paths.shape[1]
    max_points_per_path = 500
    if n_steps > max_points_per_path:
        step_idx = np.linspace(0, n_steps - 1, max_points_per_path, dtype=int)
        sample_paths = sample_paths[:, step_idx]
        time_axis = (step_idx / params.steps_per_year).round(4).tolist()
    else:
        time_axis = (np.arange(n_steps) / params.steps_per_year).round(4).tolist()

    hist_counts, hist_edges = np.histogram(terminal_prices, bins=40)

    return {
        "time_axis": time_axis,
        "sample_paths": sample_paths.round(4).tolist(),
        "histogram": {
            "counts": hist_counts.tolist(),
            "bin_edges": hist_edges.round(4).tolist(),
        },
    }


@simulate_bp.route("/simulate/run", methods=["POST"])
@login_required
def run():
    user = current_user()
    form = request.form
    saved_datasets = db.list_datasets_for_user(user["id"])

    bootstrap_returns = None
    dataset_id_used = None
    distribution = (form.get("distribution") or "normal").strip().lower()

    if distribution == "bootstrap":
        chosen_dataset_id = form.get("dataset_id")
        upload = request.files.get("dataset_file")

        if upload and upload.filename:
            try:
                file_bytes = upload.read()
                df, bootstrap_returns = parse_uploaded_csv(file_bytes)
            except DatasetError as exc:
                return render_template(
                    "simulate.html", saved_datasets=saved_datasets, config=Config,
                    form_values=form, errors={"distribution": exc.message},
                ), 400

            # Auto-save the uploaded dataset for reuse, subject to quota.
            if db.count_datasets_for_user(user["id"]) < Config.MAX_SAVED_DATASETS_PER_USER:
                blob = encrypt_text(json.dumps({"returns": bootstrap_returns.tolist()}))
                dataset_id_used = db.create_dataset(user["id"], upload.filename, len(bootstrap_returns), blob)
            else:
                flash(
                    f"Dataset quota reached ({Config.MAX_SAVED_DATASETS_PER_USER} max) — "
                    "this dataset was used for this run only and not saved. Delete an old one to free up space.",
                    "warning",
                )
        elif chosen_dataset_id:
            row = db.get_dataset(int(chosen_dataset_id), user["id"])
            if not row:
                abort(404)
            payload = json.loads(decrypt_text(row["encrypted_blob"]))
            bootstrap_returns = np.array(payload["returns"], dtype=np.float64)
            dataset_id_used = row["id"]

    try:
        params = validate_params(form, bootstrap_returns=bootstrap_returns)
    except ValidationError as exc:
        return render_template(
            "simulate.html", saved_datasets=saved_datasets, config=Config,
            form_values=form, errors=exc.errors,
        ), 400

    result = run_simulation(params)
    chart_payload = _build_chart_payload(result, params)

    token = run_cache.put(user["id"], {
        "params": params,
        "summary": result["summary"],
        "dataset_id": dataset_id_used,
        "sample_paths_for_storage": result["paths"][
            np.linspace(0, result["paths"].shape[0] - 1, min(Config.MAX_PATHS_TO_STORE, result["paths"].shape[0]), dtype=int)
        ].round(4).tolist(),
    })

    narrative = build_narrative(params, result["summary"]) # ADDED

    return render_template(
        "results.html",
        params=params,
        summary=result["summary"],
        chart_payload_json=json.dumps(chart_payload),
        token=token,
        saved=False,
        sim_name="",
        narrative=narrative,   # ADDED
    )


@simulate_bp.route("/simulate/save", methods=["POST"])
@login_required
def save_run():
    user = current_user()
    token = request.form.get("token")
    name = (request.form.get("name") or "").strip() or "Untitled simulation"

    entry = run_cache.get(token, user["id"])
    if not entry:
        flash("This run has expired and can no longer be saved. Please run it again.", "error")
        return redirect(url_for("simulate.new_simulation"))

    if db.count_simulations_for_user(user["id"]) >= Config.MAX_SAVED_SIMULATIONS_PER_USER:
        flash(
            f"You've reached your saved-simulation limit ({Config.MAX_SAVED_SIMULATIONS_PER_USER}). "
            "Delete an old one before saving a new one.",
            "error",
        )
        return redirect(url_for("simulate.saved_list"))

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
        "steps_per_year": params.steps_per_year,
    }

    sim_id = db.create_simulation(
        user_id=user["id"],
        name=name,
        dataset_id=entry.get("dataset_id"),
        encrypted_params=encrypt_text(json.dumps(params_dict)),
        encrypted_summary=encrypt_text(json.dumps(entry["summary"])),
        encrypted_sample_paths=encrypt_text(json.dumps(entry["sample_paths_for_storage"])),
    )
    flash("Simulation saved.", "success")
    return redirect(url_for("simulate.view_saved", sim_id=sim_id))


# ---------------------------------------------------------------------------
# Saved simulations
# ---------------------------------------------------------------------------
@simulate_bp.route("/saved")
@login_required
def saved_list():
    user = current_user()
    sims = db.list_simulations_for_user(user["id"])
    return render_template("saved.html", sims=sims, max_sims=Config.MAX_SAVED_SIMULATIONS_PER_USER)


@simulate_bp.route("/saved/<int:sim_id>")
@login_required
def view_saved(sim_id):
    user = current_user()
    row = db.get_simulation(sim_id, user["id"])
    if not row:
        abort(404)

    params_dict = json.loads(decrypt_text(row["encrypted_params"]))
    summary = json.loads(decrypt_text(row["encrypted_summary"]))
    sample_paths = json.loads(decrypt_text(row["encrypted_sample_paths"]))

    from mc_engine import SimulationParams
    params = SimulationParams(**{k: v for k, v in params_dict.items()})

    n_steps = len(sample_paths[0]) if sample_paths else 0
    time_axis = (np.arange(n_steps) / params.steps_per_year).round(4).tolist()
    # Rebuild a histogram from the stored summary's percentiles is not exact;
    # instead we recompute a histogram from the (small) stored sample paths'
    # terminal values as a representative approximation for the reopened view.
    terminal_sample = [p[-1] for p in sample_paths] if sample_paths else []
    if terminal_sample:
        counts, edges = np.histogram(terminal_sample, bins=min(20, len(terminal_sample)))
    else:
        counts, edges = np.array([]), np.array([])

    chart_payload = {
        "time_axis": time_axis,
        "sample_paths": sample_paths,
        "histogram": {"counts": counts.tolist(), "bin_edges": edges.round(4).tolist()},
    }

    narrative = build_narrative(params, summary) 


    return render_template(
        "results.html",
        params=params,
        summary=summary,
        chart_payload_json=json.dumps(chart_payload),
        token=None,
        saved=True,
        sim_name=row["name"],
        sim_id=sim_id,
        narrative=narrative,   
        note="Reopened from your saved simulations. Chart paths shown are the "
             f"{len(sample_paths)} representative paths stored at save time "
             "(full path detail isn't retained, to keep storage bounded).",
    )


@simulate_bp.route("/saved/<int:sim_id>/delete", methods=["POST"])
@login_required
def delete_saved(sim_id):
    user = current_user()
    db.delete_simulation(sim_id, user["id"])
    flash("Simulation deleted.", "success")
    return redirect(url_for("simulate.saved_list"))


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
@simulate_bp.route("/datasets")
@login_required
def dataset_list():
    user = current_user()
    rows = db.list_datasets_for_user(user["id"])
    return render_template("datasets.html", datasets=rows, max_datasets=Config.MAX_SAVED_DATASETS_PER_USER)


@simulate_bp.route("/datasets/upload", methods=["POST"])
@login_required
def upload_dataset():
    user = current_user()
    upload = request.files.get("dataset_file")

    if db.count_datasets_for_user(user["id"]) >= Config.MAX_SAVED_DATASETS_PER_USER:
        flash(f"Dataset quota reached ({Config.MAX_SAVED_DATASETS_PER_USER}). Delete one first.", "error")
        return redirect(url_for("simulate.dataset_list"))

    if not upload or not upload.filename:
        flash("Please choose a CSV file to upload.", "error")
        return redirect(url_for("simulate.dataset_list"))

    try:
        file_bytes = upload.read()
        df, returns = parse_uploaded_csv(file_bytes)
    except DatasetError as exc:
        flash(exc.message, "error")
        return redirect(url_for("simulate.dataset_list"))

    blob = encrypt_text(json.dumps({"returns": returns.tolist()}))
    db.create_dataset(user["id"], upload.filename, len(returns), blob)
    flash("Dataset uploaded.", "success")
    return redirect(url_for("simulate.dataset_list"))


@simulate_bp.route("/datasets/<int:dataset_id>/delete", methods=["POST"])
@login_required
def delete_dataset(dataset_id):
    user = current_user()
    db.delete_dataset(dataset_id, user["id"])
    flash("Dataset deleted.", "success")
    return redirect(url_for("simulate.dataset_list"))
