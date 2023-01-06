import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

path = r"C:\Users\stapi\chromedriver"


def get_cik():
    data = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    cik_list = list(data['CIK'])
    securities_list = list(data["Security"])
    return dict(zip(securities_list, cik_list))


if __name__ == "__main__":
    company_cik_dict = get_cik()

    with open("stocks_and_cik.json", encoding='utf-8', mode='w') as output_file:
        json.dump(company_cik_dict, output_file)

    data_urls = []
    run_logs = []

    for i, key in enumerate(company_cik_dict):
        service = Service(path)
        driver = webdriver.Chrome(service=service)

        url = f"https://www.sec.gov/edgar/browse/?CIK={company_cik_dict[key]}&owner=exclude"

        driver.get(url)
        time.sleep(3)
        section = driver.find_element(By.XPATH, '//*[@id="filingsStart"]/div[2]/div[3]/h5/a')

        ActionChains(driver=driver) \
            .move_to_element(section) \
            .pause(1) \
            .click() \
            .pause(1) \
            .perform()

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
        data_urls.append(new_url)
        driver.quit()
        time.sleep(3)
        run_logs.append(f"{key}: {company_cik_dict[key]} appended, successfully.")
        if i == 1:
            break

    run_logs.append(f"The length of the url list is: {len(data_urls)}")
    time.sleep(1)
    outstanding_shares_text_data = []

    for link in data_urls:
        service = Service(path)
        driver = webdriver.Chrome(service=service)
        form_url = link  # data_urls[0]
        driver.get(form_url)

        filter_data = driver.find_element(By.XPATH, '//*[@id="nav-filter-data"]/span[2]')

        ActionChains(driver=driver) \
            .move_to_element(filter_data) \
            .pause(2) \
            .click() \
            .pause(1) \
            .perform()

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

        outstanding_shares_text_data.append(f"('{link}','{amounts_data.text}')")
        run_logs.append(f"({link}) - data was captured successfully.")
        driver.quit()

    with open("outstanding_shares_text.txt", "w") as scraped_output:
        content = "\n".join(outstanding_shares_text_data)
        scraped_output.writelines(content)

    with open("last_run_logs.txt", "w") as log_file:
        file_content = "\n".join(run_logs)
        log_file.writelines(file_content)

    print(f"Success!")
