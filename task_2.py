import warnings

warnings.filterwarnings("ignore")
import os
import json
import random
import re
import spacy
import pandas as pd
from fuzzywuzzy import fuzz
from train_delay import PredictingDelay


class PredictDelay(object):
    def __init__(self):
        self.best_intent = None
        self.nlp = spacy.load("en_core_web_lg")
        self.recorded_data = os.getcwd() + "/pred_delay_recorded_data.csv"
        self.predicting = PredictingDelay()
        self.is_done = False

    def reset_recorded_data(self):
        f = open(self.recorded_data, 'w')
        f.write("")
        f.write("departure,destination,delay_time,exp_arr_time")
        f.close()

    def check_pred_delay_recorded_data(self):
        csv_path = 'pred_delay_recorded_data.csv'
        df = pd.read_csv(csv_path)
        if df.empty:
            return False, ""
        if df.iloc[0].isnull().any():
            return False, ""
        else:
            response_for_delay_time = self.predict_delay()
            return True, response_for_delay_time

    def predict_delay(self):
        csv_path = 'pred_delay_recorded_data.csv'
        df = pd.read_csv(csv_path)
        prediction_data = df.iloc[0]
        departure = prediction_data['departure']
        destination = prediction_data['destination']
        delay_time = prediction_data['delay_time']
        exp_arr_time = prediction_data['exp_arr_time']
        delayed_time = self.predicting.main(departure, destination, delay_time, exp_arr_time)
        self.reset_recorded_data()
        self.is_done = True
        return delayed_time

    def fetch_all_stations_with_codes(self):
        stations_all_data = open('station_codes_and_names.csv', 'r')
        stations_all_list = []
        data = stations_all_data.readlines()
        for row in data[1:]:
            row_data = row.strip().split(",")
            stations_all_list.append(row_data)
        stations_all_data.close()
        return stations_all_list

    def fetch_all_stations(self):
        stations_data = open('station_codes_and_names.csv', 'r')
        stations_list = []
        data = stations_data.readlines()
        for stations in data[1:]:
            stations = stations.split(",")
            name = stations[0]
            stations_list.append(name)
        stations_data.close()
        return stations_list

    def verify_single_location(self, location):
        csv_delay_path = 'pred_delay_recorded_data.csv'
        df = pd.read_csv(csv_delay_path)
        stations_list = self.fetch_all_stations_with_codes()

        station_code = None
        for st in stations_list:
            station_name = st[0].strip().upper()
            station_code = st[1].strip().upper()
            if station_name == location.strip().upper():
                station_code = station_code
                break

        if station_code:
            if self.best_intent == "dep_station":
                df.at[0, 'departure'] = station_code
            elif self.best_intent == "arr_station":
                df.at[0, 'destination'] = station_code
            else:
                return False
            df.to_csv(csv_delay_path, index=False)
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

    def get_pred_intent(self, text, knowledge_base):
        doc = self.nlp(text)
        self.best_intent = None
        highest_sim = 0
        sim_thresh = 0.6
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

    def extract_departure_station(self, text):
        departure_match = re.search(r'\bdeparture station is\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        if departure_match:
            departure = departure_match.group(1).strip()
            if departure == "":
                return "Oops, it looks like you did not enter a station name. Please try again."
            verified_location = self.verify_single_location(departure)
            if verified_location:
                return True
            else:
                self.partial_matching(departure)
                return "Please choose the correct station. Careful with spellings."
        elif departure_match is None:
            return "Oops, it looks like you did not enter a station name. Please try again."

    def extract_arrival_station(self, text):
        destination_match = re.search(r'\barrival station is\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        if destination_match:
            destination = destination_match.group(1).strip()
            if destination == "":
                return "Oops, it looks like you did not enter a station name. Please try again."
            verified_location = self.verify_single_location(destination)
            if verified_location:
                return True
            else:
                self.partial_matching(destination)
                return "Please choose the correct station. Careful with spellings."
        elif destination_match is None:
            return "Oops, it looks like you did not enter a station name. Please try again."

    def extract_departure_delay(self, text):
        threshold = 70
        delay_match = re.search(r'\b(departing delay is|delay is)\b\s+([A-Za-z0-9\s]+)', text, re.IGNORECASE)
        if delay_match:
            delay_text = delay_match.group(2).strip()
            if delay_text == "":
                return "Oops, it looks like you wanted to enter a delay time. Please try again."
            extract_delay_text = delay_text.split()
            if len(extract_delay_text) < 2:
                return "Can you be more specific with the delay time please?"
            sim_ratio = fuzz.partial_ratio(extract_delay_text[1].upper(), "MINUTES")
            print(sim_ratio)
            if sim_ratio >= threshold:
                number_match = re.search(r'\d+', delay_text)
                if number_match is None:
                    return "Oops, it seems like there was a mis-input. Please try again."
                csv_delay_path = 'pred_delay_recorded_data.csv'
                df = pd.read_csv(csv_delay_path)
                df.at[0, 'delay_time'] = int(number_match.group(0))
                df.to_csv(csv_delay_path, index=False)
                return True
            else:
                return "Oops, it seems like there was a mis-input. Please try again."
        elif delay_match is None:
            return "Oops, it looks like you wanted to enter a delay time. Please try again."

    def extract_expected_arrival_time(self, text):
        exp_arr_match = re.search(r'\b(My expected arrival time is|My expected time of arrival is)\b\s+((?:[01]?['
                                  r'0-9]|2[0-3]):[0-5][0-9])', text, re.IGNORECASE)
        if exp_arr_match:
            exp_arr_text = exp_arr_match.group(2).strip()
            csv_delay_path = 'pred_delay_recorded_data.csv'
            df = pd.read_csv(csv_delay_path)
            df.at[0, 'exp_arr_time'] = exp_arr_text
            df.to_csv(csv_delay_path, index=False)
            return True
        else:
            return "Oops, it looks like there's been a mis-input. Please try again."

    def load_prediction_knowledge_base(self):
        with open("prediction_intents.json") as f:
            return json.load(f)

    def chatbot_response(self, user_input):
        knowledge_base = self.load_prediction_knowledge_base()
        intent = self.get_pred_intent(user_input, knowledge_base)  # calling intent function
        print(intent)
        response = random.choice(knowledge_base[intent]["responses"])  # response from KB
        if intent is not None:
            if intent == "dep_station":
                dept_st_response = self.extract_departure_station(user_input)
                check_delay_found, delay_response = self.check_pred_delay_recorded_data()
                if check_delay_found is True:
                    return delay_response, ""
                if dept_st_response is True:
                    return response, ""
                else:
                    response = dept_st_response
                    return response, ""

            elif intent == "arr_station":
                arr_st_response = self.extract_arrival_station(user_input)
                check_delay_found, delay_response = self.check_pred_delay_recorded_data()
                if check_delay_found is True:
                    return delay_response, ""
                if arr_st_response is True:
                    return response, ""
                else:
                    response = arr_st_response
                    return response, ""

            elif intent == "dep_delay":
                dep_delay_response = self.extract_departure_delay(user_input)
                check_delay_found, delay_response = self.check_pred_delay_recorded_data()
                if check_delay_found is True:
                    return delay_response, ""
                if dep_delay_response is True:
                    return response, ""
                else:
                    response = dep_delay_response
                    return response, ""

            elif intent == "expected_arrival":
                exp_arr_response = self.extract_expected_arrival_time(user_input)
                check_delay_found, delay_response = self.check_pred_delay_recorded_data()
                if check_delay_found is True:
                    return delay_response, ""
                if exp_arr_response is True:
                    return response, ""
                else:
                    response = exp_arr_response
                    return response, ""

            elif intent == "change_conversation":
                return response, intent

            elif intent == "predict_delay":
                return response, ""

            else:
                return response, ""
        else:
            return "I'm sorry, I didn't understand that."

    # def main(self, user_input):
    #     while True:
    #         if user_input.lower() in ["exit", "quit"]:
    #             break
    #         response = self.chatbot_response(user_input)
    #         if response == "Alright, lets talk about something else. Any details that you have mentioned are saved.":
    #             return response
    #         if self.is_done is True:
    #             break
    #         return response
    def main(self, user_input):
        response = self.chatbot_response(user_input)
        return response

# if __name__ == "__main__":
#     predict_delay = PredictDelay()
#     predict_delay.reset_recorded_data()
#     predict_delay.main()
#     # print(predict_delay.fetch_all_stations_with_codes())
#     # print(predict_delay.extract_expected_arrival_time("My expected time of arrival is 15:30."))
