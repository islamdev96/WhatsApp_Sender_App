"""WhatsApp Sender Pro — Report generation and CSV export."""
import os
import csv
import datetime

from utils.logger import logger


class ReportingMixin:
    """Mixin: Report generation and CSV export."""

    def _generate_final_report(self, duration):
        """Generate and display the final campaign summary report."""
        total = self.sent + self.failed + self.invalid
        if total == 0:
            return None

        pct_ok = (self.sent / total * 100)
        pct_fail = (self.failed / total * 100)
        pct_inv = (self.invalid / total * 100)

        mins, secs = divmod(int(duration.total_seconds()), 60)
        hrs, mins = divmod(mins, 60)
        if hrs:
            dur_text = f"{hrs} ساعة {mins} دقيقة {secs} ثانية"
        elif mins:
            dur_text = f"{mins} دقيقة {secs} ثانية"
        else:
            dur_text = f"{secs} ثانية"

        csv_path = self._save_report_csv()
        csv_note = f"\n\n📄 تم حفظ التقرير:\n{csv_path}" if csv_path else ""

        summary = (
            f"📊 تقرير الإرسال النهائي\n"
            f"{'─' * 35}\n"
            f"📋 الإجمالي: {total}\n"
            f"✅ نجاح: {self.sent} ({pct_ok:.1f}%)\n"
            f"❌ فشل: {self.failed} ({pct_fail:.1f}%)\n"
            f"🚫 بدون واتساب: {self.invalid} ({pct_inv:.1f}%)\n"
            f"⏱ المدة: {dur_text}"
            f"{csv_note}"
        )

        self.log(f"\n📊 التقرير النهائي: ✅{self.sent} | ❌{self.failed} | 🚫{self.invalid} | ⏱{dur_text}")
        self._show_dialog("info", "تقرير الإرسال", summary)
        return csv_path

    def _save_report_csv(self):
        """Save the campaign results to a CSV file."""
        if not self.results_log:
            return None
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["phone", "name", "status", "error_code", "timestamp"])
                writer.writeheader()
                writer.writerows(self.results_log)

            self.log(f"📄 تم حفظ التقرير في: {filepath}")
            return filepath
        except Exception as e:
            self.log(f"⚠ تعذر حفظ التقرير: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════
    #  PRO VERSION PROGRESS WINDOW (APPENDED)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    #  BLIND MODE PROGRESS WINDOW (BENCHMARK MATCH)
    # ═══════════════════════════════════════════════════════════════════════

    def _save_number_check_report(self):
        """Save number validity check results to a CSV file."""
        if not self.results_log:
            return None, None, None
        try:
            reports_dir = os.path.join(os.getcwd(), "reports", "number_checks")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"number_check_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["phone", "name", "status", "error_code", "timestamp"])
                writer.writeheader()
                writer.writerows(self.results_log)
            valid_rows = [r for r in self.results_log if str(r.get("status", "")).strip() in ("صالح", "VALID")]
            invalid_rows = [r for r in self.results_log if str(r.get("status", "")).strip() in ("غير صالح", "INVALID")]

            valid_path = None
            invalid_path = None
            if valid_rows:
                valid_name = f"valid_numbers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                valid_path = os.path.join(reports_dir, valid_name)
                with open(valid_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["phone", "name"])
                    writer.writeheader()
                    for r in valid_rows:
                        writer.writerow({"phone": r.get("phone"), "name": r.get("name")})

            if invalid_rows:
                invalid_name = f"invalid_numbers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                invalid_path = os.path.join(reports_dir, invalid_name)
                with open(invalid_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["phone", "name", "error_code"])
                    writer.writeheader()
                    for r in invalid_rows:
                        writer.writerow({"phone": r.get("phone"), "name": r.get("name"), "error_code": r.get("error_code")})

            return filepath, valid_path, invalid_path
        except Exception as exc:
            logger.warning("Could not export validation reports: %s", exc)
            return None, None, None

    # ═══════════════════════════════════════════════════════════════════════
    #  REPORT
    # ═══════════════════════════════════════════════════════════════════════

    def _format_progress_eta(self, seconds):
        """Format remaining seconds into a human-readable ETA string."""
        if seconds is None:
            return "--"
        try:
            seconds = int(max(0, seconds))
        except Exception:
            return "--"
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}س {minutes}د"
        if minutes:
            return f"{minutes}د {secs}ث"
        return f"{secs}ث"

