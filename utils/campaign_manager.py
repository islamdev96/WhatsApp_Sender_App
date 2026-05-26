"""
Campaign Manager - Persistent campaign history with analytics.
Uses SQLite for scalability and migrates from campaigns.json once.
"""
import json
import os
import datetime
import tempfile
from utils.db import SQLiteStore
from utils.logger import logger, log_exception


class CampaignManager:
    def __init__(self, campaigns_path=None, db_path=None, use_sqlite=True):
        if campaigns_path is None:
            campaigns_path = os.path.join(os.getcwd(), "campaigns.json")
        self.campaigns_path = campaigns_path
        self.store = SQLiteStore(db_path=db_path) if use_sqlite else None
        self.campaigns = []
        if self.store:
            self._migrate_from_json_once()
        else:
            self._load_from_json()

    def _load_from_json(self):
        try:
            if os.path.exists(self.campaigns_path):
                with open(self.campaigns_path, "r", encoding="utf-8") as f:
                    campaigns = json.load(f)
                if isinstance(campaigns, list):
                    self.campaigns = [item for item in campaigns if isinstance(item, dict)]
                    if len(self.campaigns) != len(campaigns):
                        logger.warning("Skipped malformed campaign entries while loading %s", self.campaigns_path)
                else:
                    logger.warning("Ignoring campaigns file with unexpected format: %s", self.campaigns_path)
                    self.campaigns = []
        except json.JSONDecodeError as exc:
            logger.error("Invalid campaigns JSON in %s: %s", self.campaigns_path, exc)
            self.campaigns = []
        except OSError as exc:
            logger.error("Could not read campaigns file %s: %s", self.campaigns_path, exc)
            self.campaigns = []
        except Exception as exc:
            log_exception(f"Unexpected error loading campaigns from {self.campaigns_path}", exc)
            self.campaigns = []

    def _save_to_json(self):
        """Atomically persist campaigns list to JSON.

        Writes to a temporary file first then renames, so a crash during
        write never leaves a half-written (corrupt) campaigns file.
        """
        try:
            dir_name = os.path.dirname(self.campaigns_path) or "."
            fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.campaigns, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, self.campaigns_path)
            except BaseException:
                # Clean up temp file on any failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            logger.error("Could not write campaigns file %s: %s", self.campaigns_path, exc)
        except Exception as exc:
            log_exception(f"Unexpected error saving campaigns to {self.campaigns_path}", exc)

    def _migrate_from_json_once(self):
        if self.store.get_meta("campaigns_migrated") == "1":
            return
        if not os.path.exists(self.campaigns_path):
            self.store.set_meta("campaigns_migrated", "1")
            return
        try:
            with open(self.campaigns_path, "r", encoding="utf-8") as f:
                campaigns = json.load(f)
            if not isinstance(campaigns, list):
                logger.warning("Skipping campaigns migration because JSON root is not a list: %s", self.campaigns_path)
                campaigns = []
        except json.JSONDecodeError as exc:
            logger.error("Invalid campaigns JSON during migration from %s: %s", self.campaigns_path, exc)
            campaigns = []
        except OSError as exc:
            logger.error("Could not read campaigns file during migration %s: %s", self.campaigns_path, exc)
            campaigns = []
        except Exception as exc:
            log_exception(f"Unexpected error reading campaigns migration source {self.campaigns_path}", exc)
            campaigns = []

        # Batch all migration inserts in a single transaction for performance.
        try:
            self.store.execute("BEGIN", commit=False)
            for c in campaigns:
                if not isinstance(c, dict):
                    logger.warning("Skipping malformed campaign entry during migration")
                    continue
                name = c.get("name")
                try:
                    date = c.get("date") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    total = int(c.get("total", 0))
                    sent = int(c.get("sent", 0))
                    failed = int(c.get("failed", 0))
                    invalid = int(c.get("invalid", 0))
                    duration_seconds = int(c.get("duration_seconds", 0))
                    success_rate = float(c.get("success_rate", 0))
                    csv_path = c.get("csv_path")

                    cur = self.store.execute(
                        "INSERT INTO wa_campaigns(name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path) "
                        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path),
                        commit=False,
                    )
                    campaign_id = cur.lastrowid
                    results = c.get("results", [])
                    if isinstance(results, list) and results:
                        params = [
                            (
                                campaign_id,
                                r.get("phone"),
                                r.get("name"),
                                r.get("status"),
                                r.get("error_code"),
                                r.get("timestamp"),
                            )
                            for r in results
                            if isinstance(r, dict)
                        ]
                        if params:
                            self.store.executemany(
                                "INSERT INTO wa_campaign_results(campaign_id, phone, name, status, error_code, timestamp) "
                                "VALUES(?, ?, ?, ?, ?, ?)",
                                params,
                                commit=False,
                            )
                except (ValueError, TypeError) as exc:
                    logger.warning("Skipping campaign with invalid numeric fields during migration: %s", exc)
                except Exception as exc:
                    log_exception("Unexpected error migrating campaign entry", exc)
            self.store.execute("COMMIT", commit=False)
        except Exception as exc:
            # Rollback on any catastrophic failure to avoid partial state
            try:
                self.store.execute("ROLLBACK", commit=False)
            except Exception:
                pass
            log_exception("Migration transaction failed", exc)
        self.store.set_meta("campaigns_migrated", "1")

    def add_campaign(self, name, total, sent, failed, invalid,
                     duration_seconds, results_log, csv_path=None):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_rate = round(sent / total * 100, 1) if total else 0

        if not self.store:
            campaign = {
                "id": len(self.campaigns) + 1,
                "name": name,
                "date": now,
                "total": total,
                "sent": sent,
                "failed": failed,
                "invalid": invalid,
                "duration_seconds": int(duration_seconds),
                "success_rate": success_rate,
                "csv_path": csv_path,
                "results": results_log,
            }
            self.campaigns.append(campaign)
            self._save_to_json()
            return campaign

        # Wrap campaign + results in a single transaction so they
        # are never partially written (atomicity).
        try:
            self.store.execute("BEGIN", commit=False)
            cur = self.store.execute(
                "INSERT INTO wa_campaigns(name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, now, total, sent, failed, invalid, int(duration_seconds), success_rate, csv_path),
                commit=False,
            )
            campaign_id = cur.lastrowid
            if results_log:
                params = [
                    (
                        campaign_id,
                        r.get("phone"),
                        r.get("name"),
                        r.get("status"),
                        r.get("error_code"),
                        r.get("timestamp"),
                    )
                    for r in results_log
                ]
                self.store.executemany(
                    "INSERT INTO wa_campaign_results(campaign_id, phone, name, status, error_code, timestamp) "
                    "VALUES(?, ?, ?, ?, ?, ?)",
                    params,
                    commit=False,
                )
            self.store.execute("COMMIT", commit=False)
        except Exception as exc:
            try:
                self.store.execute("ROLLBACK", commit=False)
            except Exception:
                pass
            log_exception("Failed to save campaign", exc)
            campaign_id = None
        return {
            "id": campaign_id,
            "name": name,
            "date": now,
            "total": total,
            "sent": sent,
            "failed": failed,
            "invalid": invalid,
            "duration_seconds": int(duration_seconds),
            "success_rate": success_rate,
            "csv_path": csv_path,
            "results": results_log,
        }

    def get_all(self):
        if not self.store:
            return list(reversed(self.campaigns))
        return self.store.query_all(
            "SELECT id, name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path "
            "FROM wa_campaigns ORDER BY id DESC"
        )

    def get_by_id(self, campaign_id):
        if not self.store:
            for c in self.campaigns:
                if c.get("id") == campaign_id:
                    return c
            return None
        c = self.store.query_one(
            "SELECT id, name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path "
            "FROM wa_campaigns WHERE id = ?",
            (campaign_id,),
        )
        if not c:
            return None
        results = self.store.query_all(
            "SELECT phone, name, status, error_code, timestamp FROM wa_campaign_results WHERE campaign_id = ?",
            (campaign_id,),
        )
        c["results"] = results
        return c

    def get_latest(self, n=5):
        if not self.store:
            return list(reversed(self.campaigns[-n:]))
        return self.store.query_all(
            "SELECT id, name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path "
            "FROM wa_campaigns ORDER BY id DESC LIMIT ?",
            (n,),
        )

    def delete_campaign(self, campaign_id):
        if not self.store:
            self.campaigns = [c for c in self.campaigns if c.get("id") != campaign_id]
            self._save_to_json()
            return
        self.store.execute("DELETE FROM wa_campaigns WHERE id = ?", (campaign_id,), commit=True)

    def get_aggregate_stats(self):
        if not self.store:
            if not self.campaigns:
                return {
                    "total_campaigns": 0,
                    "total_messages": 0,
                    "total_sent": 0,
                    "total_failed": 0,
                    "total_invalid": 0,
                    "overall_success_rate": 0,
                    "total_duration_minutes": 0,
                    "avg_success_rate": 0,
                    "best_campaign": None,
                    "worst_campaign": None,
                }
            total_campaigns = len(self.campaigns)
            total_messages = sum(c.get("total", 0) for c in self.campaigns)
            total_sent = sum(c.get("sent", 0) for c in self.campaigns)
            total_failed = sum(c.get("failed", 0) for c in self.campaigns)
            total_invalid = sum(c.get("invalid", 0) for c in self.campaigns)
            total_duration = sum(c.get("duration_seconds", 0) for c in self.campaigns)
            overall_rate = round(total_sent / total_messages * 100, 1) if total_messages else 0
            rates = [(c.get("success_rate", 0), c.get("name", ""), c.get("id")) for c in self.campaigns]
            best = max(rates, key=lambda x: x[0])
            worst = min(rates, key=lambda x: x[0])
            return {
                "total_campaigns": total_campaigns,
                "total_messages": total_messages,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_invalid": total_invalid,
                "overall_success_rate": overall_rate,
                "total_duration_minutes": round(total_duration / 60, 1),
                "avg_success_rate": round(sum(r[0] for r in rates) / total_campaigns, 1),
                "best_campaign": {"name": best[1], "rate": best[0], "id": best[2]},
                "worst_campaign": {"name": worst[1], "rate": worst[0], "id": worst[2]},
            }

        row = self.store.query_one(
            "SELECT COUNT(*) AS total_campaigns, "
            "COALESCE(SUM(total), 0) AS total_messages, "
            "COALESCE(SUM(sent), 0) AS total_sent, "
            "COALESCE(SUM(failed), 0) AS total_failed, "
            "COALESCE(SUM(invalid), 0) AS total_invalid, "
            "COALESCE(SUM(duration_seconds), 0) AS total_duration "
            "FROM wa_campaigns"
        )
        total_campaigns = row["total_campaigns"]
        total_messages = row["total_messages"]
        total_sent = row["total_sent"]
        total_failed = row["total_failed"]
        total_invalid = row["total_invalid"]
        total_duration = row["total_duration"]
        overall_rate = round(total_sent / total_messages * 100, 1) if total_messages else 0
        best = self.store.query_one(
            "SELECT id, name, success_rate FROM wa_campaigns ORDER BY success_rate DESC LIMIT 1"
        )
        worst = self.store.query_one(
            "SELECT id, name, success_rate FROM wa_campaigns ORDER BY success_rate ASC LIMIT 1"
        )
        avg_rate_row = self.store.query_one("SELECT AVG(success_rate) AS avg_rate FROM wa_campaigns")
        avg_rate = round(avg_rate_row["avg_rate"], 1) if avg_rate_row and avg_rate_row["avg_rate"] is not None else 0

        return {
            "total_campaigns": total_campaigns,
            "total_messages": total_messages,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_invalid": total_invalid,
            "overall_success_rate": overall_rate,
            "total_duration_minutes": round(total_duration / 60, 1),
            "avg_success_rate": avg_rate,
            "best_campaign": {"name": best["name"], "rate": best["success_rate"], "id": best["id"]} if best else None,
            "worst_campaign": {"name": worst["name"], "rate": worst["success_rate"], "id": worst["id"]} if worst else None,
        }

    def get_error_breakdown(self):
        if not self.store:
            errors = {}
            for c in self.campaigns:
                for r in c.get("results", []):
                    code = r.get("error_code", "")
                    if code:
                        errors[code] = errors.get(code, 0) + 1
            return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True))
        rows = self.store.query_all(
            "SELECT error_code, COUNT(*) AS cnt FROM wa_campaign_results "
            "WHERE error_code IS NOT NULL AND error_code != '' "
            "GROUP BY error_code ORDER BY cnt DESC"
        )
        return {r["error_code"]: r["cnt"] for r in rows}
