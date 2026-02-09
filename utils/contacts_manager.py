"""
Contacts Manager — Manage contact groups for targeted sending.
Groups are stored in contact_groups.json with name, contacts list, and metadata.
"""
import json
import os
import datetime


class ContactsManager:
    def __init__(self, groups_path=None):
        if groups_path is None:
            groups_path = os.path.join(os.getcwd(), "contact_groups.json")
        self.groups_path = groups_path
        self.groups = []
        self.load()

    def load(self):
        """Load groups from file."""
        try:
            if os.path.exists(self.groups_path):
                with open(self.groups_path, 'r', encoding='utf-8') as f:
                    self.groups = json.load(f)
        except Exception:
            self.groups = []

    def save(self):
        """Persist groups to disk."""
        try:
            with open(self.groups_path, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_all(self):
        """Return list of all groups."""
        return list(self.groups)

    def get_names(self):
        """Return list of group names."""
        return [g.get("name", "") for g in self.groups]

    def get_by_name(self, name):
        """Get a group by its name."""
        for g in self.groups:
            if g.get("name") == name:
                return g
        return None

    def create_group(self, name, contacts=None):
        """Create a new group. contacts = list of {phone, name} dicts."""
        if self.get_by_name(name):
            return False  # Already exists
        group = {
            "name": name,
            "contacts": contacts or [],
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.groups.append(group)
        self.save()
        return True

    def update_contacts(self, name, contacts):
        """Replace the contacts list for a group."""
        g = self.get_by_name(name)
        if g:
            g["contacts"] = contacts
            g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
            return True
        return False

    def add_contacts(self, name, new_contacts):
        """Add contacts to a group (avoiding duplicates by phone)."""
        g = self.get_by_name(name)
        if not g:
            return False
        existing_phones = {c.get("phone") for c in g["contacts"]}
        added = 0
        for c in new_contacts:
            if c.get("phone") not in existing_phones:
                g["contacts"].append(c)
                existing_phones.add(c.get("phone"))
                added += 1
        if added:
            g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
        return added

    def remove_contact(self, group_name, phone):
        """Remove a contact by phone from a group."""
        g = self.get_by_name(group_name)
        if g:
            before = len(g["contacts"])
            g["contacts"] = [c for c in g["contacts"] if c.get("phone") != phone]
            if len(g["contacts"]) < before:
                g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
                return True
        return False

    def delete_group(self, name):
        """Delete a group by name."""
        self.groups = [g for g in self.groups if g.get("name") != name]
        self.save()

    def rename_group(self, old_name, new_name):
        """Rename a group."""
        if self.get_by_name(new_name):
            return False  # Target name exists
        g = self.get_by_name(old_name)
        if g:
            g["name"] = new_name
            g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
            return True
        return False

    def get_contact_count(self, name):
        """Get the number of contacts in a group."""
        g = self.get_by_name(name)
        return len(g["contacts"]) if g else 0
