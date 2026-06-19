using System;
using System.IO;
using Microsoft.Data.Sqlite;
using Dapper;

namespace WhatsAppSender.Core.Data;

public class Database
{
    private readonly string _connectionString;
    private readonly object _dbLock = new();

    public Database(string? dbPath = null)
    {
        if (string.IsNullOrEmpty(dbPath))
        {
            var dataDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data");
            if (!Directory.Exists(dataDir))
            {
                Directory.CreateDirectory(dataDir);
            }
            dbPath = Path.Combine(dataDir, "whatsapp_sender.db");
        }
        else
        {
            var dir = Path.GetDirectoryName(dbPath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
        }

        _connectionString = $"Data Source={dbPath};";
        Initialize();
    }

    public SqliteConnection OpenConnection()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        return conn;
    }

    private void Initialize()
    {
        lock (_dbLock)
        {
            using var conn = OpenConnection();
            conn.Execute("PRAGMA journal_mode=WAL;");
            conn.Execute("PRAGMA foreign_keys=ON;");

            const string schema = @"
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
                );";

            conn.Execute(schema);
        }
    }

    public string? GetMeta(string key)
    {
        lock (_dbLock)
        {
            using var conn = OpenConnection();
            return conn.QueryFirstOrDefault<string>(
                "SELECT value FROM wa_meta WHERE key = @Key", new { Key = key });
        }
    }

    public void SetMeta(string key, string value)
    {
        lock (_dbLock)
        {
            using var conn = OpenConnection();
            conn.Execute(@"
                INSERT INTO wa_meta (key, value) VALUES (@Key, @Value)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                new { Key = key, Value = value });
        }
    }
}
