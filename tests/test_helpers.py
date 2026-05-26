import csv
import logging
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    create_contacts_template,
    normalize_phone,
    read_contacts,
    read_contacts_auto,
    read_contacts_txt,
)


class TestHelpers(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_normalize_phone_egypt_local_number(self):
        self.assertEqual(normalize_phone("010 1234 5678"), "201012345678")

    def test_read_contacts_csv_with_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "contacts.csv")
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Phone", "Var1"])
                writer.writerow(["Alice", "01012345678", "VIP"])

            contacts = read_contacts(path)

            self.assertEqual(
                contacts,
                [{"phone": "201012345678", "name": "Alice", "var1": "VIP"}],
            )

    def test_read_contacts_txt_deduplicates_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "numbers.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("01012345678\n010 1234 5678\n")

            contacts = read_contacts_txt(path)

            self.assertEqual(len(contacts), 1)
            self.assertEqual(contacts[0]["phone"], "201012345678")

    def test_read_contacts_auto_uses_txt_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "numbers.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("+201012345678\n")

            self.assertEqual(read_contacts_auto(path)[0]["phone"], "201012345678")

    def test_create_contacts_template_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "template.csv")

            self.assertTrue(create_contacts_template(path))
            self.assertTrue(os.path.exists(path))
            self.assertEqual(read_contacts(path)[0]["phone"], "2010XXXXXXXX")

    def test_cleanup_proxy_extension(self):
        from utils.helpers import create_proxy_extension, cleanup_proxy_extension
        with tempfile.TemporaryDirectory() as tmp:
            ext_dir = create_proxy_extension(tmp, "http", "127.0.0.1", "8080", "user", "pass")
            self.assertTrue(os.path.isdir(ext_dir))
            cleanup_proxy_extension(tmp)
            self.assertFalse(os.path.exists(ext_dir))

    def test_cleanup_old_reports(self):
        from utils.helpers import cleanup_old_reports
        import time
        with tempfile.TemporaryDirectory() as tmp:
            # Create old and new files
            old_file = os.path.join(tmp, "report_old.csv")
            new_file = os.path.join(tmp, "report_new.csv")
            
            with open(old_file, "w") as f:
                f.write("old data")
            with open(new_file, "w") as f:
                f.write("new data")

            # Set old file mtime to 40 days ago
            past = time.time() - (40 * 86400)
            os.utime(old_file, (past, past))

            # Run cleanup with max_age_days = 30
            removed = cleanup_old_reports(reports_base_dir=tmp, max_age_days=30)
            
            self.assertEqual(removed, 1)
            self.assertFalse(os.path.exists(old_file))
            self.assertTrue(os.path.exists(new_file))


if __name__ == "__main__":
    unittest.main()
