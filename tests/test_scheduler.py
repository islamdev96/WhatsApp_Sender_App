"""
Tests for utils/scheduler.py — Scheduler scheduling and cancellation.
"""
import unittest
import datetime

from utils.scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    """Test Scheduler schedule, cancel, and remaining text."""

    def test_schedule_and_cancel(self):
        """Schedule a task and cancel it before execution."""
        called = []
        scheduler = Scheduler()
        future = datetime.datetime.now() + datetime.timedelta(seconds=30)
        ok, msg = scheduler.schedule(future, lambda: called.append(True))
        self.assertTrue(ok)
        self.assertTrue(scheduler.is_scheduled)
        scheduler.cancel()
        self.assertFalse(scheduler.is_scheduled)
        self.assertEqual(len(called), 0)

    def test_remaining_text_format(self):
        """get_remaining_text returns a human-readable string."""
        scheduler = Scheduler()
        future = datetime.datetime.now() + datetime.timedelta(minutes=5)
        scheduler.schedule(future, lambda: None)
        text = scheduler.get_remaining_text()
        self.assertIsNotNone(text)
        scheduler.cancel()

    def test_cancel_when_not_scheduled(self):
        """Cancel on unscheduled scheduler should not raise."""
        scheduler = Scheduler()
        scheduler.cancel()  # Should not raise

    def test_not_scheduled_initially(self):
        """New Scheduler is not scheduled."""
        scheduler = Scheduler()
        self.assertFalse(scheduler.is_scheduled)
        self.assertIsNone(scheduler.get_remaining_text())

    def test_past_time_returns_error(self):
        """Scheduling in the past returns failure."""
        scheduler = Scheduler()
        past = datetime.datetime.now() - datetime.timedelta(hours=1)
        ok, msg = scheduler.schedule(past, lambda: None)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
