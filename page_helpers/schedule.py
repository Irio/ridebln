import logging

from selenium.webdriver.common.by import By

from config import settings


def week_day_index(driver, booking_details):
    week_day_cells = driver.find_elements(By.CSS_SELECTOR, "#reserve thead td")
    week_day_indexes = [
        cell.find_element(By.CSS_SELECTOR, ".thead-dow").text for cell in week_day_cells
    ]

    day_index = week_day_indexes.index(booking_details.weekday)
    day_index += 1  # XPath indexing is 1-based
    return day_index


def find_ride(driver):
    booking_details = settings.booking_criteria[0]
    day_index = week_day_index(driver, booking_details)
    selector = f"//*[@id='reserve']//tbody//td[{day_index}]//div[span[contains(text(), '{booking_details.instructor}')] and span[contains(text(), '{booking_details.time}')]]//a"
    elems = driver.find_elements(By.XPATH, selector)
    if len(elems) == 1:
        logging.info(f"Found ride for {booking_details}.")

    return elems[0]
