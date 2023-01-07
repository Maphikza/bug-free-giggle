import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, ElementNotVisibleException
import json
import time

path = r"C:\Users\stapi\chromedriver"


def get_cik():
    """
    This function gets S&P 500 company information data from wikipedia and converts it to a pandas Dataframe which
    is then turned into a dictionary to be used in this custom_scraper.
    :return: Dictionary
    """
    data = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    cik_list = list(data['CIK'])
    securities_list = list(data["Security"])
    return dict(zip(securities_list, cik_list))


def fetch_outstanding_stock():
    """
    This function scrapes outstanding stock data that I use to calculate market caps for S&P 500 companies.
    :return: String
    """
    company_cik_dict = get_cik()
    with open("stocks_and_cik.json", encoding='utf-8', mode='w') as output_file:
        json.dump(company_cik_dict, output_file)

    for i, key in enumerate(company_cik_dict):
        service = Service(path)
        driver = webdriver.Chrome(service=service)

        url = f"https://www.sec.gov/edgar/browse/?CIK={int(company_cik_dict[key])}&owner=exclude"

        driver.get(url)
        time.sleep(3)
        section = driver.find_element(By.XPATH, '//*[@id="filingsStart"]/div[2]/div[3]/h5/a')
        try:
            ActionChains(driver=driver) \
                .move_to_element(section) \
                .pause(1) \
                .click() \
                .pause(1) \
                .perform()
        except (ElementNotInteractableException, ElementNotVisibleException):
            with open("last_run_logs.txt", "a") as inner_log_file:
                inner_log_file.write(f"This URL{url} failed.")

            continue

        filing = driver.find_element(By.XPATH, '//*[@id="selected-filings-annualOrQuarterly"]/ul/li[1]')

        filing_text = filing.find_element(By.TAG_NAME, 'span')

        ActionChains(driver=driver) \
            .move_to_element(filing_text) \
            .pause(1) \
            .click() \
            .pause(3) \
            .perform()

        wait = WebDriverWait(driver, 3)

        original_window = driver.current_window_handle

        wait.until(EC.number_of_windows_to_be(2))

        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        new_url = driver.current_url

        time.sleep(3)

        print(f"{key}")
        time.sleep(1)

        time.sleep(1)

        filter_data = driver.find_element(By.XPATH, '//*[@id="nav-filter-data"]/span[2]')
        try:
            ActionChains(driver=driver) \
                .move_to_element(filter_data) \
                .pause(2) \
                .click() \
                .pause(1) \
                .perform()
        except (ElementNotInteractableException, ElementNotVisibleException):
            with open("last_run_logs.txt", "a") as inner_log_file:
                inner_log_file.write(f"This URL{new_url} failed.")

            continue

        amounts_only = driver.find_element(By.XPATH, '//*[@id="nav-filter-dropdown"]/div[2]/input')

        ActionChains(driver=driver) \
            .move_to_element(amounts_only) \
            .pause(2) \
            .click() \
            .pause(1) \
            .perform()

        facts = driver.find_element(By.XPATH, '//*[@id="facts-menu"]/span')

        ActionChains(driver=driver) \
            .move_to_element(facts) \
            .pause(2) \
            .click() \
            .pause(1) \
            .perform()
        time.sleep(1)
        amounts_data = driver.find_element(By.XPATH, '//*[@id="taxonomies-menu-list-pagination"]/div[3]')

        with open("outstanding_shares_text.txt", "a") as scraped_output:
            scraped_output.write(f"({i})\n('{new_url}','{amounts_data.text}')\n")
        time.sleep(1)
        with open("last_run_logs.txt", "a") as inner_log_file:
            inner_log_file.write(f"{i} {key}: {company_cik_dict[key]} appended, successfully.\n({new_url}) - data was "
                                 f"captured successfully.\n")
        time.sleep(1)

        driver.quit()
    return f"Success at last!"


if __name__ == "__main__":
    print(fetch_outstanding_stock())
    with open("last_run_logs.txt", "a") as log_file:
        log_file.write("Success at last!")
