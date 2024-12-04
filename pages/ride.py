import logging

from selenium.webdriver.common.by import By


def is_spot_free(spot_elem, spot):
    result = spot_elem.tag_name == "a"
    logging.info(f"Spot {spot} is {'free' if result else 'taken'}.")
    return result
