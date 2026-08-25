"""
Tests for User Account and Access requirements (REQ-ACC-01 .. REQ-ACC-04).
"""
import re
import unittest
from datetime import datetime, timezone, timedelta

from .helpers import AppTestCase, unique_email, register_user, login_user, DEFAULT_PASSWORD
import db


class TestRegistration(AppTestCase, unittest.TestCase):
    """REQ-ACC-01: The system shall allow users to create an account."""

    def test_valid_registration_succeeds(self):
        email = unique_email("reg_valid")
        resp = register_user(self.client, email)
        self.assertEqual(resp.status_code, 302, "valid registration should redirect to login")
        with self.app.app_context():
            self.assertIsNotNone(db.get_user_by_email(email), "user should exist in the database")

    def test_duplicate_email_rejected(self):
        email = unique_email("reg_dupe")
        register_user(self.client, email)
        resp = register_user(self.client, email)
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"already exists", resp.data)

    def test_weak_password_rejected(self):
        email = unique_email("reg_weak")
        resp = self.client.post("/register", data={
            "email": email, "password": "weak", "confirm_password": "weak",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"at least", resp.data.lower())
        with self.app.app_context():
            self.assertIsNone(db.get_user_by_email(email))

    def test_mismatched_confirmation_rejected(self):
        email = unique_email("reg_mismatch")
        resp = self.client.post("/register", data={
            "email": email, "password": DEFAULT_PASSWORD, "confirm_password": "Different1",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"do not match", resp.data)

    def test_invalid_email_format_rejected(self):
        resp = self.client.post("/register", data={
            "email": "not-an-email", "password": DEFAULT_PASSWORD, "confirm_password": DEFAULT_PASSWORD,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"valid email", resp.data)

    def test_password_stored_hashed_not_plaintext(self):
        email = unique_email("reg_hash")
        register_user(self.client, email)
        with self.app.app_context():
            user = db.get_user_by_email(email)
            self.assertNotEqual(user["password_hash"], DEFAULT_PASSWORD)
            self.assertTrue(user["password_hash"].startswith("pbkdf2:"))


class TestLogin(AppTestCase, unittest.TestCase):
    """REQ-ACC-02: The system shall allow users to log in."""

    def test_correct_credentials_logs_in(self):
        email = unique_email("login_ok")
        register_user(self.client, email)
        resp = login_user(self.client, email)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers.get("Location", ""))

    def test_wrong_password_rejected(self):
        email = unique_email("login_badpw")
        register_user(self.client, email)
        resp = login_user(self.client, email, password="WrongPass1")
        self.assertEqual(resp.status_code, 401)
        self.assertIn(b"Invalid email or password", resp.data)

    def test_nonexistent_email_rejected(self):
        resp = login_user(self.client, unique_email("login_none"))
        self.assertEqual(resp.status_code, 401)

    def test_dashboard_requires_login(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))


class TestLogout(AppTestCase, unittest.TestCase):
    """REQ-ACC-03: The system shall allow users to log out."""

    def test_logout_clears_session_and_blocks_protected_pages(self):
        email = unique_email("logout")
        register_user(self.client, email)
        login_user(self.client, email)
        self.assertEqual(self.client.get("/dashboard").status_code, 200)

        resp = self.client.get("/logout")
        self.assertEqual(resp.status_code, 302)

        resp2 = self.client.get("/dashboard")
        self.assertEqual(resp2.status_code, 302)
        self.assertIn("/login", resp2.headers.get("Location", ""))


class TestPasswordReset(AppTestCase, unittest.TestCase):
    """REQ-ACC-04: The system shall allow users to reset password / 'forgot password'."""

    def test_reset_flow_end_to_end(self):
        email = unique_email("reset_ok")
        register_user(self.client, email)

        resp = self.client.post("/forgot-password", data={"email": email})
        self.assertEqual(resp.status_code, 200)
        match = re.search(r"reset-password/([^\"\s]+)", resp.get_data(as_text=True))
        self.assertIsNotNone(match, "reset link should be present in the response")
        token = match.group(1)

        new_password = "NewPass1"
        resp2 = self.client.post(f"/reset-password/{token}", data={
            "password": new_password, "confirm_password": new_password,
        })
        self.assertEqual(resp2.status_code, 302)

        # Old password must no longer work
        resp3 = login_user(self.client, email, password=DEFAULT_PASSWORD)
        self.assertEqual(resp3.status_code, 401)

        # New password must work
        resp4 = login_user(self.client, email, password=new_password)
        self.assertEqual(resp4.status_code, 302)

    def test_invalid_token_rejected(self):
        resp = self.client.get("/reset-password/not-a-real-token")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/forgot-password", resp.headers.get("Location", ""))

    def test_no_email_enumeration(self):
        """Submitting forgot-password for a nonexistent email should look identical to a real one."""
        resp_real = self.client.post("/forgot-password", data={"email": unique_email("enum_real")})
        resp_fake = self.client.post("/forgot-password", data={"email": "definitely-not-registered@test.local"})
        self.assertEqual(resp_real.status_code, resp_fake.status_code)
        # Both should show the same generic confirmation copy
        self.assertIn(b"reset link has been generated", resp_real.data)
        self.assertIn(b"reset link has been generated", resp_fake.data)


if __name__ == "__main__":
    unittest.main()
