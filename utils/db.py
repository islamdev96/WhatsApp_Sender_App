import sqlite3
import os
import threading

_DB_LOCK = threading.Lock()


class SQLiteStore:
    def __init__(self, db_path=None):
        """Initialize SQLite connection with WAL mode and create tables if needed."""
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
        CREATE TABLE IF NOT EXISTS wa_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created TEXT,
            updated TEXT
        );
        CREATE TABLE IF NOT EXISTS wa_workflow_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER,
            step_order INTEGER,
            body TEXT,
            attachments_json TEXT,
            delay_min INTEGER,
            delay_max INTEGER,
            FOREIGN KEY(workflow_id) REFERENCES wa_workflows(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS wa_scheduled_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            scheduled_time TEXT,
            message TEXT,
            attachments_json TEXT,
            group_name TEXT,
            contacts_json TEXT,
            sending_mode TEXT,
            status TEXT,
            created_at TEXT
        );
        """
        with _DB_LOCK:
            self.conn.executescript(schema)
            self.conn.commit()

    def get_meta(self, key: str) -> str | None:
        """Retrieve a value from the wa_meta key-value store."""
        with _DB_LOCK:
            cur = self.conn.execute("SELECT value FROM wa_meta WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        """Insert or update a value in the wa_meta key-value store."""
        with _DB_LOCK:
            self.conn.execute(
                "INSERT INTO wa_meta(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            self.conn.commit()

    def execute(self, sql: str, params=(), commit=False):
        """Execute a single SQL statement; optionally commit immediately."""
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            if commit:
                self.conn.commit()
            return cur

    def executemany(self, sql: str, params_list, commit: bool=False):
        """Execute a parameterized SQL statement against all parameter sequences."""
        with _DB_LOCK:
            cur = self.conn.executemany(sql, params_list)
            if commit:
                self.conn.commit()
            return cur

    def query_all(self, sql: str, params=()):
        """Execute a SELECT and return all rows as a list of dicts."""
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def query_one(self, sql: str, params=()):
        """Execute a SELECT and return the first row as a dict, or None."""
        with _DB_LOCK:
            cur = self.conn.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def close(self) -> None:
        """Explicitly close the database connection."""
        with _DB_LOCK:
            try:
                self.conn.close()
            except Exception:
                pass
