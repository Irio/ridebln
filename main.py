import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import settings
from page_helpers import did_it_book, is_spot_free, select_studio, sign_in_if_needed
from page_helpers.schedule import find_ride

logging.basicConfig(level=logging.INFO)


options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(5)


driver.get("https://www.ride-berlin.com/")

select_studio(driver)

driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
ride_elem = find_ride(driver)

driver.get(ride_elem.get_attribute("href"))
sign_in_if_needed(driver)

driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
has_booked_spot = False
for spot in settings.studio.favorite_spots:
    spot_elem = driver.find_element(By.ID, f"spotcell{spot}")
    if is_spot_free(spot_elem, spot):
        logging.info(f"Booking spot #{spot}...")
        spot_elem.click()
        sign_in_if_needed(driver)

        elem = driver.find_element(By.XPATH, "//a[contains(text(), 'Use USC')]")
        elem.click()

        has_booked_spot = did_it_book(driver)
        if has_booked_spot:
            logging.info("Booked.")

        break

if not has_booked_spot:
    logging.info(
        f"None of the favorite spots ({settings.studio.favorite_spots}) are available."
    )
