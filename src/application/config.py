import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import tomllib

from src.domain.models import BookingCriteria, StudioLocation


@dataclass
class AppConfig:
    # User credentials
    user_email: str
    user_password: str

    # System configuration
    browser_url: str
    data_dir: str

    # Booking preferences
    booking_criteria: List[BookingCriteria]

    # Automation settings
    auto_purchase_credits: bool = False
    credit_threshold: int = 2
    monthly_credit_amount: int = 20

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/ridebln.log"

    @classmethod
    def from_file(cls, config_path: str) -> "AppConfig":
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Parse user section
        user_section = data.get("user", {})
        user_email = user_section.get("email")
        user_password = user_section.get("password")

        if not user_email or not user_password:
            raise ValueError("User email and password must be provided in config")

        # Parse system section
        system_section = data.get("system", {})
        browser_url = os.getenv(
            "DYNACONF_BROWSER_URL",
            system_section.get("browser_url", "http://localhost:4444"),
        )
        data_dir = system_section.get("data_dir", "data")

        # Parse automation section
        automation_section = data.get("automation", {})
        auto_purchase_credits = automation_section.get("auto_purchase_credits", False)
        credit_threshold = automation_section.get("credit_threshold", 2)
        monthly_credit_amount = automation_section.get("monthly_credit_amount", 20)

        # Parse logging section
        logging_section = data.get("logging", {})
        log_level = logging_section.get("level", "INFO")
        log_file = logging_section.get("file", "logs/ridebln.log")

        # Parse booking criteria
        booking_criteria = []
        criteria_list = data.get("booking_criteria", [])

        for criteria_data in criteria_list:
            weekday = criteria_data.get("weekday")
            instructor = criteria_data.get("instructor")
            time = criteria_data.get("time")
            studio_name = criteria_data.get("studio", "PRENZLAUER BERG")
            preferred_spots = criteria_data.get("preferred_spots", [1, 2, 3])

            if not all([weekday, instructor, time]):
                raise ValueError(f"Invalid booking criteria: {criteria_data}")

            try:
                studio = StudioLocation(studio_name)
            except ValueError:
                raise ValueError(f"Invalid studio: {studio_name}")

            booking_criteria.append(
                BookingCriteria(
                    weekday=weekday,
                    instructor=instructor,
                    time=time,
                    studio=studio,
                    preferred_spots=preferred_spots,
                )
            )

        if not booking_criteria:
            raise ValueError("At least one booking criteria must be provided")

        return cls(
            user_email=user_email,
            user_password=user_password,
            browser_url=browser_url,
            data_dir=data_dir,
            booking_criteria=booking_criteria,
            auto_purchase_credits=auto_purchase_credits,
            credit_threshold=credit_threshold,
            monthly_credit_amount=monthly_credit_amount,
            log_level=log_level,
            log_file=log_file,
        )

    def setup_logging(self):
        import logging

        # Create logs directory
        log_path = Path(self.log_file)
        log_path.parent.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.log_file), logging.StreamHandler()],
        )
