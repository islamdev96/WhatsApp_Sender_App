"""
Tests for utils/scheduler.py — Persistent SQLite Scheduler operations and callback triggering.
"""
import os
import tempfile
import unittest
import datetime
import time
import threading
from utils.scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    """Test Scheduler SQLite database operations, scheduling, cancellation, and background polling."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_scheduler.db")
        self.scheduler = Scheduler(db_path=self.db_path)

    def tearDown(self):
        self.scheduler.stop()
        self.scheduler.store.close()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            if os.path.exists(self.tmp):
                os.rmdir(self.tmp)
        except Exception:
            pass

    def test_schedule_campaign_and_cancel(self):
        """Verify scheduling a campaign inserts it to DB and cancelling changes status."""
        future_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        
        # Schedule
        campaign_id = self.scheduler.schedule_campaign(
            name="Test Schedule",
            scheduled_time=future_time,
            message="Hello",
            attachments=[],
            group_name="TestGroup"
        )
        self.assertIsNotNone(campaign_id)
        
        # Verify lists
        upcoming = self.scheduler.get_upcoming_campaigns()
        self.assertEqual(len(upcoming), 1)
        self.assertEqual(upcoming[0]["id"], campaign_id)
        self.assertEqual(upcoming[0]["status"], "pending")
        self.assertEqual(upcoming[0]["group_name"], "TestGroup")
        
        # Cancel
        cancelled_ok = self.scheduler.cancel_campaign(campaign_id)
        self.assertTrue(cancelled_ok)
        
        # Check upcoming is empty
        self.assertEqual(len(self.scheduler.get_upcoming_campaigns()), 0)
        
        # Verify in all campaigns history
        all_camps = self.scheduler.get_all_campaigns()
        self.assertEqual(len(all_camps), 1)
        self.assertEqual(all_camps[0]["status"], "cancelled")

    def test_delete_campaign(self):
        """Verify that delete_campaign removes it entirely from the database."""
        future_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        campaign_id = self.scheduler.schedule_campaign(
            name="Temp Campaign",
            scheduled_time=future_time,
            message="Delete me",
            attachments=[]
        )
        self.assertEqual(len(self.scheduler.get_all_campaigns()), 1)
        
        self.scheduler.delete_campaign(campaign_id)
        self.assertEqual(len(self.scheduler.get_all_campaigns()), 0)

    def test_scheduler_trigger_callback(self):
        """Verify the background polling service detects due campaigns and triggers callback."""
        called_event = threading.Event()
        triggered_payload = {}

        def my_callback(name, contacts, message, attachments, sending_mode):
            triggered_payload["name"] = name
            triggered_payload["contacts"] = contacts
            triggered_payload["message"] = message
            triggered_payload["attachments"] = attachments
            triggered_payload["sending_mode"] = sending_mode
            called_event.set()
            return True

        # Schedule in the past/immediate so it triggers immediately
        past_time = datetime.datetime.now() - datetime.timedelta(seconds=1)
        
        self.scheduler.schedule_campaign(
            name="Immediate Campaign",
            scheduled_time=past_time,
            message="Trigger alert!",
            attachments=[{"type": "image", "path": "test.png"}],
            contacts=[{"phone": "12345", "name": "Target"}],
            sending_mode="blind"
        )
        
        # Start background polling
        self.scheduler.start(my_callback)
        
        # Wait up to 3 seconds for the polling background thread to run and callback to fire
        success = called_event.wait(3.0)
        self.scheduler.stop()
        
        self.assertTrue(success, "Scheduler callback was not triggered in time")
        self.assertEqual(triggered_payload["name"], "Immediate Campaign")
        self.assertEqual(triggered_payload["message"], "Trigger alert!")
        self.assertEqual(triggered_payload["sending_mode"], "blind")
        self.assertEqual(len(triggered_payload["contacts"]), 1)
        self.assertEqual(triggered_payload["contacts"][0]["phone"], "12345")


if __name__ == "__main__":
    unittest.main()
