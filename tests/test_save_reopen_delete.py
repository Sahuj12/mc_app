"""
Tests for the Save Data requirements (REQ-SAVE-01 .. REQ-SAVE-04) and the
per-user storage quotas that implement constraint C3 (limited storage).
"""
import re
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form
from config import Config


def run_and_extract_token(client, **overrides) -> str:
    resp = client.post("/simulate/run", data=default_sim_form(**overrides))
    html = resp.get_data(as_text=True)
    match = re.search(r'name="token" value="([a-f0-9]+)"', html)
    assert match, "expected an unsaved-run token on the results page"
    return match.group(1)


class TestSaveSimulation(AppTestCase, unittest.TestCase):
    """REQ-SAVE-01 / REQ-SAVE-02: Store user-inserted data and generated simulations."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "savesim")

    def test_save_persists_and_redirects_to_saved_view(self):
        token = run_and_extract_token(self.client, initial_price=175)
        resp = self.client.post("/simulate/save", data={"token": token, "name": "My saved run"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"My saved run", resp.data)
        self.assertIn(b"175.0000", resp.data)  # original input params preserved

    def test_saved_run_contains_full_summary(self):
        token = run_and_extract_token(self.client)
        resp = self.client.post("/simulate/save", data={"token": token, "name": "with summary"}, follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertIn("Mean terminal price", html)
        self.assertIn("Value at Risk (95%)", html)

    def test_expired_or_invalid_token_cannot_be_saved(self):
        resp = self.client.post("/simulate/save", data={"token": "not-a-real-token", "name": "ghost"}, follow_redirects=True)
        self.assertIn(b"expired", resp.data.lower())


class TestReopenSimulation(AppTestCase, unittest.TestCase):
    """REQ-SAVE-03: Allow users to reopen previously saved files."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "reopensim")

    def test_reopen_shows_original_inputs_and_summary(self):
        token = run_and_extract_token(self.client, initial_price=88, drift=0.04)
        self.client.post("/simulate/save", data={"token": token, "name": "reopen me"}, follow_redirects=True)

        listing = self.client.get("/saved").get_data(as_text=True)
        match = re.search(r'/saved/(\d+)"', listing)
        self.assertIsNotNone(match)
        real_sim_id = match.group(1)

        reopened = self.client.get(f"/saved/{real_sim_id}")
        self.assertEqual(reopened.status_code, 200)
        html = reopened.get_data(as_text=True)
        self.assertIn("88.0000", html)
        self.assertIn("Reopened from your saved simulations", html)

    def test_reopen_another_users_simulation_is_blocked(self):
        token = run_and_extract_token(self.client)
        save_resp = self.client.post("/simulate/save", data={"token": token, "name": "mine"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)

        # A second, different user should not be able to view this simulation.
        other_client = self.app.test_client()
        register_and_login(other_client, "otheruser")
        resp = other_client.get(f"/saved/{sim_id}")
        self.assertEqual(resp.status_code, 404)


class TestDeleteSimulation(AppTestCase, unittest.TestCase):
    """REQ-SAVE-04: Allow users to delete previously saved files."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "deletesim")

    def test_delete_removes_from_saved_list(self):
        token = run_and_extract_token(self.client)
        self.client.post("/simulate/save", data={"token": token, "name": "to be deleted"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)

        resp = self.client.post(f"/saved/{sim_id}/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"to be deleted", resp.data)

    def test_deleted_simulation_no_longer_reachable(self):
        token = run_and_extract_token(self.client)
        self.client.post("/simulate/save", data={"token": token, "name": "gone soon"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)
        self.client.post(f"/saved/{sim_id}/delete")

        resp = self.client.get(f"/saved/{sim_id}")
        self.assertEqual(resp.status_code, 404)


class TestStorageQuotas(AppTestCase, unittest.TestCase):
    """C3: The system has limited data storage -- enforced via per-user caps."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "quotas")

    def test_cannot_exceed_max_saved_simulations(self):
        last_resp = None
        for i in range(Config.MAX_SAVED_SIMULATIONS_PER_USER + 2):
            token = run_and_extract_token(self.client, time_horizon_years=0.05, num_simulations=100)
            last_resp = self.client.post(
                "/simulate/save", data={"token": token, "name": f"run{i}"}, follow_redirects=True
            )
        html = last_resp.get_data(as_text=True)
        self.assertIn("limit", html.lower())

        listing = self.client.get("/saved").get_data(as_text=True)
        saved_count = listing.count('href="/saved/')
        self.assertLessEqual(saved_count, Config.MAX_SAVED_SIMULATIONS_PER_USER)


if __name__ == "__main__":
    unittest.main()
