"""
Scheduler — Schedule WhatsApp campaigns persistently in SQLite.
Runs a background polling loop that triggers the campaign when the scheduled time arrives.
"""
import threading
import datetime
import time
import json
from utils.db import SQLiteStore
from utils.logger import logger, log_exception


class Scheduler:
    def __init__(self, db_path=None):
        self.store = SQLiteStore(db_path=db_path)
        self._polling_thread = None
        self._stop_event = threading.Event()
        self._callback = None

    def start(self, callback) -> None:
        """Starts the background thread to poll the DB for pending scheduled campaigns."""
        self._callback = callback
        self._stop_event.clear()
        if self._polling_thread is None or not self._polling_thread.is_alive():
            self._polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._polling_thread.start()
            logger.info("Scheduler background polling service started.")

    def stop(self) -> None:
        """Stops the scheduler polling service."""
        self._stop_event.set()
        if self._polling_thread:
            self._polling_thread.join(timeout=2.0)
        logger.info("Scheduler background polling service stopped.")

    def schedule_campaign(
        self,
        name: str,
        scheduled_time: datetime.datetime,
        message: str,
        attachments: list,
        group_name: str = None,
        contacts: list = None,
        sending_mode: str = "safe"
    ) -> int:
        """
        Saves a scheduled campaign to the SQLite database.
        Returns the inserted campaign ID.
        """
        time_str = scheduled_time.strftime("%Y-%m-%d %H:%M")
        attachments_json = json.dumps(attachments or [])
        contacts_json = json.dumps(contacts or [])
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = self.store.execute(
            """
            INSERT INTO wa_scheduled_campaigns (
                name, scheduled_time, message, attachments_json, 
                group_name, contacts_json, sending_mode, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, time_str, message, attachments_json, group_name, contacts_json, sending_mode, "pending", created_at),
            commit=True
        )
        campaign_id = cur.lastrowid
        logger.info(f"Campaign '{name}' scheduled for {time_str} (ID: {campaign_id})")
        return campaign_id

    def cancel_campaign(self, campaign_id: int) -> bool:
        """Cancels a scheduled campaign by setting its status to 'cancelled'."""
        row = self.store.query_one("SELECT status FROM wa_scheduled_campaigns WHERE id = ?", (campaign_id,))
        if not row or row["status"] != "pending":
            return False
        self.store.execute(
            "UPDATE wa_scheduled_campaigns SET status = ? WHERE id = ?",
            ("cancelled", campaign_id),
            commit=True
        )
        logger.info(f"Cancelled scheduled campaign ID: {campaign_id}")
        return True

    def delete_campaign(self, campaign_id: int) -> None:
        """Deletes a campaign from the schedule queue permanently."""
        self.store.execute("DELETE FROM wa_scheduled_campaigns WHERE id = ?", (campaign_id,), commit=True)
        logger.info(f"Deleted campaign ID: {campaign_id}")

    def get_upcoming_campaigns(self) -> list[dict]:
        """Returns all pending scheduled campaigns sorted by scheduled time."""
        rows = self.store.query_all(
            "SELECT * FROM wa_scheduled_campaigns WHERE status = 'pending' ORDER BY scheduled_time ASC"
        )
        return [dict(r) for r in rows]

    def get_all_campaigns(self) -> list[dict]:
        """Returns all scheduled campaigns in history."""
        rows = self.store.query_all("SELECT * FROM wa_scheduled_campaigns ORDER BY id DESC")
        return [dict(r) for r in rows]

    def _poll_loop(self) -> None:
        """Periodic polling loop executed in a background thread."""
        while not self._stop_event.is_set():
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                # Find pending campaigns where scheduled_time is less than or equal to now
                rows = self.store.query_all(
                    "SELECT * FROM wa_scheduled_campaigns WHERE status = 'pending' AND scheduled_time <= ?",
                    (now_str,)
                )
                
                for r in rows:
                    campaign_id = r["id"]
                    logger.info(f"Triggering scheduled campaign ID {campaign_id} (Scheduled: {r['scheduled_time']})")
                    
                    # Mark as sending to prevent duplicate triggers
                    self.store.execute(
                        "UPDATE wa_scheduled_campaigns SET status = 'sending' WHERE id = ?",
                        (campaign_id,),
                        commit=True
                    )
                    
                    # Trigger the callback
                    if self._callback:
                        # Resolve contacts list
                        contacts = []
                        group_name = r["group_name"]
                        if group_name:
                            # Load contacts from ContactsManager database
                            from utils.contacts_manager import ContactsManager
                            mgr = ContactsManager(db_path=self.store.db_path)
                            g = mgr.get_by_name(group_name)
                            if g:
                                contacts = g.get("contacts", [])
                        else:
                            contacts_json = r["contacts_json"]
                            if contacts_json:
                                contacts = json.loads(contacts_json)
                        
                        message = r["message"]
                        attachments = json.loads(r["attachments_json"] or "[]")
                        sending_mode = r["sending_mode"] or "safe"
                        campaign_name = r["name"]
                        
                        # Start sending in a separate thread so it doesn't block the scheduler loop
                        threading.Thread(
                            target=self._run_campaign_async,
                            args=(campaign_id, campaign_name, contacts, message, attachments, sending_mode),
                            daemon=True
                        ).start()
            except Exception as exc:
                log_exception("Error in scheduler polling loop iteration", exc)
                
            # Wait for 10 seconds before next check
            self._stop_event.wait(10.0)

    def _run_campaign_async(
        self,
        campaign_id: int,
        campaign_name: str,
        contacts: list,
        message: str,
        attachments: list,
        sending_mode: str
    ) -> None:
        """Helper to run the campaign callback and save status results."""
        try:
            success = self._callback(campaign_name, contacts, message, attachments, sending_mode)
            new_status = "completed" if success else "failed"
            self.store.execute(
                "UPDATE wa_scheduled_campaigns SET status = ? WHERE id = ?",
                (new_status, campaign_id),
                commit=True
            )
            logger.info(f"Scheduled campaign ID {campaign_id} finished with status: {new_status}")
        except Exception as exc:
            log_exception(f"Exception during scheduled campaign ID {campaign_id} callback execution", exc)
            self.store.execute(
                "UPDATE wa_scheduled_campaigns SET status = 'failed' WHERE id = ?",
                (campaign_id,),
                commit=True
            )
