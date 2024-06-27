from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import csv
import re
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile


class GreaterAnglia(object):
    def __init__(self):
        # Initialize the Selenium WebDriver with Chrome options
        chrome_options = Options()
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/97.0.4692.99 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless")  # headless mode
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.logo = (By.XPATH, "//img[@id='header-logo']")
        self.cookies = (By.XPATH, "/html/body/div[1]/div/div[4]/div[1]/div[2]/button[4]")
        self.from_field = (By.XPATH, "(//input[contains(@id, 'from')])[1]")
        self.to_field = (By.XPATH, "//div[contains (@class, 'input-group')]/input[contains(@class, 'to-station')]")
        self.fild_time_and_tickets_button = (By.XPATH, "//div[contains(@class, 'footer')]/div/span/button")
        self.from_to_select = (By.XPATH, "//ul[contains(@id, 'from-buy')]/li[1]")
        self.to_to_select = (By.XPATH, "//ul[contains(@id, 'listbox_to')]/li[1]")
        self.more = (By.XPATH, "//*[@id='act-a']/span[1]")
        self.search_result_page = (By.XPATH, "//*[@id='app']/div/div/div[1]/header/div[1]/a[2]/picture/img")
        self.cheapest_fare = (By.XPATH, "//*[@id='app']/div/div/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div["
                                        "2]/div/div[1]/h3/span[2]/span/span")
        self.button = None
        self.updated_url = None
        self.url = None

    def wait(self, condition, timeout=60):
        return WebDriverWait(self.driver, timeout).until(condition)

    def handle_cookies(self, url):
        self.driver.get(url)
        try:
            self.button = self.wait(EC.element_to_be_clickable(self.cookies))
            self.button.click()
        except Exception as e:
            raise Exception("Cookies button not found or not clickable") from e

    def search_for_train(self, origin, destination, replacing_date):
        try:
            self.wait(EC.visibility_of_element_located(self.logo))
            more = self.wait(EC.element_to_be_clickable(self.more))
            more.click()

            from_field = self.wait(EC.element_to_be_clickable(self.from_field))
            from_field.send_keys(origin)

            from_to_select = self.wait(EC.visibility_of_element_located(self.from_to_select))
            from_to_select.click()

            to_field = self.wait(EC.visibility_of_element_located(self.to_field))
            to_field.send_keys(destination)

            to_to_select = self.wait(EC.element_to_be_clickable(self.to_to_select))
            to_to_select.click()

            search_button = self.wait(EC.element_to_be_clickable(self.fild_time_and_tickets_button))
            search_button.click()

            self.wait(EC.visibility_of_element_located(self.cheapest_fare))
            self.url = self.driver.current_url
            self.updated_url = self.replace_url(replacing_date)
            return self.updated_url
        except Exception as e:
            print(e)

    def replace_url(self, replacing_date):
        date_pattern = r"\d{4}-\d{2}-\d{2}"
        if not re.search(date_pattern, self.url):
            raise ValueError("Invalid URL: Date pattern not found")
        updated_url = re.sub(date_pattern, replacing_date, self.url)
        return updated_url

    def find_cheapest_ticket(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span._1w9rlv9")))
            self.driver.implicitly_wait(10)
            # Get the source of the page
            element = self.driver.find_element(By.XPATH, "//span[contains(@class, '_1w9rlv9')]/span/span")
            cheapest_fare = element.text

            return cheapest_fare

        except Exception as e:
            print(e)

    def run(self, from_station, to_station, date_str):
        current_year = datetime.now().year
        month, date = date_str.split()
        constructed_date = f"{current_year}-{month}-{date}"

        url_ga = "https://www.greateranglia.co.uk/"
        self.handle_cookies(url_ga)
        updated_url = self.search_for_train(from_station, to_station, constructed_date)
        cheapest_fare = self.find_cheapest_ticket(updated_url)

        date_obj = datetime.strptime(f"{current_year} {date_str}", "%Y %m %d")
        formatted_date = date_obj.strftime("%a %d %b %Y")

        self.driver.quit()
        with open('train_data.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Origin', 'Destination', 'Fare', 'URL'])
            writer.writerow([formatted_date, from_station, to_station, cheapest_fare, updated_url])
