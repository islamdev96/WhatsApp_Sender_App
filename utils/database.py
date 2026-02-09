import sqlite3
import json
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/whatsapp_sender.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Contacts Table (replacing CSV/Excel for internal storage)
        c.execute('''CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone TEXT UNIQUE,
                        name TEXT,
                        group_name TEXT,
                        status TEXT DEFAULT 'valid',
                        last_sent TIMESTAMP
                    )''')

        # Campaigns Table
        c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        total_contacts INTEGER,
                        sent_count INTEGER,
                        failed_count INTEGER,
                        status TEXT,
                        duration_seconds INTEGER DEFAULT 0
                    )''')
                    
        # Logs Table (Detailed results)
        c.execute('''CREATE TABLE IF NOT EXISTS campaign_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id INTEGER,
                        phone TEXT,
                        status TEXT,
                        error_code TEXT,
                        timestamp TIMESTAMP,
                        FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                    )''')
                    
        # Settings/KV Store
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )''')

        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def log_campaign_start(self, name, total):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO campaigns (name, start_time, total_contacts, status) VALUES (?, ?, ?, ?)",
                  (name, datetime.now(), total, "RUNNING"))
        campaign_id = c.lastrowid
        conn.commit()
        conn.close()
        return campaign_id

    def update_campaign_stats(self, campaign_id, sent, failed, status="RUNNING"):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE campaigns SET sent_count=?, failed_count=?, status=? WHERE id=?",
                  (sent, failed, status, campaign_id))
        conn.commit()
        conn.close()

    def log_result(self, campaign_id, phone, status, error_code="-"):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO campaign_logs (campaign_id, phone, status, error_code, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (campaign_id, phone, status, error_code, datetime.now()))
        conn.commit()
        conn.close()

    def get_recent_campaigns(self, limit=5):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT name, sent_count, failed_count, start_time, status FROM campaigns ORDER BY start_time DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
