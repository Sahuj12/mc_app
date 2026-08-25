"""
Shared test infrastructure: a base TestCase that gives every test a fresh
Flask test client against the isolated test database, plus small helpers
for common flows (registering + logging in a user) so individual test
files stay focused on what they're actually verifying.
"""
from __future__ import annotations

import uuid

import app as app_module
import db as db_module
from config import Config


class AppTestCase:
    """
    Mixin providing app/client setup. Actual test classes should inherit
    from (AppTestCase, unittest.TestCase) -- see test files for the pattern.

    Each test method gets a fresh Flask test client. The underlying SQLite
    database persists across tests within a run (it's the isolated temp
    database set up in tests/__init__.py), so tests use unique emails
    (see `unique_email`) to avoid colliding with each other rather than
    wiping the database between every single test -- this keeps the suite
    fast while still avoiding cross-test interference.
    """

    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.app = app_module.app

    def setUp(self):
        self.client = self.app.test_client()


def unique_email(tag: str) -> str:
    """Generate a collision-free email for a test, tagged for readability in failures."""
    return f"{tag}.{uuid.uuid4().hex[:10]}@test.local"


DEFAULT_PASSWORD = "TestPass1"


def register_user(client, email: str, password: str = DEFAULT_PASSWORD):
    return client.post("/register", data={
        "email": email, "password": password, "confirm_password": password,
    })


def login_user(client, email: str, password: str = DEFAULT_PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


def register_and_login(client, tag: str, password: str = DEFAULT_PASSWORD) -> str:
    """Register a fresh unique user and log them in on the given client. Returns the email used."""
    email = unique_email(tag)
    register_user(client, email, password)
    login_user(client, email, password)
    return email


def default_sim_form(**overrides) -> dict:
    """A baseline valid simulation form payload, with any fields overridden for a specific test."""
    form = {
        "initial_price": "100",
        "drift": "0.07",
        "volatility": "0.2",
        "time_horizon_years": "1",
        "num_simulations": "500",
        "distribution": "normal",
        "random_seed": "42",
    }
    form.update({k: str(v) for k, v in overrides.items()})
    return form
