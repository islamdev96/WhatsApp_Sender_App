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


if __name__ == "__main__":
    unittest.main()
