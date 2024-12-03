import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .my_rides import *
from .ride import *
from .schedule import *


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
