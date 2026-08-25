"""
Tests for Security non-functional requirements (NFR-SEC-01 .. NFR-SEC-03).
"""
import json
import re
import sqlite3
import unittest
from datetime import datetime, timezone, timedelta

from .helpers import AppTestCase, register_and_login, register_user, login_user, unique_email, default_sim_form, DEFAULT_PASSWORD
from config import Config
import db
from security import hash_password, verify_password, encrypt_text, decrypt_text


class TestPasswordHashing(unittest.TestCase):
    """NFR-SEC-01: Store user information using secure hashing."""

    def test_hash_is_not_plaintext(self):
        h = hash_password("SuperSecret1")
        self.assertNotEqual(h, "SuperSecret1")

    def test_hash_uses_pbkdf2(self):
        h = hash_password("SuperSecret1")
        self.assertTrue(h.startswith("pbkdf2:"))

    def test_correct_password_verifies(self):
        h = hash_password("SuperSecret1")
        self.assertTrue(verify_password("SuperSecret1", h))

    def test_wrong_password_fails_verification(self):
        h = hash_password("SuperSecret1")
        self.assertFalse(verify_password("WrongPassword", h))

    def test_same_password_hashed_twice_produces_different_hashes(self):
        """Salting means identical passwords should not produce identical hashes."""
        h1 = hash_password("SuperSecret1")
        h2 = hash_password("SuperSecret1")
        self.assertNotEqual(h1, h2)


class TestEncryptionAtRest(AppTestCase, unittest.TestCase):
    """NFR-SEC-03: Store user charts and data using encryption."""

    def setUp(self):
        super().setUp()
        self.email = register_and_login(self.client, "encryption")

    def test_saved_simulation_blob_is_not_plaintext_json(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        token = re.search(r'name="token" value="([a-f0-9]+)"', html).group(1)
        self.client.post("/simulate/save", data={"token": token, "name": "encrypted check"}, follow_redirects=True)

        conn = sqlite3.connect(Config.DATABASE_PATH)
        row = conn.execute("SELECT encrypted_params, encrypted_summary FROM simulations ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()

        for blob in row:
            self.assertFalse(blob.startswith(b"{"), "stored blob should be ciphertext, not raw JSON")
            with self.assertRaises(Exception):
                json.loads(blob)  # should not parse as plaintext JSON

    def test_encrypted_blob_round_trips_correctly(self):
        original = json.dumps({"initial_price": 100, "drift": 0.07})
        encrypted = encrypt_text(original)
        self.assertNotEqual(encrypted, original.encode("utf-8"))
        decrypted = decrypt_text(encrypted)
        self.assertEqual(decrypted, original)

    def test_tampered_ciphertext_fails_to_decrypt(self):
        encrypted = encrypt_text("sensitive data")
        tampered = encrypted[:-1] + (b"0" if encrypted[-1:] != b"0" else b"1")
        with self.assertRaises(ValueError):
            decrypt_text(tampered)

    def test_uploaded_dataset_encrypted_at_rest(self):
        import io
        data = {"dataset_file": (io.BytesIO(b"price\n" + b"\n".join(str(100 + i).encode() for i in range(50))), "d.csv")}
        self.client.post("/datasets/upload", data=data, content_type="multipart/form-data")

        conn = sqlite3.connect(Config.DATABASE_PATH)
        row = conn.execute("SELECT encrypted_blob FROM datasets ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        self.assertFalse(row[0].startswith(b"{"))


class TestSessionTimeout(AppTestCase, unittest.TestCase):
    """NFR-SEC-02: Session timeout."""

    def setUp(self):
        super().setUp()
        self.email = register_and_login(self.client, "sessiontimeout")

    def test_active_session_stays_logged_in(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)

    def test_stale_session_is_logged_out(self):
        with self.client.session_transaction() as sess:
            sess["last_active"] = (
                datetime.now(timezone.utc) - timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES + 5)
            ).isoformat()

        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_activity_refreshes_session_timeout(self):
        """Each authenticated request should push the timeout window forward."""
        with self.client.session_transaction() as sess:
            near_limit = datetime.now(timezone.utc) - timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES - 1)
            sess["last_active"] = near_limit.isoformat()

        # This request is still within the window and should succeed, refreshing last_active.
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)

        with self.client.session_transaction() as sess:
            refreshed = datetime.fromisoformat(sess["last_active"])
        self.assertGreater(refreshed, near_limit)


if __name__ == "__main__":
    unittest.main()
