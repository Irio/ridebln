import logging
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from config import settings

logging.basicConfig(level=logging.INFO)


def select_studio(driver):
    logging.info(f'Selecting studio "{settings.studio.name}"...')
    elem = driver.find_element(
        By.XPATH, f"//*[contains(text(), '{settings.studio.name}')]"
    )
    studio_url = elem.get_attribute("href")
    driver.get(studio_url)


def does_need_sign_in(driver):
    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    response = False
    if iframes:
        driver.switch_to.frame(iframes[0])
        response = "Please login to continue" in driver.page_source
        driver.switch_to.default_content()

    if response:
        logging.info("It needs to sign in.")

    return response


def sign_in(driver):
    logging.info("Signing in...")
    driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))

    elem = driver.find_element(By.ID, "username")
    elem.send_keys(settings.user.email)
    elem = driver.find_element(By.ID, "password")
    elem.send_keys(settings.user.password)
    elem.send_keys(Keys.RETURN)

    driver.switch_to.default_content()


def sign_in_if_needed(driver):
    if does_need_sign_in(driver):
        sign_in(driver)


def is_bike_free(driver, bike_number):
    driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))

    elem = driver.find_element(By.ID, f"spotcell{bike_number}")
    result = "Enrolled" not in re.split(r"\s+", elem.get_attribute("class"))

    driver.switch_to.default_content()
    return result


options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(5)

driver.get("https://www.ride-berlin.com/")

select_studio(driver)

driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))

week_day_cells = driver.find_elements(By.CSS_SELECTOR, "#reserve thead td")
week_day_indexes = [
    cell.find_element(By.CSS_SELECTOR, ".thead-dow").text for cell in week_day_cells
]

booking_details = settings.booking_criteria[0]
day_index = week_day_indexes.index(booking_details.weekday)
day_index += 1  # XPath indexing is 1-based

selector = f"//*[@id='reserve']//tbody//td[{day_index}]//div[span[contains(text(), '{booking_details.instructor}')] and span[contains(text(), '{booking_details.time}')]]//a"
elems = driver.find_elements(By.XPATH, selector)
if len(elems) == 1:
    logging.info(f"Found ride for {booking_details}.")

driver.get(elems[0].get_attribute("href"))
sign_in_if_needed(driver)

driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))


def is_spot_free(spot_elem):
    result = spot_elem.tag_name == "a"
    logging.info(f"Spot {spot} is {'free' if result else 'taken'}.")
    return result


def did_it_book(driver):
    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    response = False
    if iframes:
        driver.switch_to.frame(iframes[0])
        response = (
            "You have been successfully enrolled in the class highlighted below"
            in driver.page_source
        )
        driver.switch_to.default_content()

    return response


for spot in settings.studio.favorite_spots:
    spot_elem = driver.find_element(By.ID, f"spotcell{spot}")
    if is_spot_free(spot_elem):
        logging.info(f"Booking spot #{spot}...")
        spot_elem.click()
        sign_in_if_needed(driver)

        elem = driver.find_element(By.XPATH, "//a[contains(text(), 'Use USC')]")
        elem.click()

        if did_it_book(driver):
            logging.info(f"Booked.")

        break
