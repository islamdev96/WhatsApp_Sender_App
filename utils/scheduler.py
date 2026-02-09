"""
Scheduler — Schedule WhatsApp sending for a specific date/time.
Runs a background timer that triggers the sending callback when the scheduled time arrives.
"""
import threading
import datetime
import time


class Scheduler:
    def __init__(self):
        self._timer_thread = None
        self._cancel_event = threading.Event()
        self.scheduled_time = None
        self.is_scheduled = False

    def schedule(self, target_datetime, callback, *args, **kwargs):
        """
        Schedule a callback to run at target_datetime.
        Returns (success, message).
        """
        now = datetime.datetime.now()
        if target_datetime <= now:
            return False, "الوقت المحدد في الماضي. يرجى اختيار وقت مستقبلي."

        self.cancel()  # Cancel any existing schedule

        self.scheduled_time = target_datetime
        self.is_scheduled = True
        self._cancel_event.clear()

        delay_seconds = (target_datetime - now).total_seconds()

        def _wait_and_run():
            # Wait in 1-second increments so we can cancel
            end_time = time.time() + delay_seconds
            while time.time() < end_time:
                if self._cancel_event.is_set():
                    self.is_scheduled = False
                    return
                time.sleep(1)

            self.is_scheduled = False
            if not self._cancel_event.is_set():
                callback(*args, **kwargs)

        self._timer_thread = threading.Thread(target=_wait_and_run, daemon=True)
        self._timer_thread.start()

        time_str = target_datetime.strftime("%Y-%m-%d %H:%M")
        mins = int(delay_seconds // 60)
        return True, f"تم الجدولة في {time_str} (بعد {mins} دقيقة)"

    def cancel(self):
        """Cancel the scheduled task."""
        self._cancel_event.set()
        self.is_scheduled = False
        self.scheduled_time = None

    def get_remaining(self):
        """Get remaining time as (minutes, seconds) or None if not scheduled."""
        if not self.is_scheduled or not self.scheduled_time:
            return None
        remaining = (self.scheduled_time - datetime.datetime.now()).total_seconds()
        if remaining <= 0:
            return None
        mins, secs = divmod(int(remaining), 60)
        return mins, secs

    def get_remaining_text(self):
        """Get remaining time as formatted text."""
        r = self.get_remaining()
        if not r:
            return None
        mins, secs = r
        if mins >= 60:
            hrs = mins // 60
            mins = mins % 60
            return f"{hrs} ساعة {mins} دقيقة"
        return f"{mins} دقيقة {secs} ثانية"
