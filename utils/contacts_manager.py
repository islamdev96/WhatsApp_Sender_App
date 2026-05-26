"""
Contacts Manager — Manage contact groups for targeted sending.
Groups are stored in contact_groups.json with name, contacts list, and metadata.
"""
import json
import os
import datetime
from utils.db import SQLiteStore
from utils.logger import logger, log_exception


def _clean_contacts(contacts):
    return [c for c in contacts or [] if isinstance(c, dict) and c.get("phone")]


def _contact_params(group_id, contacts):
    return [(group_id, c.get("phone"), c.get("name", "")) for c in _clean_contacts(contacts)]


class ContactsManager:
    def __init__(self, groups_path=None, db_path=None, use_sqlite=True):
        if groups_path is None:
            groups_path = os.path.join(os.getcwd(), "contact_groups.json")
        self.groups_path = groups_path
        self.groups = []
        self.store = SQLiteStore(db_path=db_path) if use_sqlite else None
        if self.store:
            self._migrate_from_json_once()
        else:
            self.load()

    def load(self):
        """Load groups from file."""
        try:
            if os.path.exists(self.groups_path):
                with open(self.groups_path, 'r', encoding='utf-8') as f:
                    groups = json.load(f)
                if isinstance(groups, list):
                    self.groups = [item for item in groups if isinstance(item, dict)]
                    if len(self.groups) != len(groups):
                        logger.warning("Skipped malformed contact group entries while loading %s", self.groups_path)
                else:
                    logger.warning("Ignoring contact groups file with unexpected format: %s", self.groups_path)
                    self.groups = []
        except json.JSONDecodeError as exc:
            logger.error("Invalid contact groups JSON in %s: %s", self.groups_path, exc)
            self.groups = []
        except OSError as exc:
            logger.error("Could not read contact groups file %s: %s", self.groups_path, exc)
            self.groups = []
        except Exception as exc:
            log_exception(f"Unexpected error loading contact groups from {self.groups_path}", exc)
            self.groups = []

    def save(self):
        """Persist groups to disk."""
        try:
            with open(self.groups_path, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.error("Could not write contact groups file %s: %s", self.groups_path, exc)
        except Exception as exc:
            log_exception(f"Unexpected error saving contact groups to {self.groups_path}", exc)

    def _migrate_from_json_once(self):
        if self.store.get_meta("contacts_migrated") == "1":
            return
        if not os.path.exists(self.groups_path):
            self.store.set_meta("contacts_migrated", "1")
            return
        try:
            with open(self.groups_path, 'r', encoding='utf-8') as f:
                groups = json.load(f)
            if not isinstance(groups, list):
                logger.warning("Skipping contacts migration because JSON root is not a list: %s", self.groups_path)
                groups = []
        except json.JSONDecodeError as exc:
            logger.error("Invalid contact groups JSON during migration from %s: %s", self.groups_path, exc)
            groups = []
        except OSError as exc:
            logger.error("Could not read contact groups file during migration %s: %s", self.groups_path, exc)
            groups = []
        except Exception as exc:
            log_exception(f"Unexpected error reading contact groups migration source {self.groups_path}", exc)
            groups = []

        for g in groups:
            if not isinstance(g, dict):
                logger.warning("Skipping malformed contact group during migration")
                continue
            name = g.get("name")
            if not name:
                continue
            created = g.get("created") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            updated = g.get("updated") or created
            existing = self.store.query_one("SELECT id FROM wa_groups WHERE name = ?", (name,))
            if not existing:
                cur = self.store.execute(
                    "INSERT INTO wa_groups(name, created, updated) VALUES(?, ?, ?)",
                    (name, created, updated),
                    commit=True,
                )
                group_id = cur.lastrowid
            else:
                group_id = existing["id"]
            contacts = g.get("contacts", [])
            if isinstance(contacts, list) and contacts:
                params = _contact_params(group_id, contacts)
                if params:
                    self.store.executemany(
                        "INSERT OR IGNORE INTO wa_contacts(group_id, phone, name) VALUES(?, ?, ?)",
                        params,
                        commit=True,
                    )
        self.store.set_meta("contacts_migrated", "1")

    def get_all(self):
        """Return list of all groups."""
        if not self.store:
            return list(self.groups)
        groups = self.store.query_all("SELECT id, name, created, updated FROM wa_groups ORDER BY id DESC")
        out = []
        for g in groups:
            contacts = self.store.query_all(
                "SELECT phone, name FROM wa_contacts WHERE group_id = ? ORDER BY id",
                (g["id"],),
            )
            out.append({
                "name": g["name"],
                "contacts": contacts,
                "created": g.get("created"),
                "updated": g.get("updated"),
            })
        return out

    def get_names(self):
        """Return list of group names."""
        if not self.store:
            return [g.get("name", "") for g in self.groups]
        rows = self.store.query_all("SELECT name FROM wa_groups ORDER BY id DESC")
        return [r.get("name", "") for r in rows]

    def get_by_name(self, name):
        """Get a group by its name."""
        if not self.store:
            for g in self.groups:
                if g.get("name") == name:
                    return g
            return None
        g = self.store.query_one("SELECT id, name, created, updated FROM wa_groups WHERE name = ?", (name,))
        if not g:
            return None
        contacts = self.store.query_all(
            "SELECT phone, name FROM wa_contacts WHERE group_id = ? ORDER BY id",
            (g["id"],),
        )
        return {"name": g["name"], "contacts": contacts, "created": g.get("created"), "updated": g.get("updated")}

    def create_group(self, name, contacts=None):
        """Create a new group. contacts = list of {phone, name} dicts."""
        if self.get_by_name(name):
            return False  # Already exists
        created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not self.store:
            group = {"name": name, "contacts": _clean_contacts(contacts), "created": created, "updated": created}
            self.groups.append(group)
            self.save()
            return True
        cur = self.store.execute(
            "INSERT INTO wa_groups(name, created, updated) VALUES(?, ?, ?)",
            (name, created, created),
            commit=True,
        )
        group_id = cur.lastrowid
        if contacts:
            params = _contact_params(group_id, contacts)
            if params:
                self.store.executemany(
                    "INSERT OR IGNORE INTO wa_contacts(group_id, phone, name) VALUES(?, ?, ?)",
                    params,
                    commit=True,
                )
        return True

    def update_contacts(self, name, contacts):
        """Replace the contacts list for a group."""
        if not self.store:
            g = self.get_by_name(name)
            if g:
                g["contacts"] = _clean_contacts(contacts)
                g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
                return True
            return False
        g = self.store.query_one("SELECT id FROM wa_groups WHERE name = ?", (name,))
        if not g:
            return False
        group_id = g["id"]
        self.store.execute("DELETE FROM wa_contacts WHERE group_id = ?", (group_id,), commit=True)
        params = _contact_params(group_id, contacts)
        if params:
            self.store.executemany(
                "INSERT OR IGNORE INTO wa_contacts(group_id, phone, name) VALUES(?, ?, ?)",
                params,
                commit=True,
            )
        self.store.execute(
            "UPDATE wa_groups SET updated = ? WHERE id = ?",
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), group_id),
            commit=True,
        )
        return True

    def add_contacts(self, name, new_contacts):
        """Add contacts to a group (avoiding duplicates by phone)."""
        if not self.store:
            g = self.get_by_name(name)
            if not g:
                return False
            existing_phones = {c.get("phone") for c in _clean_contacts(g.get("contacts", []))}
            added = 0
            for c in _clean_contacts(new_contacts):
                if c.get("phone") not in existing_phones:
                    g["contacts"].append(c)
                    existing_phones.add(c.get("phone"))
                    added += 1
            if added:
                g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
            return added
        g = self.store.query_one("SELECT id FROM wa_groups WHERE name = ?", (name,))
        if not g:
            return False
        group_id = g["id"]
        before = self.store.query_one("SELECT COUNT(*) AS c FROM wa_contacts WHERE group_id = ?", (group_id,))["c"]
        params = _contact_params(group_id, new_contacts)
        if params:
            self.store.executemany(
                "INSERT OR IGNORE INTO wa_contacts(group_id, phone, name) VALUES(?, ?, ?)",
                params,
                commit=True,
            )
        after = self.store.query_one("SELECT COUNT(*) AS c FROM wa_contacts WHERE group_id = ?", (group_id,))["c"]
        added = max(0, after - before)
        if added:
            self.store.execute(
                "UPDATE wa_groups SET updated = ? WHERE id = ?",
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), group_id),
                commit=True,
            )
        return added

    def remove_contact(self, group_name, phone):
        """Remove a contact by phone from a group."""
        if not self.store:
            g = self.get_by_name(group_name)
            if g:
                before = len(g["contacts"])
                g["contacts"] = [c for c in _clean_contacts(g.get("contacts", [])) if c.get("phone") != phone]
                if len(g["contacts"]) < before:
                    g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    self.save()
                    return True
            return False
        g = self.store.query_one("SELECT id FROM wa_groups WHERE name = ?", (group_name,))
        if not g:
            return False
        cur = self.store.execute(
            "DELETE FROM wa_contacts WHERE group_id = ? AND phone = ?",
            (g["id"], phone),
            commit=True,
        )
        if cur.rowcount:
            self.store.execute(
                "UPDATE wa_groups SET updated = ? WHERE id = ?",
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), g["id"]),
                commit=True,
            )
            return True
        return False

    def delete_group(self, name):
        """Delete a group by name."""
        if not self.store:
            self.groups = [g for g in self.groups if g.get("name") != name]
            self.save()
            return
        self.store.execute("DELETE FROM wa_groups WHERE name = ?", (name,), commit=True)

    def rename_group(self, old_name, new_name):
        """Rename a group."""
        if self.get_by_name(new_name):
            return False  # Target name exists
        if not self.store:
            g = self.get_by_name(old_name)
            if g:
                g["name"] = new_name
                g["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
                return True
            return False
        cur = self.store.execute(
            "UPDATE wa_groups SET name = ?, updated = ? WHERE name = ?",
            (new_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), old_name),
            commit=True,
        )
        return cur.rowcount > 0

    def get_contact_count(self, name):
        """Get the number of contacts in a group."""
        if not self.store:
            g = self.get_by_name(name)
            return len(_clean_contacts(g.get("contacts", []))) if g else 0
        g = self.store.query_one("SELECT id FROM wa_groups WHERE name = ?", (name,))
        if not g:
            return 0
        row = self.store.query_one("SELECT COUNT(*) AS c FROM wa_contacts WHERE group_id = ?", (g["id"],))
        return row["c"] if row else 0
