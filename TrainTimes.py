from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import re
import time
import random
from datetime import datetime
import csv


class TrainTimes:
    def __init__(self):
        self.constructed_url = None
        chrome_options = Options()
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/97.0.4692.99 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless")  # headless mode
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def construct_url(self, from_station, to_station, time_str, date_str):
        base_url = "https://traintimes.org.uk"
        current_year = datetime.now().year
        month, date = date_str.split()
        from_station_encoded = from_station.replace(" ", "+")
        to_station_encoded = to_station.replace(" ", "+")
        self.constructed_url = f"{base_url}/{from_station_encoded}/{to_station_encoded}/{time_str}/{current_year}-{month}-{date}"
        return self.constructed_url

    def random_delay(self, min_seconds=0.1, max_seconds=0.5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scraping(self, url):
        try:
            self.driver.get(url)
            self.random_delay()

            elements = self.driver.find_elements(By.XPATH,
                                                 "//ul[contains(@class, 'results')]/li/small[contains(text(), 'Single')]")
            lowest_price = None
            for element in elements:
                element_text = element.text
                prices = re.findall(r"£(\d+\.\d{2}) [\w\s-]*Single", element_text)
                if prices:
                    for price in prices:
                        price_str = price.split()[0]
                        price_value = float(price_str[1:])
                        if lowest_price is None or price_value < lowest_price:
                            lowest_price = price_value

            if lowest_price is not None:
                formatted_price = f"£{lowest_price:.2f}"
                return formatted_price
            else:
                return None
        except Exception as e:
            print(e)
        finally:
            self.driver.quit()

    def run(self, from_station, to_station, time, date_str):
        url = self.construct_url(from_station, to_station, time, date_str)
        cheapest_fare = self.scraping(url)
        current_year = datetime.now().year
        date_obj = datetime.strptime(f"{current_year} {date_str}", "%Y %m %d")
        formatted_date = date_obj.strftime("%a %d %b %Y")
        with open('train_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([formatted_date, from_station, to_station, cheapest_fare, url])
