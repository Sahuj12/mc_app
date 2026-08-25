"""
Tests for Simulation Input requirements (REQ-IN-01 .. REQ-IN-05).
"""
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form
from config import Config


class TestRequiredParams(AppTestCase, unittest.TestCase):
    """REQ-IN-01: Modify required financial parameters."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "reqparams")

    def test_all_required_fields_accepted_when_valid(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(
            initial_price=250, drift=0.1, volatility=0.35, time_horizon_years=2, num_simulations=1000,
        ))
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("250.0000", html)  # initial price echoed on results page

    def test_new_simulation_form_exposes_all_required_fields(self):
        resp = self.client.get("/simulate/new")
        html = resp.get_data(as_text=True)
        for field in ["initial_price", "drift", "volatility", "time_horizon_years", "num_simulations"]:
            self.assertIn(f'name="{field}"', html, f"form should expose editable field: {field}")


class TestOptionalParams(AppTestCase, unittest.TestCase):
    """REQ-IN-02: Modify optional parameters (seed, distribution type, custom datasets)."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "optparams")

    def test_new_simulation_form_exposes_optional_fields(self):
        resp = self.client.get("/simulate/new")
        html = resp.get_data(as_text=True)
        self.assertIn('name="random_seed"', html)
        self.assertIn('name="distribution"', html)
        self.assertIn('name="dataset_file"', html)

    def test_random_seed_is_optional_and_reproducible(self):
        import json, re

        def extract_payload(html):
            match = re.search(r'<script id="chart-data" type="application/json">(.*?)</script>', html, re.S)
            return json.loads(match.group(1))

        resp_a = self.client.post("/simulate/run", data=default_sim_form(random_seed=999))
        resp_b = self.client.post("/simulate/run", data=default_sim_form(random_seed=999))
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(resp_b.status_code, 200)

        payload_a = extract_payload(resp_a.get_data(as_text=True))
        payload_b = extract_payload(resp_b.get_data(as_text=True))
        self.assertEqual(
            payload_a["sample_paths"], payload_b["sample_paths"],
            "identical seed and inputs should reproduce identical simulated paths",
        )

    def test_seed_left_blank_still_runs(self):
        form = default_sim_form()
        form["random_seed"] = ""
        resp = self.client.post("/simulate/run", data=form)
        self.assertEqual(resp.status_code, 200)


class TestValidationErrors(AppTestCase, unittest.TestCase):
    """REQ-IN-04: Validate inputs and display errors."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "valerr")

    def test_negative_initial_price_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(initial_price=-5))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"field-error", resp.data)

    def test_out_of_range_volatility_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(volatility=-1))
        self.assertEqual(resp.status_code, 400)

    def test_out_of_range_drift_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(drift=99))
        self.assertEqual(resp.status_code, 400)

    def test_out_of_range_time_horizon_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(time_horizon_years=999))
        self.assertEqual(resp.status_code, 400)

    def test_non_numeric_input_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(initial_price="not-a-number"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"must be a number", resp.data)

    def test_invalid_distribution_name_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(distribution="not_a_real_distribution"))
        self.assertEqual(resp.status_code, 400)

    def test_bootstrap_without_dataset_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(distribution="bootstrap"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"requires an uploaded dataset", resp.data)

    def test_cross_field_memory_guardrail(self):
        """A combination that is individually in-range per-field but whose
        simulations x steps product is too large must still be rejected."""
        resp = self.client.post("/simulate/run", data=default_sim_form(
            time_horizon_years=10, num_simulations=9999,
        ))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"too large", resp.data)

    def test_valid_input_after_fixing_errors_succeeds(self):
        """Simulates a user correcting a validation error and resubmitting."""
        bad = self.client.post("/simulate/run", data=default_sim_form(initial_price=-5))
        self.assertEqual(bad.status_code, 400)
        good = self.client.post("/simulate/run", data=default_sim_form(initial_price=100))
        self.assertEqual(good.status_code, 200)


class TestSimulationCountLimit(AppTestCase, unittest.TestCase):
    """REQ-IN-05: Ask for number of simulations, but enforce a maximum limit."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "simcount")

    def test_at_maximum_allowed_succeeds(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(
            num_simulations=Config.MAX_SIMULATIONS, time_horizon_years=0.05,
        ))
        self.assertEqual(resp.status_code, 200)

    def test_above_maximum_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(
            num_simulations=Config.MAX_SIMULATIONS + 1, time_horizon_years=0.05,
        ))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"num_simulations", resp.data)

    def test_below_minimum_rejected(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(num_simulations=1))
        self.assertEqual(resp.status_code, 400)

    def test_form_advertises_the_maximum(self):
        resp = self.client.get("/simulate/new")
        html = resp.get_data(as_text=True)
        self.assertIn(str(Config.MAX_SIMULATIONS), html)


if __name__ == "__main__":
    unittest.main()
