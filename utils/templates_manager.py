"""
Templates Manager — Save, load, and manage reusable message templates.
Templates are stored in templates.json with name + body.
"""
import json
import os
import datetime


class TemplatesManager:
    def __init__(self, templates_path=None):
        if templates_path is None:
            templates_path = os.path.join(os.getcwd(), "templates.json")
        self.templates_path = templates_path
        self.templates = []
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

    def get_all(self):
        """Return list of all templates."""
        return list(self.templates)

    def get_names(self):
        """Return list of template names."""
        return [t.get("name", "") for t in self.templates]

    def get_by_name(self, name):
        """Get a template by its name."""
        for t in self.templates:
            if t.get("name") == name:
                return t
        return None

    def add(self, name, body):
        """Add a new template or update existing one with the same name."""
        for t in self.templates:
            if t.get("name") == name:
                t["body"] = body
                t["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
                return
        self.templates.append({
            "name": name,
            "body": body,
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.save()

    def delete(self, name):
        """Delete a template by name."""
        self.templates = [t for t in self.templates if t.get("name") != name]
        self.save()

    def rename(self, old_name, new_name):
        """Rename a template."""
        t = self.get_by_name(old_name)
        if t:
            t["name"] = new_name
            t["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
