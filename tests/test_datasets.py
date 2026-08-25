"""
Tests for dataset upload (REQ-IN-03) and its use in bootstrap simulations.
"""
import io
import unittest
import numpy as np

from .helpers import AppTestCase, register_and_login, default_sim_form


def make_price_csv(n=500, seed=1) -> bytes:
    rng = np.random.default_rng(seed)
    prices = 100 * np.exp(np.cumsum(0.0003 + 0.01 * rng.standard_normal(n)))
    content = "price\n" + "\n".join(f"{p:.4f}" for p in prices)
    return content.encode("utf-8")


class TestDatasetUpload(AppTestCase, unittest.TestCase):
    """REQ-IN-03: Upload optional datasets."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "dataset")

    def test_upload_valid_price_csv_succeeds(self):
        data = {"dataset_file": (io.BytesIO(make_price_csv()), "prices.csv")}
        resp = self.client.post("/datasets/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 302)
        listing = self.client.get("/datasets")
        self.assertIn(b"prices.csv", listing.data)

    def test_upload_empty_file_rejected(self):
        data = {"dataset_file": (io.BytesIO(b""), "empty.csv")}
        resp = self.client.post("/datasets/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True).lower()
        self.assertTrue(
            "no columns to parse" in html or "no rows" in html or "could not parse" in html,
            "empty file upload should show a clear parsing error, not silently succeed",
        )
        # And critically: it must NOT have been saved as a usable dataset.
        self.assertIn("no datasets uploaded yet", html)

    def test_upload_non_csv_content_rejected_gracefully(self):
        data = {"dataset_file": (io.BytesIO(b"this is not a csv at all \x00\x01\x02"), "garbage.csv")}
        resp = self.client.post("/datasets/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)  # graceful error page, not a 500 crash

    def test_uploaded_dataset_usable_in_bootstrap_simulation(self):
        data = {"dataset_file": (io.BytesIO(make_price_csv()), "hist.csv")}
        self.client.post("/datasets/upload", data=data, content_type="multipart/form-data")

        listing = self.client.get("/datasets").get_data(as_text=True)
        import re
        # crude extraction of the delete-form action to find the dataset id
        match = re.search(r"/datasets/(\d+)/delete", listing)
        self.assertIsNotNone(match)
        dataset_id = match.group(1)

        resp = self.client.post("/simulate/run", data=default_sim_form(
            distribution="bootstrap", dataset_id=dataset_id,
        ))
        self.assertEqual(resp.status_code, 200)

    def test_delete_dataset(self):
        data = {"dataset_file": (io.BytesIO(make_price_csv()), "to_delete.csv")}
        self.client.post("/datasets/upload", data=data, content_type="multipart/form-data")
        listing = self.client.get("/datasets").get_data(as_text=True)
        import re
        dataset_id = re.search(r"/datasets/(\d+)/delete", listing).group(1)

        resp = self.client.post(f"/datasets/{dataset_id}/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"to_delete.csv", resp.data)


if __name__ == "__main__":
    unittest.main()
