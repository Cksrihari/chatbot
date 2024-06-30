import sys
import time

from TrainTimes import TrainTimes
from GreaterAnglia import GreaterAnglia
import csv
from datetime import datetime


class MainScraping(object):
    def __init__(self):
        self.tt_scraper = TrainTimes()
        self.ga_scraper = GreaterAnglia()

    @staticmethod
    def slow_print(text):  # Delayed printing function
        for character in text:
            sys.stdout.write(character)  # writes the character
            sys.stdout.flush()
            time.sleep(0.01)

    def cheapest_compared(self):
        cheapest_fare = float('inf')
        cheapest_rows = []

        with open("train_data.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                fare = float(row['Fare'].replace('£', ''))

                if fare < cheapest_fare:
                    cheapest_fare = fare
                    cheapest_rows = [row]
                elif fare == cheapest_fare:
                    cheapest_rows.append(row)

        if cheapest_rows:
            date = cheapest_rows[0]['Date']
            origin = cheapest_rows[0]['Origin']
            destination = cheapest_rows[0]['Destination']

            if len(cheapest_rows) == 1:
                fare = cheapest_rows[0]['Fare']
                url = cheapest_rows[0]['URL']
                self.slow_print(f"Origin: {origin}")
                self.slow_print(f"Destination: {destination}")
                self.slow_print(f"Date: {date}")
                self.slow_print(f"Cheapest Fare: {fare}")
                self.slow_print(f"URL: {url}")
            else:
                fare = cheapest_rows[0]['Fare']
                url1 = cheapest_rows[0]['URL']
                url2 = cheapest_rows[1]['URL']
                self.slow_print(f"Origin: {origin}")
                self.slow_print(f"Destination: {destination}")
                self.slow_print(f"Date: {date}")
                self.slow_print(f"Cheapest Fare: {fare}")
                self.slow_print(f"URL 1: {url1}")
                self.slow_print(f"URL 2: {url2}\n")
        else:
            self.slow_print("No cheapest fare, please try different combinations")

    def convert_date_format(self, date_str):
        try:
            # Check if the input is already in the required format
            if len(date_str) == 5 and date_str[2] == ' ':
                # Ensure it's in 'mm dd' format (simple validation)
                month, day = date_str.split(' ')
                if month.isdigit() and day.isdigit() and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    return date_str

            # Try parsing with fractional seconds (float)
            try:
                datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                # If parsing with float fails, try without fractional seconds
                datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

            # Format the datetime object to 'mm dd' format
            formatted_date = datetime_obj.strftime('%m %d')

            return formatted_date
        except ValueError:
            return None

    def main(self, departure, destination, date, time):
        date = self.convert_date_format(date)
        self.ga_scraper.run(departure, destination, date)
        self.tt_scraper.run(departure, destination, time, date)
        return self.cheapest_compared()

if __name__ == "__main__":
    main = MainScraping()
    main.main("Norwich","London Liverpool Street","06 27","15:00")
