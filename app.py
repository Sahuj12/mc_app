"""
Application entry point.

Run locally with:

    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000 in a desktop browser (see constraint C1 --
this app targets desktop browsers; it is not designed for mobile viewports).
"""
from __future__ import annotations

import logging
from datetime import timedelta

from flask import Flask, redirect, url_for, session, render_template

from config import Config
import db
from auth import auth_bp, login_required, current_user
from sim_routes import simulate_bp
from export_routes import export_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # In production behind HTTPS, also set SESSION_COOKIE_SECURE = True.
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_BYTES + (1024 * 1024)  # headroom for form fields

    logging.basicConfig(level=logging.INFO)

    db.init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(simulate_bp)
    app.register_blueprint(export_bp)

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("simulate.dashboard"))
        return render_template("landing.html")

    @app.context_processor
    def inject_globals():
        return {"current_user": current_user()}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, message="Uploaded file is too large."), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("error.html", code=500, message="Something went wrong on our end."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
