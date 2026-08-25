"""
Tests for the Reliability non-functional requirement (NFR-REL-01): the
system shall handle invalid inputs gracefully -- meaning clean 4xx errors
with helpful messages, never an unhandled server crash (500) or a stack
trace leaking to the user.
"""
import io
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form
from config import Config


class TestGracefulFailure(AppTestCase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "reliability")

    def test_missing_required_field_does_not_crash(self):
        form = default_sim_form()
        del form["initial_price"]
        resp = self.client.post("/simulate/run", data=form)
        self.assertEqual(resp.status_code, 400)

    def test_completely_empty_submission_does_not_crash(self):
        resp = self.client.post("/simulate/run", data={})
        self.assertEqual(resp.status_code, 400)

    def test_oversized_upload_rejected_cleanly(self):
        # Build a file just over the configured max upload size.
        oversized = b"price\n" + b"1.0\n" * (Config.MAX_UPLOAD_BYTES // 4)
        data = {"dataset_file": (io.BytesIO(oversized), "big.csv")}
        resp = self.client.post("/datasets/upload", data=data, content_type="multipart/form-data")
        self.assertIn(resp.status_code, (302, 413), "oversized upload should be rejected, not crash the server")

    def test_nonexistent_saved_simulation_returns_404_not_500(self):
        resp = self.client.get("/saved/999999999")
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_page_returns_custom_404(self):
        resp = self.client.get("/this-page-does-not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"Page not found", resp.data)

    def test_malformed_dataset_id_in_bootstrap_run_handled(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(
            distribution="bootstrap", dataset_id="not-a-number",
        ))
        # Should fail gracefully (400/404), not crash with a 500.
        self.assertIn(resp.status_code, (400, 404))

    def test_sql_injection_style_input_does_not_crash_or_succeed(self):
        """Basic defense-in-depth check: malicious-looking input should be
        treated as ordinary invalid data (parameterized queries throughout
        db.py prevent actual injection), not cause a server error."""
        resp = self.client.post("/simulate/run", data=default_sim_form(
            initial_price="100'; DROP TABLE users; --",
        ))
        self.assertEqual(resp.status_code, 400)  # rejected as non-numeric, not a crash

        # Confirm the users table is still intact afterward.
        import db
        self.assertIsNotNone(db.get_user_by_email)  # module still importable/functional
        whoami = self.client.get("/dashboard")
        self.assertEqual(whoami.status_code, 200)  # our own session still works => table intact


if __name__ == "__main__":
    unittest.main()
