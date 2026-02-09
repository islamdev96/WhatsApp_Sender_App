"""
Templates Manager — Save, load, and manage reusable message templates.
Templates are stored in templates.json with name + body.
"""
import json
import os
import datetime
from utils.db import SQLiteStore


class TemplatesManager:
    def __init__(self, templates_path=None, db_path=None, use_sqlite=True):
        if templates_path is None:
            templates_path = os.path.join(os.getcwd(), "templates.json")
        self.templates_path = templates_path
        self.templates = []
        self.store = SQLiteStore(db_path=db_path) if use_sqlite else None
        if self.store:
            self._migrate_from_json_once()
        else:
            self.load()

    def load(self):
        """Load templates from file."""
        try:
            if os.path.exists(self.templates_path):
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
        except Exception:
            self.templates = []

    def save(self):
        """Persist templates to disk."""
        try:
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _migrate_from_json_once(self):
        if self.store.get_meta("templates_migrated") == "1":
            return
        if not os.path.exists(self.templates_path):
            self.store.set_meta("templates_migrated", "1")
            return
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        except Exception:
            templates = []
        for t in templates:
            name = t.get("name")
            body = t.get("body", "")
            created = t.get("created") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            updated = t.get("updated") or created
            if not name:
                continue
            existing = self.store.query_one("SELECT id FROM wa_templates WHERE name = ?", (name,))
            if not existing:
                self.store.execute(
                    "INSERT INTO wa_templates(name, body, created, updated) VALUES(?, ?, ?, ?)",
                    (name, body, created, updated),
                    commit=True,
                )
        self.store.set_meta("templates_migrated", "1")

    def get_all(self):
        """Return list of all templates."""
        if not self.store:
            return list(self.templates)
        return self.store.query_all("SELECT name, body, created, updated FROM wa_templates ORDER BY id DESC")

    def get_names(self):
        """Return list of template names."""
        if not self.store:
            return [t.get("name", "") for t in self.templates]
        rows = self.store.query_all("SELECT name FROM wa_templates ORDER BY id DESC")
        return [r.get("name", "") for r in rows]

    def get_by_name(self, name):
        """Get a template by its name."""
        if not self.store:
            for t in self.templates:
                if t.get("name") == name:
                    return t
            return None
        return self.store.query_one("SELECT name, body, created, updated FROM wa_templates WHERE name = ?", (name,))

    def add(self, name, body):
        """Add a new template or update existing one with the same name."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not self.store:
            for t in self.templates:
                if t.get("name") == name:
                    t["body"] = body
                    t["updated"] = now
                    self.save()
                    return
            self.templates.append({"name": name, "body": body, "created": now, "updated": now})
            self.save()
            return
        existing = self.store.query_one("SELECT id FROM wa_templates WHERE name = ?", (name,))
        if existing:
            self.store.execute(
                "UPDATE wa_templates SET body = ?, updated = ? WHERE name = ?",
                (body, now, name),
                commit=True,
            )
        else:
            self.store.execute(
                "INSERT INTO wa_templates(name, body, created, updated) VALUES(?, ?, ?, ?)",
                (name, body, now, now),
                commit=True,
            )

    def delete(self, name):
        """Delete a template by name."""
        if not self.store:
            self.templates = [t for t in self.templates if t.get("name") != name]
            self.save()
            return
        self.store.execute("DELETE FROM wa_templates WHERE name = ?", (name,), commit=True)

    def rename(self, old_name, new_name):
        """Rename a template."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not self.store:
            t = self.get_by_name(old_name)
            if t:
                t["name"] = new_name
                t["updated"] = now
                self.save()
            return
        self.store.execute(
            "UPDATE wa_templates SET name = ?, updated = ? WHERE name = ?",
            (new_name, now, old_name),
            commit=True,
        )
