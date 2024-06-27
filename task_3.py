import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
import os
import json
import random
import re
import spacy
import pandas as pd
from task_3_contingency_details import ContingencyDetails


class ContingencyPlan(object):
    def __init__(self):
        self.best_intent = None
        self.nlp = spacy.load("en_core_web_lg")
        self.recorded_verified_data = os.getcwd() + "/verified_data.csv"
        self.recorded_contingency_data = os.getcwd() + "/contingency_plan_recorded_data.csv"
        self.contingency_details = ContingencyDetails()

    def load_contingency_knowledge_base(self):
        with open("contingency_intents.json") as f:
            return json.load(f)

    def reset_recorded_verified_data(self):
        f = open(self.recorded_verified_data, 'w')
        f.write("")
        f.write("station_1,station_2,blockage")
        f.close()

    def reset_recorded_contingency_data(self):
        f = open(self.recorded_contingency_data, 'w')
        f.write("")
        f.write("plan_code,train_status,train_service,peak")
        f.close()

    def fetch_blocked_stations(self):
        blocked_stations = []
        with open('blocked_stations_data.csv', mode='r') as file:
            lines = file.readlines()
            header = lines[0].strip().split(',')
            station_1_index = header.index('station_1')
            station_2_index = header.index('station_2')

            for line in lines[1:]:
                row = line.strip().split(',')
                stations = []
                station_1 = row[station_1_index]
                station_2 = row[station_2_index]
                if station_1:
                    stations.append(station_1)
                if station_2:
                    stations.append(station_2)
                if stations:
                    blocked_stations.append(stations)
        return blocked_stations

    def get_contingency_intent(self, text, knowledge_base):
        doc = self.nlp(text)
        self.best_intent = None
        highest_sim = 0
        sim_thresh = 0.5
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

    def check_contingency_recorded_data(self):
        csv_path = 'contingency_plan_recorded_data.csv'
        df = pd.read_csv(csv_path)
        if df.empty:
            return False, ""
        if df.iloc[0].isnull().any():
            return False, ""
        else:
            response_for_contingency_plan = self.get_contingency_plan()
            return True, response_for_contingency_plan

    def get_contingency_plan(self):
        csv_path = 'contingency_plan_recorded_data.csv'
        df = pd.read_csv(csv_path)
        contingency_data = df.iloc[0]
        plan_code = contingency_data['plan_code']
        status = contingency_data['train_status']
        service = contingency_data['train_service']
        peak = contingency_data['peak']
        delayed_time = self.contingency_details.get_peak_message(plan_code, status, service, peak)
        self.reset_recorded_contingency_data()
        return delayed_time

    def verify_stations(self, station_1, station_2):
        df = pd.read_csv('blocked_stations_data.csv')
        matched_row = df[(df['station_1'].str.strip().str.lower() == station_1.strip().lower()) &
                         (df['station_2'].str.strip().str.lower() == station_2.strip().lower())]
        if not matched_row.empty:
            return True
        else:
            return False

    def verify_stations_and_blockage(self):
        df_verified = pd.read_csv('verified_data.csv')
        df_blocked = pd.read_csv('blocked_stations_data.csv')

        if df_verified.iloc[0].isnull().any():
            return True, "Can you please provide more details."

        station_1 = df_verified.iloc[0]['station_1']
        station_2 = df_verified.iloc[0]['station_2']
        blockage = df_verified.iloc[0]['blockage']

        for index, row in df_blocked.iterrows():
            if (row['station_1'] == station_1 and
                    row['station_2'] == station_2 and
                    row['blockage'] == blockage):
                self.get_plan_code()
                return True, "Can you please provide more details."

        self.reset_recorded_verified_data()
        return False, ("I am sorry, it seems like the data you have provided is not consistent with the one I "
                       "have. Please re-enter the correct details.")

    def save_stations_to_verify(self, station_1, station_2):
        df = pd.read_csv('verified_data.csv')
        df.at[0, 'station_1'] = station_1
        df.at[0, 'station_2'] = station_2
        df.to_csv('verified_data.csv', index=False)

    def save_blockage_to_verify(self, blockage):
        df = pd.read_csv('verified_data.csv')
        df.at[0, 'blockage'] = blockage
        df.to_csv('verified_data.csv', index=False)

    def get_plan_code(self):
        df_verified = pd.read_csv('verified_data.csv')
        df_blocked = pd.read_csv('blocked_stations_data.csv')

        station_1 = df_verified.iloc[0]['station_1']
        station_2 = df_verified.iloc[0]['station_2']
        blockage = df_verified.iloc[0]['blockage']

        for index, row in df_blocked.iterrows():
            if (row['station_1'] == station_1 and
                    row['station_2'] == station_2 and
                    row['blockage'] == blockage):
                df_cont_plan_rec_data = pd.read_csv('contingency_plan_recorded_data.csv')
                df_cont_plan_rec_data.at[0, 'plan_code'] = row['code_plan']
                df_cont_plan_rec_data.to_csv('contingency_plan_recorded_data.csv', index=False)

    def extract_blocked_stations(self, text):
        stations_match = re.search(r'\bbetween\b\s+([A-Za-z\s]+)\s+\band\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        if stations_match:
            first_station = stations_match.group(1).strip()
            second_station = stations_match.group(2).strip()
            if first_station == "" or second_station == "":
                return "Oops, it looks like there's been a mis-input. Please try again."
            verified_stations = self.verify_stations(first_station, second_station)
            if verified_stations is True:
                self.save_stations_to_verify(first_station, second_station)
                is_verified, is_verified_response = self.verify_stations_and_blockage()
                if is_verified is True:
                    return is_verified_response
                elif is_verified is False:
                    return is_verified_response
                return True
            else:
                self.fetch_blocked_stations()
                return ("Please choose the correct stations. Here is a list of stations for which I have the "
                        "contingencies for  Careful with spellings.")
        elif stations_match is None:
            return "Oops, it looks like there's been a mis-input. Please try again."

    def extract_and_save_status(self, text):
        status_match = re.search(r'\b(The status of the train is|The train is)\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        if status_match:
            status = status_match.group(2)
            if status == "":
                return "Oops, it looks like there's been a mis-input. PLease try again."
            elif status not in ["running", "amended", "cancelled"]:
                return "I'm sorry the status of the train should either be running, amended, or cancelled."
            else:
                df_status = pd.read_csv('contingency_plan_recorded_data.csv')
                df_status.at[0, 'train_status'] = status
                df_status.to_csv('contingency_plan_recorded_data.csv', index=False)
                return True
        elif status_match is None:
            return "Oops, it looks like there's been a mis-input. Please try again."

    def extract_and_save_service(self, text):
        pattern_1 = re.search(r'\bThe train service is\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        pattern_2 = re.search(r'\bIt is a train service\b\s+([A-Za-z\s]+)', text, re.IGNORECASE)
        pattern_3 = re.search(r'\bIt is a\b\s+([A-Za-z\s]+)\s+train\b', text, re.IGNORECASE)

        service = None

        if pattern_1:
            service = pattern_1.group(1).strip()
        elif pattern_2:
            service = pattern_2.group(1).strip()
        elif pattern_3:
            service = pattern_3.group(1).strip()

        print(service)
        if service in ["Greater Anglia", "Freight"]:
            df_service = pd.read_csv('contingency_plan_recorded_data.csv')
            df_service.at[0, 'train_service'] = service
            df_service.to_csv('contingency_plan_recorded_data.csv', index=False)
            return True
        else:
            return "I'm sorry, the train service should either be Greater Anglia or Freight."

    def extract_time(self, text):
        time_match = re.search(r'\bThe time is\b\s+((?:[01]?[0-9]|2[0-3]):[0-5][0-9])', text, re.IGNORECASE)
        if time_match:
            time_text = time_match.group(1).strip()
            time_obj = datetime.strptime(time_text, "%H:%M").time()

            if datetime.strptime("04:30", "%H:%M").time() <= time_obj <= datetime.strptime("09:30",
                                                                                           "%H:%M").time():
                peak_category = "am_peak"
            elif datetime.strptime("16:00", "%H:%M").time() <= time_obj <= datetime.strptime("19:00",
                                                                                             "%H:%M").time():
                peak_category = "pm_peak"
            elif datetime.strptime("09:30", "%H:%M").time() <= time_obj <= datetime.strptime("16:00",
                                                                                             "%H:%M").time():
                peak_category = "off_peak"
            else:
                peak_category = "non_peak"

            current_date = datetime.now()
            if current_date.weekday() > 4:
                peak_category = "non-peak"

            df = pd.read_csv('contingency_plan_recorded_data.csv')
            df.at[0, 'peak'] = peak_category
            df.to_csv('contingency_plan_recorded_data.csv', index=False)
            return True
        else:
            return "Oops, it looks like there's been a mis-input. Please try again."

    def chatbot_response(self, user_input):
        knowledge_base = self.load_contingency_knowledge_base()
        intent = self.get_contingency_intent(user_input, knowledge_base)
        print(intent)
        response = random.choice(knowledge_base[intent]["responses"])
        if intent is not None:
            if intent == "partial_blockage":
                self.save_blockage_to_verify("partial")
                is_verified, is_verified_response = self.verify_stations_and_blockage()
                if is_verified is True:
                    response = is_verified_response
                    return response, ""
                return response, ""

            if intent == "full_blockage":
                self.save_blockage_to_verify("full")
                is_verified, is_verified_response = self.verify_stations_and_blockage()
                if is_verified is True:
                    response = is_verified_response
                    return response, ""
                return response, ""

            if intent == "blocked_stations":
                stations_exist = self.extract_blocked_stations(user_input)
                if stations_exist is True:
                    return response, ""
                else:
                    response = stations_exist
                    return response, ""

            if intent == "train_status":
                train_status = self.extract_and_save_status(user_input)
                check_contingency_found, contingency_response = self.check_contingency_recorded_data()
                if check_contingency_found is True:
                    return contingency_response
                if train_status is True:
                    return response, ""
                else:
                    response = train_status
                    return response, ""

            if intent == "train_service":
                anglia_service = self.extract_and_save_service(user_input)
                check_contingency_found, contingency_response = self.check_contingency_recorded_data()
                if check_contingency_found is True:
                    return contingency_response
                if anglia_service is True:
                    return response, ""
                else:
                    response = anglia_service
                    return response, ""

            if intent == "time_intent":
                time = self.extract_time(user_input)
                check_contingency_found, contingency_response = self.check_contingency_recorded_data()
                if check_contingency_found is True:
                    return contingency_response, ""
                if time is True:
                    return response, ""
                else:
                    response = time
                    return response, ""

            if intent == "change_conversation":
                return response, intent

            else:
                return response, ""
        else:
            return "I'm sorry, I didn't understand that."

    # def main(self):
    #     knowledge_base = self.load_prediction_knowledge_base()
    #     print("Chatbot: I can give you contingency plans for partial and full blockages. Please give me more details. "
    #           "I would require the type of blockage, the stations between which the blockage occurs, the type of "
    #           "train service, the time and the status of the train.")
    #     while True:
    #         user_input = input("You(I am in task 3): ")
    #         if user_input.lower() in ["exit", "quit"]:
    #             print("Chatbot: Goodbye!")
    #             break
    #         response = self.chatbot_response(user_input, knowledge_base)
    #
    #         if response == "Alright, lets talk about something else.":
    #             return response
    #         print("Chatbot:", response)
    def main(self, user_input):
        response = self.chatbot_response(user_input)
        return response

if __name__ == "__main__":
    contingency = ContingencyPlan()
    # contingency.main()
    print(contingency.fetch_blocked_stations())
    # print(contingency.extract_blocked_stations("The blockage is between and Maningtree."))
    # print(contingency.verify_stations("Diss", "Norwich"))
    # contingency.save_stations_to_verify("Diss", "Trowse")
    # contingency.save_blockage_to_verify("partial")
    # print(contingency.verify_stations_and_blockage())
    # contingency.get_plan_code()
    # print(contingency.extract_and_save_service("The train service is Greater Anglia."))
    # contingency.extract_time("The time is 12:00.")
