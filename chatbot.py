import os
import json
import random
import re
import time

import spacy
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from fuzzywuzzy import fuzz
from main_scraping import MainScraping
from datetime import datetime, timedelta
import csv
from task_2 import PredictDelay
from task_3 import ContingencyPlan


class ChatBot(object):
    def __init__(self):
        self.time = None
        self.date = None
        self.departure = None
        self.destination = None
        self.best_intent = None
        self.data_info = {}
        self.nlp = spacy.load("en_core_web_lg")
        self.recorded_data = os.getcwd() + "/recorded_data.csv"
        self.scraping = MainScraping()
        self.predict = PredictDelay()
        self.contingency = ContingencyPlan()
        self.leave_loop = False

    def load_knowledge_base(self):
        with open("intents.json") as f:
            return json.load(f)

    def reset_recorded_data(self):
        f = open(self.recorded_data, 'w')
        f.write("")
        f.write("departure,destination,date,time")

    def check_recorded_data(self):
        f = open(self.recorded_data, 'r')
        data = f.readlines()
        for info in data[1:]:
            info = info.split(",")
            self.data_info['departure'] = info[0]
            self.data_info['destination'] = info[1]
            self.data_info['date'] = info[2]
            self.data_info['time'] = info[3].rstrip("\n")
        f.close()
        return self.data_info

    def fetch_all_stations(self):
        stations_data = open('stations.csv', 'r')
        stations_list, station_dict = [], {}
        data = stations_data.readlines()
        for stations in data[1:]:
            stations = stations.split(",")
            name = stations[0]
            stations_list.append(name)
        return stations_list

    def verify_single_location(self, location):
        csv_path = 'recorded_data.csv'
        df = pd.read_csv(csv_path)
        stations_list = self.fetch_all_stations()
        stations_dict = {}
        for st in stations_list:
            if st.upper() == location.upper():
                stations_dict["location"] = location
        if "location" in stations_dict.keys() and self.best_intent == "to_station":
            df.at[0, 'destination'] = stations_dict['location']
            df.to_csv(csv_path, index=False)
            return True
        if "location" in stations_dict.keys() and self.best_intent == "from_station":
            df.at[0, 'departure'] = stations_dict['location']
            df.to_csv(csv_path, index=False)
            return True
        else:
            return False

    def verify_location(self, departure, destination):
        csv_path = 'recorded_data.csv'
        df = pd.read_csv(csv_path)
        stations_list = self.fetch_all_stations()
        stations_dict = {}
        for st in stations_list:
            if st.upper() == departure.upper():
                stations_dict["departure"] = departure
            if st.upper() == destination.upper():
                stations_dict["destination"] = destination

        if "departure" not in stations_dict.keys() and "destination" not in stations_dict.keys():
            self.partial_matching(departure)
            self.partial_matching(destination)
            return False
        elif "departure" in stations_dict.keys() and "destination" not in stations_dict.keys():
            self.partial_matching(destination)
            df.at[0, 'departure'] = stations_dict['departure']
            df.to_csv(csv_path, index=False)
            return False
        elif "departure" not in stations_dict.keys() and "destination" in stations_dict.keys():
            self.partial_matching(departure)
            df.at[0, 'destination'] = stations_dict['destination']
            df.to_csv(csv_path, index=False)
            return False
        elif "departure" in stations_dict.keys() and "destination" in stations_dict.keys():
            df.at[0, 'departure'] = stations_dict['departure']
            df.at[0, 'destination'] = stations_dict['destination']
            df.to_csv(csv_path, index=False)
            return True
        else:
            return False

    def partial_matching(self, input_station, threshold=90):
        stations_list = self.fetch_all_stations()
        partial_matches = []
        for station in stations_list:
            ratio = fuzz.partial_ratio(station.upper(), input_station.upper())
            if ratio >= threshold:
                partial_matches.append(station)

        if len(partial_matches) > 1:
            print(f"Multiple stations matched to {input_station}:\n" + "\n".join(partial_matches))
            return partial_matches

    # Extracting entities
    def extract_from_location(self, text):
        from_match = re.search(r'\bfrom\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)

        if from_match:
            departure = from_match.group(1).strip()
            if departure == "":
                return "Oops, it looks like you did not enter a station name. Please try again."

            verified_location = self.verify_single_location(departure)
            if verified_location:
                return True
            else:
                self.partial_matching(departure)
                return "Multiple locations found. Select from above"
        elif from_match is None:
            return "Oops, it looks like you did not enter a station name. Please try again."

    def extract_to_location(self, text):
        to_match = re.search(r'\bto\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)

        if to_match:
            destination = to_match.group(1).strip()
            if destination == "":
                return "Oops, it looks like you did not enter a station name. Please try again."
            verified_location = self.verify_single_location(destination)
            if verified_location:
                return True
            else:
                self.partial_matching(destination)
                return "Multiple locations found. Select from above"
        elif to_match is None:
            return "Oops, it looks like you did not enter a station name. Please try again."


    def extract_location_entities(self, text):
        # to_match
        match = re.search(r'\bfrom\b\s+([A-Za-z\s]+)\s+\bto\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        if match:
            departure = match.group(1).strip()
            destination = match.group(2).strip()
            verified_locations = self.verify_location(departure, destination)
            if verified_locations:
                self.departure = departure
                self.destination = destination
                return True
            else:
                print("Un-able to fetch desired stations")
                return False
        else:
            print("Invalid locations, Please check the locations entered.")
            return False

    def convert_date(self, user_input):
        current_date = datetime.now()
        words = user_input.split()

        # Handle 'today' and 'tomorrow'
        if 'today' in words:
            return current_date
        elif 'tomorrow' in words:
            return current_date + timedelta(days=1)

        # Remove ordinal suffixes from day numbers
        user_input = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', user_input)
        user_input = re.sub(r'of\s+', '', user_input)  # Remove 'of' if present

        # Try parsing different date formats
        date_formats = [
            "%d-%m-%Y",
            "%d %B %Y",
            "%d %B"
        ]

        for date_format in date_formats:
            try:
                date_obj = datetime.strptime(user_input, date_format)
                # If the format does not include a year, add the current year
                if date_format == "%d %B":
                    date_obj = date_obj.replace(year=current_date.year)
                return date_obj
            except ValueError:
                continue

        print(f"Unable to convert '{user_input}' to any known date format.")
        return None

    def extract_date_entities(self, text):
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                user_date = ent.text.lower()  # Convert to lowercase for case insensitivity
                if user_date == "today":
                    self.date = self.convert_date(user_date)
                elif user_date == "tomorrow":
                    self.date = self.convert_date(user_date)
                else:
                    self.date = self.convert_date(user_date)
                break
        return self.date

    def extract_time_entities(self, text):
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "TIME":
                self.time = ent.text
                break
        return self.time

    def verify_datetime(self):
        if not self.date or not self.time:
            return False

        csv_path = 'recorded_data.csv'
        df = pd.read_csv(csv_path)

        now = datetime.now()
        current_date = now.date()
        current_time = now.time()

        if self.date.date() > current_date:
            # Future date
            df.at[0, 'date'] = self.date.strftime("%m %d")
            df.at[0, 'time'] = self.time
            df.to_csv(csv_path, index=False)
            return True
        elif self.date.date() == current_date:
            # Current date
            extracted_time = datetime.strptime(self.time, "%H:%M").time()
            if extracted_time > current_time:
                df.at[0, 'date'] = self.date.strftime("%m %d")
                df.at[0, 'time'] = self.time
                df.to_csv(csv_path, index=False)
                return True
        return False

    def retry_fetching_data(self, text):
        recorded_data = self.check_recorded_data()

        if "departure" in recorded_data.keys() and recorded_data["departure"] not in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] not in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] not in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] not in ["", None]:
            check_data = self.check_recorded_data()
            print("Perfect! I will be back in a moment with best option available.")
            self.data_scraping()

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] not in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] not in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] not in ["", None]):
            self.extract_location_entities(text)

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] not in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] not in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] not in ["", None]):
            self.extract_location_entities(text)

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] not in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] not in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] not in ["", None]):
            self.extract_date_entities(text)

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] not in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] not in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] not in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] in ["", None]):
            self.extract_time_entities(text)

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] and recorded_data["date"] not in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] not in ["", None]):
            self.extract_location_entities(text)

        elif ("departure" in recorded_data.keys() and recorded_data["departure"] not in ["", None] \
            and "destination" in recorded_data.keys() and recorded_data["destination"] not in ["", None] \
            and "date" in recorded_data.keys() and recorded_data["date"] in ["", None] \
            and "time" in recorded_data.keys() and recorded_data["time"] in ["", None]):
            self.extract_date_entities(text)
            self.extract_time_entities(text)

        elif ("departure" not in recorded_data.keys() \
            and "destination" not in recorded_data.keys() \
            and "date" not in recorded_data.keys() \
            and "time" not in recorded_data.keys()):
            self.extract_location_entities(text)
            self.extract_date_entities(text)
            self.extract_time_entities(text)

    def extract_all_entities(self, text):
        self.extract_location_entities(text)
        self.verify_location(self.departure, self.destination)
        self.extract_date_entities(text)
        self.extract_time_entities(text)
        self.verify_datetime()

    def save_to_csv(self, filename = "recorded_data.csv"):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['departure', 'destination', 'date', 'time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({
                'departure': self.departure,
                'destination': self.destination,
                'date': self.date,
                'time': self.time
            })

    def get_intent(self, text, knowledge_base):
        doc = self.nlp(text)
        self.best_intent = None
        highest_sim = 0
        sim_thresh = 0.60
        for interaction_type, data in knowledge_base.items():
            for example in data["patterns"]:
                example_doc = self.nlp(example)
                sim = doc.similarity(example_doc)
                if sim > highest_sim:
                    highest_sim = sim
                    self.best_intent = interaction_type
        if highest_sim > sim_thresh:
            return self.best_intent
        else:
            self.best_intent = "unknown_intent"
        return self.best_intent

    def data_scraping(self):
        self.scraping.main(self.data_info['departure'], self.data_info['destination'],
                                             self.data_info['date'], self.data_info['time'])
        self.reset_recorded_data()

    def read_recorded_data(self):
        file_path = 'recorded_data.csv'
        required_columns = {'departure', 'destination', 'date', 'time'}
        recorded_data = {column: [] for column in required_columns}
        missing_columns = required_columns.copy()
        empty_columns = set()

        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames

            if fieldnames is None:
                return "The file is empty or incorrectly formatted."

            for column in required_columns:
                if column not in fieldnames:
                    recorded_data.pop(column)
                else:
                    missing_columns.discard(column)

            for row in reader:
                for column in recorded_data:
                    value = row[column]
                    recorded_data[column].append(value)
                    if value == '':
                        empty_columns.add(column)

        if empty_columns:
            empty_columns_message = ", ".join(sorted(empty_columns)) + " value(s) is/are empty."
        else:
            empty_columns_message = "No columns contain empty values."

        print("Recorded Data:", recorded_data)
        print("Empty Columns:", empty_columns_message)
    # chatbot response


    def chatbot_response(self, user_input):
        knowledge_base = self.load_knowledge_base()
        intent = self.get_intent(user_input, knowledge_base)  # calling intent function
        response = random.choice(knowledge_base[intent]["responses"])  # response from KB
        if intent is not None:
            if intent == "book_train_tickets":
                self.retry_fetching_data(user_input)
                return response, None

            elif intent == "ask_date_time":
                self.retry_fetching_data(user_input)
                if self.verify_datetime():
                    self.retry_fetching_data(user_input)
                    return response, None
                else:
                    return "Date or time cannot be in the past, please retry with valid input"

            elif intent == "from_station":
                departure_found = self.extract_from_location(user_input)
                if departure_found is True:
                    return response, None
                else:
                    response = departure_found
                return response, None

            elif intent == "to_station":
                destination_found = self.extract_to_location(user_input)
                if destination_found is True:
                    return response, None
                else:
                    response = destination_found
                    return response, None

            elif intent == "show_recorded_data":
                self.read_recorded_data()
                return response, None

            elif intent == "all_entities":
                self.extract_all_entities(user_input)
                self.save_to_csv()
                self.retry_fetching_data(user_input)
                return response, None

            elif intent == "predict_delay":
                response = self.predict.main(user_input)
                return response, intent

            elif intent == "contingency_plans":
                response = self.contingency.main(user_input)
                return response, intent

            else:
                return response, None
        else:
            return "I'm sorry, I didn't understand that."

    # def main(self):
    #     knowledge_base = self.load_knowledge_base()
    #     print("Chatbot: Hi, how can i help you?")
    #     while True:
    #         user_input = input("You: ")
    #         if user_input.lower() in ["exit", "quit", "bye"]:
    #             print("Chatbot: Goodbye!")
    #             break
    #         response = self.chatbot_response(user_input)
    #         print("Chatbot:", response)
    def main(self, user_input):
        response = self.chatbot_response(user_input)
        return response

#
# if __name__ == "__main__":
#     chatbot = ChatBot()
#     chatbot.main()