import sqlite3
import os
import threading

_DB_LOCK = threading.Lock()


class SQLiteStore:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "data", "whatsapp_sender.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with _DB_LOCK:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA foreign_keys=ON;")
        self._init_schema()

    def _init_schema(self):
        schema = """
        CREATE TABLE IF NOT EXISTS wa_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS wa_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created TEXT,
            updated TEXT
        );
        CREATE TABLE IF NOT EXISTS wa_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            phone TEXT,
            name TEXT,
            UNIQUE(group_id, phone),
            FOREIGN KEY(group_id) REFERENCES wa_groups(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS wa_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            body TEXT,
            created TEXT,
            updated TEXT
        );
        CREATE TABLE IF NOT EXISTS wa_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            total INTEGER,
            sent INTEGER,
            failed INTEGER,
            invalid INTEGER,
            duration_seconds INTEGER,
            success_rate REAL,
            csv_path TEXT
        );
        CREATE TABLE IF NOT EXISTS wa_campaign_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            phone TEXT,
            name TEXT,
            status TEXT,
            error_code TEXT,
            timestamp TEXT,
            FOREIGN KEY(campaign_id) REFERENCES wa_campaigns(id) ON DELETE CASCADE
        );
        """
        with _DB_LOCK:
            self.conn.executescript(schema)
            self.conn.commit()

    def get_meta(self, key):
        with _DB_LOCK:
            cur = self.conn.execute("SELECT value FROM wa_meta WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_meta(self, key, value):
        with _DB_LOCK:
            self.conn.execute(
                "INSERT INTO wa_meta(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            self.conn.commit()

    def execute(self, sql, params=(), commit=False):
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            if commit:
                self.conn.commit()
            return cur

    def executemany(self, sql, params_list, commit=False):
        with _DB_LOCK:
            cur = self.conn.executemany(sql, params_list)
            if commit:
                self.conn.commit()
            return cur

    def query_all(self, sql, params=()):
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def query_one(self, sql, params=()):
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
