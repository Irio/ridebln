import logging
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import settings
from pages import RideBlnPage, StudioPage, did_it_book, is_spot_free

logging.basicConfig(level=logging.INFO)

browser_options = Options()
browser_options.add_argument("--headless")
browser_options.add_argument("--no-sandbox")
browser_options.add_argument("--remote-allow-origins=*")
browser_options.add_argument("--disable-dev-shm-usage")
browser_options.add_argument("--disable-gpu")
browser_options.add_argument("--window-size=1920,1080")
browser_options.add_argument("--disable-extensions")
browser_options.add_argument("--disable-software-rasterizer")

if __name__ == "__main__":
    with webdriver.Remote(settings.browser_url, options=browser_options) as driver:
        driver.get("https://www.ride-berlin.com/")
        site = RideBlnPage(driver)
        site.select_studio(settings.studio.name)

        site = StudioPage(driver)
        ride_url = site.ride_url(settings.booking_criteria[0])
        if not ride_url:
            sys.exit()
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

                elem = driver.find_element(
                    By.XPATH, "//a[contains(text(), 'Use USC')]")
                elem.click()

                has_booked_spot = did_it_book(driver)
                if has_booked_spot:
                    logging.info("Booked.")

                break

        if not has_booked_spot:
            logging.info(
                f"None of the favorite spots ({settings.studio.favorite_spots}) are available."
            )
