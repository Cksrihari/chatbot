import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
from chatbot import ChatBot
from datetime import datetime, timedelta


class TestChatBot(unittest.TestCase):
    def setUp(self):
        self.chatbot = ChatBot()

    @patch('builtins.open', new_callable=mock_open, read_data="Norwich,London Liverpool Street\n")
    def test_fetch_all_stations(self, mock_file):
        stations = self.chatbot.fetch_all_stations()
        self.assertEqual(stations, ['Norwich', 'London Liverpool Street'])


    @patch('pandas.read_csv')
    def test_check_recorded_data(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({
            'departure': ['Norwich'],
            'destination': ['London Liverpool Street'],
            'date': ['06 25'],
            'time': ['12:00']
        })
        data_info = self.chatbot.check_recorded_data()
        self.assertEqual(data_info, {
            'departure': 'Norwich',
            'destination': 'London Liverpool Street',
            'date': '06 25',
            'time': '12:00'
        })

    def test_convert_date(self):
        self.assertEqual(self.chatbot.convert_date("today").date(), datetime.now().date())
        self.assertEqual(self.chatbot.convert_date("tomorrow").date(), (datetime.now() + timedelta(days=1)).date())
        self.assertEqual(self.chatbot.convert_date("15 June").date(), datetime(2024, 6, 15).date())

    def test_extract_date_entities(self):
        self.assertEqual(self.chatbot.extract_date_entities("I need a ticket for the 15th of June 2024").date(),
                         datetime(2024, 6, 15).date())

    def test_extract_time_entities(self):
        self.assertEqual(self.chatbot.extract_time_entities("The train leaves at 15:00"), '15:00')

    def test_get_intent(self):
        knowledge_base = {
            "book_train_tickets": {"patterns": ["I want to book a ticket", "Book a train ticket"],
                                   "responses": ["Sure, I can help with that."]},
            "ask_date_time": {"patterns": ["What is the time?", "Tell me the date"],
                              "responses": ["It's 3 PM. Today is 15th June."]}
        }
        self.assertEqual(self.chatbot.get_intent("I want to book a ticket", knowledge_base), "book_train_tickets")
        self.assertEqual(self.chatbot.get_intent("What is the time?", knowledge_base), "ask_date_time")

    @patch('builtins.open', new_callable=mock_open, read_data="Norwich,London Liverpool Street\n")
    def test_partial_matching(self, mock_file):
        matches = self.chatbot.partial_matching('Noriwch')
        self.assertIn('Norwich', matches)

    @patch('pandas.read_csv')
    def test_verify_single_location(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({
            'departure': ['Norwich'],
            'destination': [''],
            'date': [''],
            'time': ['']
        })
        self.assertTrue(self.chatbot.verify_single_location('Norwich'))

    @patch('pandas.read_csv')
    def test_verify_location(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({
            'departure': ['Norwich'],
            'destination': ['London Liverpool Street'],
            'date': [''],
            'time': ['']
        })
        self.assertTrue(self.chatbot.verify_location('Norwich', 'London Liverpool Street'))

    @patch('pandas.read_csv')
    def test_verify_datetime(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({
            'departure': ['Norwich'],
            'destination': ['London'],
            'date': ['06 25'],
            'time': ['12:00']
        })
        self.chatbot.date = datetime.strptime('06 25', "%d %m")
        self.chatbot.time = '12:00'
        self.assertTrue(self.chatbot.verify_datetime())

    @patch('pandas.read_csv')
    def test_retry_fetching_data(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({
            'departure': ['Norwich'],
            'destination': ['London'],
            'date': ['06 25'],
            'time': ['12:00']
        })
        self.chatbot.data_scraping = MagicMock()
        self.chatbot.retry_fetching_data("book a train ticket")
        self.chatbot.data_scraping.assert_called_once()

    def test_chatbot_response(self):
        knowledge_base = {
            "book_train_tickets": {"patterns": ["I want to book a ticket"],
                                   "responses": ["Sure, I can help with that."]},
            "ask_date_time": {"patterns": ["What is the time?"], "responses": ["It's 3 PM."]}
        }
        response = self.chatbot.chatbot_response("I want to book a ticket", knowledge_base)
        self.assertEqual(response, "Sure, I can help with that.")


if __name__ == '__main__':
    unittest.main()
