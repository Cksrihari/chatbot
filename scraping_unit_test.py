import pandas as pd
from datetime import datetime
from main_scraping import MainScraping
from TrainTimes import TrainTimes
from GreaterAnglia import GreaterAnglia
from selenium import webdriver
from unittest.mock import patch, MagicMock
import time
import unittest


class UnitTest(unittest.TestCase):
    @patch('builtins.print')
    def test_cheapest_compared(self, mock_print):
        # Create a sample dataframe that would mimic the CSV file
        sample_data = {
            'Date': ['Mon 01 Jan 2023', 'Tue 02 Jan 2023'],
            'Origin': ['Norwich', 'Norwich'],
            'Destination': ['LDS', 'LDS'],
            'Fare': ['£25.00', '£30.00'],
            'URL': ['http://example.com/1', 'http://example.com/2']
        }
        df = pd.DataFrame(sample_data)
        df.to_csv("train_data.csv", index=False)

        main = MainScraping()
        main.cheapest_compared()

        # Define expected output
        expected_output = (
            "Date: Mon 01 Jan 2023\n"
            "Origin: Norwich\n"
            "Destination: LDS\n"
            "Cheapest Fare: £25.00\n"
            "URL: http://example.com/1\n"
        )
        # Assert print was called with the expected output
        mock_print.assert_called_with(expected_output)

    @patch.object(GreaterAnglia, 'run')
    @patch.object(TrainTimes, 'run')
    @patch.object(Main, 'cheapest_compared')
    def test_main(self, mock_cheapest_compared, mock_tt_run, mock_ga_run):
        main = Main()
        main.main()
        self.ga = GreaterAnglia()
        self.ga.driver = MagicMock(spec=webdriver.Chrome)

        # Assert that the methods were called
        mock_ga_run.assert_called_once_with("Norwich", "LDS", "06 01")
        mock_tt_run.assert_called_once_with("Norwich", "LDS", "15:00", "06 01")
        mock_cheapest_compared.assert_called_once()

    def setUp(self):
        self.train_times = TrainTimes()
        self.ga = GreaterAnglia()

    def test_construct_url(self):
        result = self.train_times.construct_url("London", "Manchester", "15:00", "06 01")
        expected_year = datetime.now().year
        expected_url = f"https://traintimes.org.uk/London/Manchester/15:00/{expected_year}-06-01"
        self.assertEqual(result, expected_url)

    @patch.object(TrainTimes, 'random_delay')
    @patch.object(webdriver.Chrome, 'get')
    @patch.object(webdriver.Chrome, 'find_elements')
    @patch.object(webdriver.Chrome, 'quit')
    def test_scraping(self, mock_quit, mock_find_elements, mock_get, mock_random_delay):
        mock_element = MagicMock()
        mock_element.text = '£20.00 Advance Single'
        mock_find_elements.return_value = [mock_element]
        result = self.train_times.scraping("http://fakeurl.com")
        self.assertEqual(result, '£20.00')
        mock_get.assert_called_with("http://fakeurl.com")
        mock_quit.assert_called_once()

    @patch.object(TrainTimes, 'construct_url')
    @patch.object(TrainTimes, 'scraping')
    def test_run_train_times(self, mock_scraping, mock_construct_url):
        mock_construct_url.return_value = "http://fakeurl.com"
        mock_scraping.return_value = "£20.00"
        self.train_times.run("London", "Manchester", "15:00", "06 01")
        with open('train_data.csv', 'r') as file:
            lines = file.readlines()
        self.assertGreater(len(lines), 0)

    def test_random_delay(self):
        start_time = time.time()
        self.train_times.random_delay(0.1, 0.2)
        elapsed_time = time.time() - start_time
        self.assertTrue(0.1 <= elapsed_time <= 0.2)

    @patch.object(webdriver.Chrome, 'get')
    @patch('selenium.webdriver.support.ui.WebDriverWait.until')
    def test_handle_cookies(self, mock_wait, mock_get):
        mock_element = MagicMock()
        mock_wait.return_value = mock_element
        self.ga.handle_cookies("http://fakeurl.com")
        mock_get.assert_called_with("http://fakeurl.com")
        mock_element.click.assert_called_once()

    def test_replace_url(self):
        self.ga.url = "http://fakeurl.com/2023-06-01"
        result = self.ga.replace_url("2024-06-01")
        self.assertIn("2024-06-01", result)

    @patch.object(webdriver.Chrome, 'get')
    @patch.object(webdriver.Chrome, 'find_element')
    def test_find_cheapest_ticket(self, mock_find_element, mock_get):
        mock_element = MagicMock()
        mock_element.text = '£20.00'
        mock_find_element.return_value = mock_element
        result = self.ga.find_cheapest_ticket("http://fakeurl.com")
        self.assertEqual(result, '£20.00')

    @patch.object(GreaterAnglia, 'handle_cookies')
    @patch.object(GreaterAnglia, 'search_for_train')
    @patch.object(GreaterAnglia, 'find_cheapest_ticket')
    def test_run_greater_anglia(self, mock_find_cheapest_ticket, mock_search_for_train, mock_handle_cookies):
        mock_search_for_train.return_value = "http://fakeurl.com"
        mock_find_cheapest_ticket.return_value = "£20.00"
        self.ga.run("London", "Manchester", "06 01")
        with open('train_data.csv', 'r') as file:
            lines = file.readlines()
        self.assertGreater(len(lines), 0)

    # Negative test cases
    @patch.object(webdriver.Chrome, 'get')
    @patch('selenium.webdriver.support.ui.WebDriverWait.until')
    def test_handle_cookies_no_cookies_button(self, mock_wait, mock_get):
        mock_wait.side_effect = Exception("Timeout")
        with self.assertRaises(Exception) as context:
            self.ga.handle_cookies("http://fakeurl.com")
        self.assertTrue("Cookies button not found or not clickable" in str(context.exception))

    def test_construct_url_empty_strings(self):
        with self.assertRaises(ValueError):
            self.train_times.construct_url("", "", "", "")

    @patch.object(webdriver.Chrome, 'get')
    @patch.object(webdriver.Chrome, 'find_elements')
    def test_scraping_no_elements_found(self, mock_find_elements, mock_get):
        mock_find_elements.return_value = []
        result = self.train_times.scraping("http://fakeurl.com")
        self.assertIsNone(result)

    def test_replace_url_invalid_url(self):
        self.ga.url = "invalid-url"
        with self.assertRaises(ValueError) as context:
            self.ga.replace_url("2024-06-01")
        self.assertTrue("Invalid URL: Date pattern not found" in str(context.exception))

    @patch.object(webdriver.Chrome, 'get')
    @patch('selenium.webdriver.support.ui.WebDriverWait.until')
    def test_handle_cookies_no_cookies_button(self, mock_wait, mock_get):
        mock_wait.side_effect = Exception("Timeout")
        with self.assertRaises(Exception):
            self.ga.handle_cookies("http://fakeurl.com")


if __name__ == "__main__":
    unittest.main()








