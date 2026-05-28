"""
Tests for utils/db.py — SQLiteStore CRUD, meta store, and close behavior.
"""
import os
import tempfile
import unittest

from utils.db import SQLiteStore


class TestSQLiteStore(unittest.TestCase):
    """Test the SQLiteStore wrapper for correctness and edge cases."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test.db")
        self.store = SQLiteStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_meta_set_and_get(self):
        """set_meta → get_meta round trip."""
        self.store.set_meta("version", "2.0")
        self.assertEqual(self.store.get_meta("version"), "2.0")

    def test_meta_overwrite(self):
        """set_meta overwrites existing value (UPSERT)."""
        self.store.set_meta("k", "old")
        self.store.set_meta("k", "new")
        self.assertEqual(self.store.get_meta("k"), "new")

    def test_meta_missing_key_returns_none(self):
        """get_meta on non-existent key returns None."""
        self.assertIsNone(self.store.get_meta("nonexistent"))

    def test_execute_and_query_all(self):
        """execute INSERT + query_all returns dicts."""
        self.store.execute(
            "INSERT INTO wa_meta(key, value) VALUES(?, ?)",
            ("a", "1"), commit=True,
        )
        rows = self.store.query_all("SELECT key, value FROM wa_meta WHERE key = ?", ("a",))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["key"], "a")
        self.assertEqual(rows[0]["value"], "1")

    def test_query_one_returns_dict_or_none(self):
        """query_one returns a dict for existing row, None for missing."""
        self.store.set_meta("x", "42")
        row = self.store.query_one("SELECT value FROM wa_meta WHERE key = ?", ("x",))
        self.assertIsNotNone(row)
        self.assertEqual(row["value"], "42")

        missing = self.store.query_one("SELECT value FROM wa_meta WHERE key = ?", ("zzz",))
        self.assertIsNone(missing)

    def test_executemany(self):
        """executemany inserts multiple rows in one call."""
        params = [("k1", "v1"), ("k2", "v2"), ("k3", "v3")]
        self.store.executemany(
            "INSERT INTO wa_meta(key, value) VALUES(?, ?)", params, commit=True,
        )
        rows = self.store.query_all("SELECT key FROM wa_meta ORDER BY key")
        self.assertEqual(len(rows), 3)

    def test_close_is_idempotent(self):
        """Calling close() multiple times should not raise."""
        self.store.close()
        self.store.close()  # Should not raise


class TestSQLiteStoreFile(unittest.TestCase):
    """Test database file creation."""

    def test_creates_db_file(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "subdir", "test.db")
        store = SQLiteStore(db_path=path)
        store.set_meta("test", "1")
        store.close()
        self.assertTrue(os.path.exists(path))
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
