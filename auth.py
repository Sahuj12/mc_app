"""
Authentication blueprint: registration, login/logout, forgot/reset password.

Session handling notes
-----------------------
- Flask's signed session cookie stores only the user id and a
  last-activity timestamp; no password or sensitive data ever goes in the
  cookie.
- Every request through @login_required checks the last-activity timestamp
  against Config.SESSION_TIMEOUT_MINUTES and force-logs-out stale sessions.

Password reset notes
---------------------
- This demo app does not have an SMTP server configured, so instead of
  emailing the reset link we render it directly on the "forgot password"
  confirmation page (and log it server-side). In a real deployment, replace
  `deliver_reset_link()` with an actual email send (e.g. via an email API)
  and stop returning the link in the HTTP response.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)

import db
from config import Config
from security import hash_password, verify_password, generate_reset_token, verify_reset_token

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        last_active = session.get("last_active")
        if not user_id or not last_active:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))

        last_active_dt = datetime.fromisoformat(last_active)
        if datetime.now(timezone.utc) - last_active_dt > timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES):
            session.clear()
            flash("Your session expired due to inactivity. Please log in again.", "error")
            return redirect(url_for("auth.login"))

        session["last_active"] = datetime.now(timezone.utc).isoformat()
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.get_user_by_id(user_id)


def _validate_email(email: str) -> str | None:
    if not email or not EMAIL_RE.match(email.strip()):
        return "Please enter a valid email address."
    return None


def _validate_password(password: str) -> str | None:
    if not password or len(password) < Config.MIN_PASSWORD_LENGTH:
        return f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters."
    if password.lower() == password or password.upper() == password:
        return "Password should mix uppercase and lowercase letters."
    if not any(c.isdigit() for c in password):
        return "Password should include at least one digit."
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    errors = {}
    email_err = _validate_email(email)
    if email_err:
        errors["email"] = email_err
    pw_err = _validate_password(password)
    if pw_err:
        errors["password"] = pw_err
    if password != confirm:
        errors["confirm_password"] = "Passwords do not match."

    if not errors and db.get_user_by_email(email):
        errors["email"] = "An account with this email already exists."

    if errors:
        return render_template("register.html", errors=errors, email=email), 400

    user_id = db.create_user(email, hash_password(password))
    current_app.logger.info("New account created: user_id=%s", user_id)
    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""

    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email), 401

    session.clear()
    session["user_id"] = user["id"]
    session["last_active"] = datetime.now(timezone.utc).isoformat()
    session.permanent = True

    flash(f"Welcome back, {user['email']}!", "success")
    next_url = request.args.get("next")
    return redirect(next_url or url_for("simulate.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = (request.form.get("email") or "").strip()
    user = db.get_user_by_email(email)

    reset_link = None
    if user:
        token = generate_reset_token(user["id"])
        reset_link = url_for("auth.reset_password", token=token, _external=True)
        # In production: send `reset_link` via email instead of displaying it.
        current_app.logger.info("Password reset requested for user_id=%s: %s", user["id"], reset_link)

    # Always show the same confirmation regardless of whether the email
    # exists, to avoid leaking which emails are registered.
    return render_template("forgot_password.html", submitted=True, reset_link=reset_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_id = verify_reset_token(token)
    if not user_id:
        flash("This password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""
    errors = {}
    pw_err = _validate_password(password)
    if pw_err:
        errors["password"] = pw_err
    if password != confirm:
        errors["confirm_password"] = "Passwords do not match."

    if errors:
        return render_template("reset_password.html", token=token, errors=errors), 400

    db.update_user_password(user_id, hash_password(password))
    flash("Your password has been reset. Please log in.", "success")
    return redirect(url_for("auth.login"))
