import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import settings
from pages import RideBlnPage, StudioPage, did_it_book, is_spot_free

logging.basicConfig(level=logging.INFO)


options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Connect to the remote Selenium instance (seleniarm/standalone-chromium)
driver = webdriver.Remote(
    command_executor="http://chrome:4444/wd/hub",  # Replace 'chrome' with the name of the Chrome service in docker-compose
    options=options
)
# driver = webdriver.Chrome(options=options)
# driver.implicitly_wait(5)


driver.get("https://www.ride-berlin.com/")
site = RideBlnPage(driver)
site.select_studio(settings.studio.name)

site = StudioPage(driver)
ride_url = site.ride_url(settings.booking_criteria[0])
if not ride_url:
    exit()
driver.get(ride_url)
site.sign_in_if_needed(settings.user)

driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
has_booked_spot = False
for spot in settings.studio.favorite_spots:
    spot_elem = driver.find_element(By.ID, f"spotcell{spot}")
    if is_spot_free(spot_elem, spot):
        logging.info(f"Booking spot #{spot}...")
        spot_elem.click()
        site.sign_in_if_needed(settings.user)

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
