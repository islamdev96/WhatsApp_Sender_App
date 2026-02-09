"""
Campaign Manager — Persistent campaign history with analytics.
Each campaign is saved as a JSON record in campaigns.json with
full metadata, per-contact results, and aggregate stats.
"""
import json
import os
import datetime


class CampaignManager:
    def __init__(self, campaigns_path=None):
        if campaigns_path is None:
            campaigns_path = os.path.join(os.getcwd(), "campaigns.json")
        self.campaigns_path = campaigns_path
        self.campaigns = []
        self.load()

    def load(self):
        """Load campaigns from disk."""
        try:
            if os.path.exists(self.campaigns_path):
                with open(self.campaigns_path, 'r', encoding='utf-8') as f:
                    self.campaigns = json.load(f)
        except Exception:
            self.campaigns = []

    def save(self):
        """Persist all campaigns to disk."""
        try:
            with open(self.campaigns_path, 'w', encoding='utf-8') as f:
                json.dump(self.campaigns, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_campaign(self, name, total, sent, failed, invalid,
                     duration_seconds, results_log, csv_path=None):
        """Record a completed campaign."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        campaign = {
            "id": len(self.campaigns) + 1,
            "name": name,
            "date": now,
            "total": total,
            "sent": sent,
            "failed": failed,
            "invalid": invalid,
            "duration_seconds": int(duration_seconds),
            "success_rate": round(sent / total * 100, 1) if total else 0,
            "csv_path": csv_path,
            "results": results_log,  # list of {phone, name, status, error_code, timestamp}
        }
        self.campaigns.append(campaign)
        self.save()
        return campaign

    def get_all(self):
        """Return all campaigns (newest first)."""
        return list(reversed(self.campaigns))

    def get_by_id(self, campaign_id):
        """Get a specific campaign by ID."""
        for c in self.campaigns:
            if c.get("id") == campaign_id:
                return c
        return None

    def get_latest(self, n=5):
        """Return the latest N campaigns."""
        return list(reversed(self.campaigns[-n:]))

    def delete_campaign(self, campaign_id):
        """Delete a campaign by ID."""
        self.campaigns = [c for c in self.campaigns if c.get("id") != campaign_id]
        self.save()

    def get_aggregate_stats(self):
        """Return aggregate stats across all campaigns."""
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

    def get_error_breakdown(self):
        """Return error code frequency across all campaigns."""
        errors = {}
        for c in self.campaigns:
            for r in c.get("results", []):
                code = r.get("error_code", "")
                if code:
                    errors[code] = errors.get(code, 0) + 1
        return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True))
