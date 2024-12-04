import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class RideBlnPage:
    def __init__(self, driver):
        assert driver.current_url.startswith("https://www.ride-berlin.com/")
        self.driver = driver

    def select_studio(self, studio_name):
        logging.info(f'Selecting studio "{studio_name}"...')
        elem = self.driver.find_element(
            By.XPATH, f"//*[contains(text(), '{studio_name}')]"
        )
        studio_url = elem.get_attribute("href")
        self.driver.get(studio_url)

    def must_sign_in(self):
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

        response = False
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            response = "Please login to continue" in self.driver.page_source
            self.driver.switch_to.default_content()

        if response:
            logging.info("It needs to sign in.")

        return response

    def sign_in(self, user):
        logging.info("Signing in...")
        self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))

        elem = self.driver.find_element(By.ID, "username")
        elem.send_keys(user.email)
        elem = self.driver.find_element(By.ID, "password")
        elem.send_keys(user.password)
        elem.send_keys(Keys.RETURN)

        self.driver.switch_to.default_content()

    def sign_in_if_needed(self, user):
        if self.must_sign_in():
            self.sign_in(user)
