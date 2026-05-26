import json
import logging
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.campaign_manager import CampaignManager
from utils.contacts_manager import ContactsManager
from utils.templates_manager import TemplatesManager


class TestJsonManagers(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_campaign_manager_ignores_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "campaigns.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{bad json")

            manager = CampaignManager(campaigns_path=path, use_sqlite=False)

            self.assertEqual(manager.get_all(), [])

    def test_contacts_manager_filters_malformed_groups_and_contacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "contact_groups.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        "bad",
                        {
                            "name": "Customers",
                            "contacts": [
                                {"phone": "201000000000", "name": "A"},
                                "bad contact",
                            ],
                        },
                    ],
                    f,
                )

            manager = ContactsManager(groups_path=path, use_sqlite=False)
            self.assertEqual(manager.get_names(), ["Customers"])
            self.assertEqual(manager.add_contacts("Customers", ["bad", {"phone": "201111111111"}]), 1)

    def test_templates_manager_filters_malformed_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "templates.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(["bad", {"name": "Welcome", "body": "Hi"}], f)

            manager = TemplatesManager(templates_path=path, use_sqlite=False)

            self.assertEqual(manager.get_names(), ["Welcome"])


if __name__ == "__main__":
    unittest.main()
