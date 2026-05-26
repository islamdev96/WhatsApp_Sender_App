import logging
import os
import sys
import tempfile
import unittest
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.logger as app_logger


class TestLoggerSetup(unittest.TestCase):
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_setup_logger_configures_own_handlers_when_root_has_handler(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_log_dir = app_logger.LOG_DIR
            root = logging.getLogger()
            root_handler = logging.NullHandler()
            logger_name = f"test_logger_{uuid.uuid4().hex}"
            logger = logging.getLogger(logger_name)

            app_logger.LOG_DIR = tmp
            root.addHandler(root_handler)
            try:
                configured = app_logger.setup_logger(name=logger_name, level=logging.CRITICAL)

                self.assertIs(configured, logger)
                self.assertGreaterEqual(len(configured.handlers), 2)
                self.assertFalse(configured.propagate)
                self.assertTrue(any(name.endswith(".log") for name in os.listdir(tmp)))
            finally:
                root.removeHandler(root_handler)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                app_logger.LOG_DIR = old_log_dir


if __name__ == "__main__":
    unittest.main()
