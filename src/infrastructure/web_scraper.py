import logging
import time
from contextlib import contextmanager
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.domain.models import BookingCriteria, RideClass, StudioLocation, User

logger = logging.getLogger(__name__)


class RideBerlinScraper:
    def __init__(self, browser_url: str, user: User = None, max_retries: int = 3):
        self.browser_url = browser_url
        self.user = user
        self.max_retries = max_retries
        self.driver = None

    def __enter__(self):
        options = self._get_browser_options()
        self.driver = webdriver.Remote(self.browser_url, options=options)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def _get_browser_options(self) -> Options:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        return options

    @contextmanager
    def _iframe_context(self):
        iframe = self.driver.find_element(By.TAG_NAME, "iframe")
        self.driver.switch_to.frame(iframe)
        try:
            yield
        finally:
            self.driver.switch_to.default_content()

    def _retry_operation(self, operation, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (WebDriverException, TimeoutException) as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2**attempt)

    def navigate_to_home(self):
        self.driver.get("https://www.ride-berlin.com/")

    def select_studio(self, studio: StudioLocation):
        logger.info(f'Selecting studio "{studio.value}"...')
        elem = self.driver.find_element(
            By.XPATH, f"//*[contains(text(), '{studio.value}')]"
        )
        studio_url = elem.get_attribute("href")
        self.driver.get(studio_url)

    def must_sign_in(self) -> bool:
        try:
            with self._iframe_context():
                return "Please login to continue" in self.driver.page_source
        except NoSuchElementException:
            return False

    def sign_in(self, user: User):
        def _do_sign_in():
            logger.info("Signing in...")
            with self._iframe_context():
                email_field = self.driver.find_element(By.ID, "username")
                email_field.clear()
                email_field.send_keys(user.email)

                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(user.password)
                password_field.send_keys(Keys.RETURN)

            time.sleep(2)

        # Handle the flaky sign-in by retrying up to 3 times
        for attempt in range(3):
            _do_sign_in()
            if not self.must_sign_in():
                logger.info("Sign in successful")
                return
            logger.warning(f"Sign in attempt {attempt + 1} failed, retrying...")

        raise Exception("Failed to sign in after 3 attempts")

    def find_matching_rides(self, criteria: BookingCriteria) -> List[RideClass]:
        with self._iframe_context():
            rides = []

            # Find column for the specified weekday
            day_index = self._get_weekday_column_index(criteria.weekday)
            if day_index == -1:
                return rides

            # XPath is 1-based
            xpath_day_index = day_index + 1
            selector = f"//*[@id='reserve']//tbody//td[{xpath_day_index}]//div[contains(@class, 'scheduleBlock')][.//span[contains(@class, 'scheduleInstruc') and contains(text(), '{criteria.instructor}')]][.//span[contains(@class, 'scheduleTime') and contains(text(), '{criteria.time}')]]//a"

            elements = self.driver.find_elements(By.XPATH, selector)

            for elem in elements:
                url = elem.get_attribute("href")
                rides.append(
                    RideClass(
                        url=url,
                        weekday=criteria.weekday,
                        instructor=criteria.instructor,
                        time=criteria.time,
                        studio=criteria.studio,
                    )
                )

            return rides

    def _get_weekday_column_index(self, weekday: str) -> int:
        cells = self.driver.find_elements(By.CSS_SELECTOR, "#reserve thead td")
        weekdays = [
            cell.find_element(By.CSS_SELECTOR, ".thead-dow").text.lower()
            for cell in cells
        ]

        try:
            return weekdays.index(weekday.lower())
        except ValueError:
            return -1

    def get_available_spots(self, ride_url: str) -> List[int]:
        self.driver.get(ride_url)
        self._ensure_signed_in()

        available_spots = []

        with self._iframe_context():
            for spot_num in range(1, 60):  # Assuming max 60 spots
                try:
                    spot_elem = self.driver.find_element(By.ID, f"spotcell{spot_num}")
                    if spot_elem.tag_name == "a":  # Free spots are links
                        available_spots.append(spot_num)
                except NoSuchElementException:
                    continue

        logger.info(f"Found {len(available_spots)} available spots: {available_spots}")
        return available_spots

    def book_spot(self, ride_url: str, spot_number: int, use_usc: bool = True) -> bool:
        self.driver.get(ride_url)
        self._ensure_signed_in()

        with self._iframe_context():
            try:
                spot_elem = self.driver.find_element(By.ID, f"spotcell{spot_number}")
                if spot_elem.tag_name != "a":
                    logger.info(f"Spot {spot_number} is not available")
                    return False

                spot_elem.click()
                time.sleep(1)  # Allow page to load after spot selection
                self._ensure_signed_in()

                if use_usc:
                    # Try to click USC button, but don't fail if it's auto-selected
                    try:
                        usc_elem = self.driver.find_element(
                            By.XPATH, "//a[contains(text(), 'Use USC')]"
                        )
                        usc_elem.click()
                        logger.info("Clicked USC credit option")
                    except NoSuchElementException:
                        logger.info("USC option not found - likely auto-selected")

                # Check for success by looking for alert element inside iframe
                try:
                    alert_elem = self.driver.find_element(By.CSS_SELECTOR, ".alert")
                    alert_text = alert_elem.text.strip()
                    logger.info(f"Alert element found: '{alert_text}'")

                    # Check if alert indicates success (contains positive keywords)
                    success_keywords = [
                        "success",
                        "enrolled",
                        "booked",
                        "confirmed",
                        "erfolgreich",
                        "bestätigt",
                    ]
                    alert_lower = alert_text.lower()

                    for keyword in success_keywords:
                        if keyword in alert_lower:
                            logger.info(
                                f"Booking success detected in alert: '{alert_text}'"
                            )
                            return True

                    # If alert exists but doesn't contain success keywords, it might be an error
                    logger.warning(
                        f"Alert found but doesn't indicate success: '{alert_text}'"
                    )
                    return False

                except NoSuchElementException:
                    logger.debug("No .alert element found")
                    # If no alert element, assume success since booking process completed
                    logger.info("No alert element found - assuming booking succeeded")
                    return True

            except NoSuchElementException as e:
                logger.error(f"Failed to book spot {spot_number}: {e}")
                return False

    def _ensure_signed_in(self):
        if self.must_sign_in():
            if not self.user:
                raise Exception("User needs to sign in but no credentials provided")
            self.sign_in(self.user)

    def get_credit_balance(self) -> Optional[int]:
        pass

    def purchase_credits(self, amount: int) -> bool:
        pass
