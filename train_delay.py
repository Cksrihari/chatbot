import pandas as pd
import joblib
from datetime import datetime, timedelta
from xgboost import XGBClassifier
import os

class PredictingDelay(object):
    def __init__(self):
        self.user_input = os.getcwd() + "/user_input.csv"

    def clear_user_input(self):
        f = open(self.user_input, 'w')
        f.write("")
        f.write("departure_station,arrival_station,date,day,is_weekday,peak_hour,hour,departure_delay")
        f.close()

    def transform_input(self, input_data, label_encoders):
        for col, mapping in label_encoders.items():
            if col in input_data:
                input_data[col] = mapping[input_data[col]]
        return input_data

    def is_peak_hour(self, current_time_par, weekday):
        peak_hour = 0
        morning_peak_start = datetime.strptime("06:30", "%H:%M").time()
        morning_peak_end = datetime.strptime("09:30", "%H:%M").time()
        evening_peak_start = datetime.strptime("16:29", "%H:%M").time()
        evening_peak_end = datetime.strptime("18:34", "%H:%M").time()

        current_time = current_time_par.time()
        if weekday == 1:
            if (morning_peak_start <= current_time <= morning_peak_end) or (
                    evening_peak_start <= current_time <= evening_peak_end):
                peak_hour = 1

        return peak_hour

    def main(self, dep_st, arr_st, dep_delay, exp_arr):
        curr_date = datetime.now()

        if curr_date.month == 2:
            with open('feb_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('feb_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        elif curr_date.month == 6:
            with open('june_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('june_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        elif curr_date.month == 7:
            with open('july_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('july_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        elif curr_date.month == 8:
            with open('aug_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('aug_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        elif curr_date.month == 10:
            with open('oct_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('oct_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        elif curr_date.month == 11:
            with open('nov_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('nov_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)
        else:
            with open('combined_months_model.pkl', 'rb') as file:
                model = joblib.load(file)
            with open('combined_months_label_encoders.pkl', 'rb') as file:
                label_encoders = joblib.load(file)

        if curr_date.weekday() == 5 or curr_date.weekday() == 6:
            weekday = 0
        else:
            weekday = 1

        peak_hour = self.is_peak_hour(curr_date, weekday)

        prediction_inputs = {
            'departure_station': dep_st,
            'arrival_station': arr_st,
            'date': curr_date.strftime("%d"),
            'day': curr_date.weekday(),
            'is_weekday': weekday,
            'peak_hour': peak_hour,
            'hour': curr_date.hour,
            'departure_delay': dep_delay
        }

        input_df = pd.DataFrame([prediction_inputs])
        input_df.to_csv('user_input.csv', index=False)

        input_data = pd.read_csv('user_input.csv')

        transformed_input_data = self.transform_input(input_data.iloc[0].to_dict(), label_encoders)
        input_df_transformed = pd.DataFrame([transformed_input_data])

        prediction = model.predict(input_df_transformed)
        delay_in_minutes = round(prediction[0])

        if delay_in_minutes <= 0:
            return "It seems your delayed time of arrival is still the same."

        exp_arr_time = datetime.strptime(exp_arr, "%H:%M")
        delayed_time = exp_arr_time + timedelta(minutes=delay_in_minutes)
        delayed_time_str = delayed_time.strftime("%H:%M")
        self.clear_user_input()
        file.close()
        return f"Your delayed time is {delayed_time_str}. Please adjust your schedule accordingly."


if __name__ == '__main__':
    predict_delay = PredictingDelay()
