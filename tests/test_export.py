"""
Tests for Data Export requirements (REQ-EXP-01, REQ-EXP-02).
"""
import csv
import io
import json
import re
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form


def run_and_extract_token(client, **overrides) -> str:
    resp = client.post("/simulate/run", data=default_sim_form(**overrides))
    html = resp.get_data(as_text=True)
    match = re.search(r'name="token" value="([a-f0-9]+)"', html)
    assert match
    return match.group(1)


class TestExportCSV(AppTestCase, unittest.TestCase):
    """REQ-EXP-01 (CSV branch): export results and summaries as CSV."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "exportcsv")

    def test_export_csv_from_unsaved_run(self):
        token = run_and_extract_token(self.client, initial_price=120)
        resp = self.client.get(f"/export/csv?token={token}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "text/csv; charset=utf-8")

        rows = list(csv.reader(io.StringIO(resp.get_data(as_text=True))))
        header = rows[0]
        self.assertEqual(header, ["Section", "Field", "Value"])
        # initial_price parameter row should be present with the right value
        param_rows = {r[1]: r[2] for r in rows if len(r) == 3 and r[0] == "Parameter"}
        self.assertEqual(param_rows.get("initial_price"), "120.0")

    def test_export_csv_from_saved_run(self):
        token = run_and_extract_token(self.client)
        save_resp = self.client.post("/simulate/save", data={"token": token, "name": "csv export test"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)

        resp = self.client.get(f"/export/csv?sim_id={sim_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Parameter,initial_price", resp.data)

    def test_export_csv_missing_identifier_fails_cleanly(self):
        resp = self.client.get("/export/csv")
        self.assertEqual(resp.status_code, 400)

    def test_export_csv_expired_token_fails_cleanly(self):
        resp = self.client.get("/export/csv?token=not-a-real-token")
        self.assertEqual(resp.status_code, 404)


class TestExportJSON(AppTestCase, unittest.TestCase):
    """REQ-EXP-01 (JSON branch): export results and summaries as JSON."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "exportjson")

    def test_export_json_from_unsaved_run(self):
        token = run_and_extract_token(self.client, initial_price=99)
        resp = self.client.get(f"/export/json?token={token}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "application/json")

        payload = json.loads(resp.get_data(as_text=True))
        self.assertIn("parameters", payload)
        self.assertIn("summary_statistics", payload)
        self.assertIn("sample_terminal_prices", payload)
        self.assertEqual(payload["parameters"]["initial_price"], 99.0)

    def test_export_json_from_saved_run(self):
        token = run_and_extract_token(self.client)
        self.client.post("/simulate/save", data={"token": token, "name": "json export test"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)

        resp = self.client.get(f"/export/json?sim_id={sim_id}")
        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.get_data(as_text=True))
        self.assertIn("summary_statistics", payload)

    def test_export_json_for_other_users_sim_is_blocked(self):
        token = run_and_extract_token(self.client)
        self.client.post("/simulate/save", data={"token": token, "name": "private"}, follow_redirects=True)
        listing = self.client.get("/saved").get_data(as_text=True)
        sim_id = re.search(r'/saved/(\d+)"', listing).group(1)

        other_client = self.app.test_client()
        register_and_login(other_client, "exportother")
        resp = other_client.get(f"/export/json?sim_id={sim_id}")
        self.assertEqual(resp.status_code, 404)


class TestChartExportUI(AppTestCase, unittest.TestCase):
    """
    REQ-EXP-02: export charts as PNG/JPEG.

    The actual image encoding happens client-side in the browser (canvas ->
    PNG, see static/js/results.js downloadChart()), so it cannot be verified
    by a server-side HTTP test. This test verifies the export controls are
    present and wired to the correct chart canvases; a manual check in a
    real browser (click each export button, confirm a PNG downloads) is
    recommended to close the loop -- see REQUIREMENTS_TRACEABILITY_MATRIX.md.
    """

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "chartexport")

    def test_png_export_buttons_present_and_reference_correct_canvases(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        self.assertIn("downloadChart('pathsChart'", html)
        self.assertIn("downloadChart('histChart'", html)

    def test_results_js_defines_download_chart_function(self):
        resp = self.client.get("/static/js/results.js")
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        resp.close()
        self.assertIn(b"window.downloadChart", data)
        self.assertIn(b"toDataURL(\"image/png\")", data)


if __name__ == "__main__":
    unittest.main()
