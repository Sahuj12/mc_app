"""
Tests for Simulation Output and Charts requirements (REQ-OUT-02, REQ-OUT-03).
"""
import json
import re
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form


def extract_chart_payload(html: str) -> dict:
    match = re.search(r'<script id="chart-data" type="application/json">(.*?)</script>', html, re.S)
    assert match, "chart-data payload should be embedded in the results page"
    return json.loads(match.group(1))


class TestChartPayload(AppTestCase, unittest.TestCase):
    """REQ-OUT-02: Present the simulations in the form of a chart."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "chartpayload")

    def test_results_page_contains_chart_canvases(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        self.assertIn('id="pathsChart"', html)
        self.assertIn('id="histChart"', html)

    def test_chart_payload_has_sample_paths_and_histogram(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(num_simulations=2000))
        payload = extract_chart_payload(resp.get_data(as_text=True))
        self.assertIn("sample_paths", payload)
        self.assertIn("histogram", payload)
        self.assertGreater(len(payload["sample_paths"]), 0)
        self.assertIn("counts", payload["histogram"])
        self.assertIn("bin_edges", payload["histogram"])

    def test_chart_paths_are_subsampled_not_all_simulations(self):
        """Plotting all 5000 paths would be unreadable; the app should subsample."""
        resp = self.client.post("/simulate/run", data=default_sim_form(num_simulations=5000))
        payload = extract_chart_payload(resp.get_data(as_text=True))
        self.assertLess(len(payload["sample_paths"]), 5000)

    def test_outlier_flags_present_and_bounded(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(num_simulations=3000, volatility=0.4))
        payload = extract_chart_payload(resp.get_data(as_text=True))
        self.assertIn("is_outlier", payload)
        self.assertEqual(len(payload["is_outlier"]), len(payload["sample_paths"]))


class TestStatisticalSummary(AppTestCase, unittest.TestCase):
    """REQ-OUT-03: Provide statistical summaries."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "statsummary")

    def test_summary_page_contains_key_statistics(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        for label in [
            "Mean terminal price", "Median terminal price", "Std. deviation",
            "Min / Max", "Mean return", "Probability of loss", "Skewness",
            "Excess kurtosis", "Value at Risk (95%)", "Value at Risk (99%)",
            "Conditional VaR (95%)", "Outlier paths", "Percentiles of terminal price",
        ]:
            self.assertIn(label, html, f"summary should display: {label}")

    def test_percentiles_are_monotonically_increasing(self):
        resp = self.client.post("/simulate/run", data=default_sim_form(num_simulations=3000))
        html = resp.get_data(as_text=True)
        # Extract the percentile table row values in order
        rows = re.findall(r'<td>([\d.]+)</td>', html)
        percentile_values = [float(v) for v in rows[-9:]]  # last 9 <td> are the percentile row
        self.assertEqual(percentile_values, sorted(percentile_values),
                          "P1..P99 should be non-decreasing")

    def test_probability_of_loss_is_a_valid_percentage(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        match = re.search(r'Probability of loss.*?stat-value">([\d.]+)%', html, re.S)
        self.assertIsNotNone(match)
        value = float(match.group(1))
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 100.0)

    def test_summary_language_stays_descriptive_not_advisory(self):
        """C2: the tool must not give financial advice -- check for the disclaimer language."""
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        self.assertIn("not a prediction or recommendation", html)
        self.assertNotIn("you should buy", html.lower())
        self.assertNotIn("you should sell", html.lower())
        self.assertNotIn("we recommend", html.lower())


if __name__ == "__main__":
    unittest.main()
