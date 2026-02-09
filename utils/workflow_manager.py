"""
Workflow Manager — Manage multi-step sending workflows.
Stores workflows and steps in SQLite.
"""
import json
import os
import datetime
from utils.db import SQLiteStore


class WorkflowManager:
    def __init__(self, db_path=None):
        self.store = SQLiteStore(db_path=db_path)

    def get_all(self):
        rows = self.store.query_all("SELECT id, name, created, updated FROM wa_workflows ORDER BY id DESC")
        out = []
        for r in rows:
            count = self.store.query_one(
                "SELECT COUNT(*) AS c FROM wa_workflow_steps WHERE workflow_id = ?",
                (r["id"],),
            )["c"]
            out.append({**r, "steps_count": count})
        return out

    def get_by_name(self, name):
        if not name:
            return None
        wf = self.store.query_one("SELECT id, name, created, updated FROM wa_workflows WHERE name = ?", (name,))
        if not wf:
            return None
        steps = self._get_steps(wf["id"])
        wf["steps"] = steps
        return wf

    def get(self, workflow_id):
        wf = self.store.query_one("SELECT id, name, created, updated FROM wa_workflows WHERE id = ?", (workflow_id,))
        if not wf:
            return None
        wf["steps"] = self._get_steps(workflow_id)
        return wf

    def _get_steps(self, workflow_id):
        rows = self.store.query_all(
            "SELECT id, step_order, body, attachments_json, delay_min, delay_max "
            "FROM wa_workflow_steps WHERE workflow_id = ? ORDER BY step_order",
            (workflow_id,),
        )
        steps = []
        for r in rows:
            attachments = []
            if r.get("attachments_json"):
                try:
                    attachments = json.loads(r["attachments_json"])
                except Exception:
                    attachments = []
            steps.append({
                "id": r["id"],
                "order": r["step_order"],
                "body": r.get("body") or "",
                "attachments": attachments,
                "delay_min": r.get("delay_min") or 0,
                "delay_max": r.get("delay_max") or 0,
            })
        return steps

    def save(self, name, steps, workflow_id=None):
        if not name:
            return False, "اسم سير العمل مطلوب."
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        existing = self.store.query_one("SELECT id FROM wa_workflows WHERE name = ?", (name,))
        if workflow_id:
            if existing and existing["id"] != workflow_id:
                return False, "يوجد سير عمل بنفس الاسم."
            self.store.execute(
                "UPDATE wa_workflows SET name = ?, updated = ? WHERE id = ?",
                (name, now, workflow_id),
                commit=True,
            )
            wf_id = workflow_id
        else:
            if existing:
                return False, "يوجد سير عمل بنفس الاسم."
            cur = self.store.execute(
                "INSERT INTO wa_workflows(name, created, updated) VALUES(?, ?, ?)",
                (name, now, now),
                commit=True,
            )
            wf_id = cur.lastrowid

        # Replace steps
        self.store.execute("DELETE FROM wa_workflow_steps WHERE workflow_id = ?", (wf_id,), commit=True)
        order = 1
        for s in steps or []:
            body = s.get("body", "")
            attachments = s.get("attachments", [])
            delay_min = int(s.get("delay_min", 0) or 0)
            delay_max = int(s.get("delay_max", 0) or 0)
            self.store.execute(
                "INSERT INTO wa_workflow_steps(workflow_id, step_order, body, attachments_json, delay_min, delay_max) "
                "VALUES(?, ?, ?, ?, ?, ?)",
                (wf_id, order, body, json.dumps(attachments, ensure_ascii=False), delay_min, delay_max),
                commit=True,
            )
            order += 1
        return True, wf_id

    def delete(self, workflow_id):
        self.store.execute("DELETE FROM wa_workflow_steps WHERE workflow_id = ?", (workflow_id,), commit=True)
        self.store.execute("DELETE FROM wa_workflows WHERE id = ?", (workflow_id,), commit=True)
        return True
