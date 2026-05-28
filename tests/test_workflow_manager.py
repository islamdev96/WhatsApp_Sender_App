"""
Tests for utils/workflow_manager.py — CRUD operations on workflows.
"""
import os
import tempfile
import unittest

from utils.workflow_manager import WorkflowManager


class TestWorkflowManager(unittest.TestCase):
    """Test WorkflowManager save, get, list, and delete operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "wf_test.db")
        self.wm = WorkflowManager(db_path=self.db_path)

    def tearDown(self):
        self.wm.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_workflow(self):
        """Save a workflow with steps and retrieve it by name."""
        steps = [
            {"body": "Hello {name}", "attachments": [], "delay_min": 5, "delay_max": 10},
            {"body": "Follow up", "attachments": [{"path": "img.png", "type": "image"}], "delay_min": 10, "delay_max": 15},
        ]
        ok, result = self.wm.save("My Workflow", steps)
        self.assertTrue(ok)

        wf = self.wm.get_by_name("My Workflow")
        self.assertIsNotNone(wf)
        self.assertEqual(wf["name"], "My Workflow")
        self.assertEqual(len(wf["steps"]), 2)
        self.assertEqual(wf["steps"][0]["body"], "Hello {name}")

    def test_get_all_returns_list(self):
        """get_all returns all workflows."""
        self.wm.save("WF1", [{"body": "A", "attachments": []}])
        self.wm.save("WF2", [
            {"body": "B", "attachments": []},
            {"body": "C", "attachments": []},
        ])
        all_wf = self.wm.get_all()
        self.assertEqual(len(all_wf), 2)

    def test_delete_workflow(self):
        """Delete removes the workflow and its steps."""
        ok, wf_id = self.wm.save("ToDelete", [{"body": "X", "attachments": []}])
        self.assertTrue(ok)

        self.wm.delete(wf_id)
        self.assertIsNone(self.wm.get_by_name("ToDelete"))

    def test_get_nonexistent_returns_none(self):
        """get_by_name on missing name returns None."""
        self.assertIsNone(self.wm.get_by_name("DoesNotExist"))

    def test_save_rejects_duplicate_names(self):
        """Saving with the same name without workflow_id returns error."""
        self.wm.save("WF", [{"body": "Old", "attachments": []}])
        ok, msg = self.wm.save("WF", [{"body": "New", "attachments": []}])
        self.assertFalse(ok)

    def test_update_existing_workflow(self):
        """Updating an existing workflow by ID replaces its steps."""
        ok, wf_id = self.wm.save("WF", [{"body": "Old", "attachments": []}])
        self.assertTrue(ok)

        ok2, wf_id2 = self.wm.save("WF", [
            {"body": "New1", "attachments": []},
            {"body": "New2", "attachments": []},
        ], workflow_id=wf_id)
        self.assertTrue(ok2)

        wf = self.wm.get_by_name("WF")
        self.assertEqual(len(wf["steps"]), 2)
        self.assertEqual(wf["steps"][0]["body"], "New1")


if __name__ == "__main__":
    unittest.main()
