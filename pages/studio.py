import logging

from selenium.webdriver.common.by import By

from pages.main import RideBlnPage


class StudioPage(RideBlnPage):
    def __init__(self, driver):
        super().__init__(driver)

        assert driver.current_url.startswith("https://www.ride-berlin.com/reserve")

    def _column_for_weekday(self, weekday):
        cells = self.driver.find_elements(By.CSS_SELECTOR, "#reserve thead td")
        indexes = [
            cell.find_element(By.CSS_SELECTOR, ".thead-dow").text for cell in cells
        ]

        return indexes.index(weekday)

    def ride_url(self, booking_details):
        self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))

        # XPath indexing is 1-based
        day_index = 1 + self._column_for_weekday(booking_details.weekday)
        selector = f"//*[@id='reserve']//tbody//td[{day_index}]//div[span[contains(text(), '{booking_details.instructor}')] and span[contains(text(), '{booking_details.time}')]]//a"
        print(selector)
        elems = self.driver.find_elements(By.XPATH, selector)

        url = None
        if len(elems) == 0:
            logging.info(f"Can't find rides matching {booking_details}.")
        elif len(elems) == 1:
            logging.info(f"Found ride for {booking_details}.")
            url = elems[0].get_attribute("href")
        else:
            logging.info(f"Found multiple rides for {booking_details}.")

        self.driver.switch_to.default_content()
        return url
