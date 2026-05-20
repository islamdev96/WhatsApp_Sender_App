"""
Unit Test Suite for WhatsApp Sender Pro.
Verifies all core utility functions, configuration management, phone normalization, and spintax parsing.
"""
import unittest
import os
import shutil
import tempfile
import json
from utils.config_manager import ConfigManager
from utils.helpers import normalize_phone, read_contacts_txt, read_contacts
from gui.modern_ui import ModernWhatsAppApp

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_default_config(self):
        config = ConfigManager(config_path=self.config_path)
        self.assertEqual(config.get("default_country_code"), "20")
        self.assertEqual(config.get("appearance_mode"), "dark")

    def test_save_and_load(self):
        config = ConfigManager(config_path=self.config_path)
        config.set("default_country_code", "966")
        config.set("appearance_mode", "light")
        config.save()

        # Reload config
        config2 = ConfigManager(config_path=self.config_path)
        self.assertEqual(config2.get("default_country_code"), "966")
        self.assertEqual(config2.get("appearance_mode"), "light")


class TestPhoneNormalization(unittest.TestCase):
    def test_egypt_normalization(self):
        # Local format starting with 01X -> 201X
        self.assertEqual(normalize_phone("01012345678", "20"), "201012345678")
        self.assertEqual(normalize_phone("1012345678", "20"), "201012345678")
        # Already normalized
        self.assertEqual(normalize_phone("201012345678", "20"), "201012345678")
        self.assertEqual(normalize_phone("+201012345678", "20"), "201012345678")

    def test_saudi_normalization(self):
        # Saudi local format starting with 05X -> 9665X
        self.assertEqual(normalize_phone("0501234567", "966"), "966501234567")
        self.assertEqual(normalize_phone("+966501234567", "966"), "966501234567")
        self.assertEqual(normalize_phone("501234567", "966"), "966501234567")

    def test_general_formatting(self):
        # Strips spaces, dashes, dots, brackets
        self.assertEqual(normalize_phone(" +966 (50) 123-45.67 ", "966"), "966501234567")
        # Strips .0 suffix from float conversions
        self.assertEqual(normalize_phone("966501234567.0", "966"), "966501234567")


class TestContactsReader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_read_txt_line_by_line(self):
        file_path = os.path.join(self.temp_dir, "numbers.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("0501234567\n0507654321\n+966555555555\n")

        contacts = read_contacts_txt(file_path, default_country_code="966")
        self.assertEqual(len(contacts), 3)
        self.assertEqual(contacts[0]["phone"], "966501234567")
        self.assertEqual(contacts[1]["phone"], "966507654321")
        self.assertEqual(contacts[2]["phone"], "966555555555")

    def test_read_txt_regex_fallback(self):
        file_path = os.path.join(self.temp_dir, "mixed.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("سجل هذا الرقم 0501234567 وهاتف العميل الآخر +966507654321 في القائمة.")

        contacts = read_contacts_txt(file_path, default_country_code="966")
        self.assertEqual(len(contacts), 2)
        phones = [c["phone"] for c in contacts]
        self.assertIn("966501234567", phones)
        self.assertIn("966507654321", phones)


class TestSpintaxAndTemplate(unittest.TestCase):
    def setUp(self):
        # We need an app instance to test UI template logic,
        # but let's mock the UI parts to keep it fast and headless.
        # However, _apply_template and _apply_spintax are fully deterministic.
        class DummyApp:
            def __init__(self):
                # Mock spin_text_var to return True
                class MockVar:
                    def get(self): return True
                self.spin_text_var = MockVar()
            
            from gui.modern_ui import ModernWhatsAppApp
            _apply_template = ModernWhatsAppApp._apply_template
            _apply_spintax = ModernWhatsAppApp._apply_spintax
            
        self.app = DummyApp()

    def test_template_variables(self):
        contact = {
            "name": "سعد",
            "phone": "966501111111",
            "var1": "شاحن سريع",
            "var2": "50 ريال",
        }
        text = "مرحباً يا {name}، لقد قمت بشراء {var1} بسعر {var2}."
        result = self.app._apply_template(text, contact)
        self.assertEqual(result, "مرحباً يا سعد، لقد قمت بشراء شاحن سريع بسعر 50 ريال.")

    def test_spintax_rotation(self):
        text = "{أهلاً|مرحباً|أهلاً وسهلاً}"
        results = set()
        # Run multiple times to capture all variations
        for _ in range(50):
            res = self.app._apply_spintax(text)
            results.add(res)
        
        self.assertIn("أهلاً", results)
        self.assertIn("مرحباً", results)
        self.assertIn("أهلاً وسهلاً", results)

if __name__ == "__main__":
    unittest.main()
