import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.gmaps_scraper import GMapsScraper


class TestGMapsScraper(unittest.TestCase):
    def test_scraper_initialization(self):
        mock_driver = MagicMock()
        scraper = GMapsScraper(mock_driver)
        self.assertEqual(scraper.driver, mock_driver)

    @patch("time.sleep")
    def test_scraper_search_timeout(self, mock_sleep):
        mock_driver = MagicMock()
        scraper = GMapsScraper(mock_driver)

        # Mock TimeoutException on wait
        from selenium.common.exceptions import TimeoutException
        with patch("selenium.webdriver.support.ui.WebDriverWait.until", side_effect=TimeoutException()):
            stop_event = MagicMock()
            stop_event.is_set.return_value = False
            
            results = scraper.scrape("Dentists in Cairo", stop_event, max_results=10)
            self.assertEqual(len(results), 0)

    @patch("time.sleep")
    def test_scraper_stops_on_event(self, mock_sleep):
        mock_driver = MagicMock()
        scraper = GMapsScraper(mock_driver)

        stop_event = MagicMock()
        stop_event.is_set.return_value = True

        results = scraper.scrape("Dentists in Cairo", stop_event, max_results=10)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
