import logging
from datetime import datetime
from typing import List, Optional

from src.domain.models import (
    Booking,
    BookingCriteria,
    BookingStatus,
    CreditBalance,
    CreditPackage,
    CreditType,
    RideClass,
    User,
)
from src.infrastructure.storage import FileStorage
from src.infrastructure.web_scraper import RideBerlinScraper

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, scraper: RideBerlinScraper, storage: FileStorage, user: User):
        self.scraper = scraper
        self.storage = storage
        self.user = user

    def search_and_book(self, criteria: BookingCriteria) -> Optional[Booking]:
        if self.storage.has_existing_booking_for_criteria(criteria):
            logger.info(f"Already have a booking for {criteria}")
            return None

        booking = Booking(
            id=None,
            criteria=criteria,
            ride_class=None,
            spot_number=None,
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
        )

        try:
            self.storage.save_booking(booking)

            self.scraper.navigate_to_home()
            self.scraper.select_studio(criteria.studio)

            # Sign-in is now handled automatically in _ensure_signed_in

            matching_rides = self.scraper.find_matching_rides(criteria)

            if not matching_rides:
                booking.status = BookingStatus.FAILED
                booking.error_message = "No matching rides found"
                self.storage.save_booking(booking)
                logger.warning(f"No matching rides found for {criteria}")
                return booking

            for ride in matching_rides:
                available_spots = self.scraper.get_available_spots(ride.url)
                ride.available_spots = available_spots

                preferred_available = [
                    spot for spot in criteria.preferred_spots if spot in available_spots
                ]

                logger.info(f"Available spots: {available_spots}")
                logger.info(f"Preferred spots: {criteria.preferred_spots}")
                logger.info(f"Preferred available spots: {preferred_available}")

                if preferred_available:
                    spot_to_book = preferred_available[0]
                    logger.info(f"Attempting to book spot {spot_to_book}")
                    booking_success = self.scraper.book_spot(ride.url, spot_to_book)
                    logger.info(f"Booking attempt result: {booking_success}")

                    if booking_success:
                        booking.ride_class = ride
                        booking.spot_number = spot_to_book
                        booking.status = BookingStatus.BOOKED
                        booking.booked_at = datetime.now()
                        self.storage.save_booking(booking)

                        logger.info(
                            f"✅ Successfully booked spot {spot_to_book} for {criteria}"
                        )
                        return booking
                    else:
                        logger.warning(
                            f"Failed to book spot {spot_to_book}, trying next available spot"
                        )

            booking.status = BookingStatus.FAILED
            booking.error_message = "No preferred spots available"
            self.storage.save_booking(booking)
            logger.warning(f"No preferred spots available for {criteria}")
            return booking

        except Exception as e:
            logger.error(f"Failed to book {criteria}: {e}")
            booking.status = BookingStatus.FAILED
            booking.error_message = str(e)
            self.storage.save_booking(booking)
            return booking

    def get_booking_history(self, limit: int = 50) -> List[Booking]:
        return self.storage.get_recent_bookings(limit)

    def get_active_bookings(self) -> List[Booking]:
        pending = self.storage.get_bookings_by_status(BookingStatus.PENDING)
        booked = self.storage.get_bookings_by_status(BookingStatus.BOOKED)
        return pending + booked

    def cancel_booking(self, booking_id: str) -> bool:
        booking = self.storage.get_booking(booking_id)
        if not booking:
            return False

        booking.status = BookingStatus.CANCELLED
        self.storage.save_booking(booking)
        return True


class CreditService:
    def __init__(self, scraper: RideBerlinScraper, storage: FileStorage, user: User):
        self.scraper = scraper
        self.storage = storage
        self.user = user

    def get_credit_balance(self) -> Optional[CreditBalance]:
        # Try to get from storage first
        balance = self.storage.get_credit_balance()

        # If no balance or old data, try to refresh from website
        if not balance or (datetime.now() - balance.last_updated).days > 1:
            try:
                # This would need implementation in the scraper
                # For now, return stored balance or create empty one
                if not balance:
                    balance = CreditBalance()

                logger.info(
                    "Credit balance check - implement scraper.get_credit_balance() for live data"
                )

            except Exception as e:
                logger.error(f"Failed to refresh credit balance: {e}")

        return balance

    def update_credit_package(
        self, package_name: str, credits: int, credit_type: CreditType
    ):
        balance = self.get_credit_balance() or CreditBalance()

        package = CreditPackage(
            type=credit_type,
            name=package_name,
            remaining_credits=credits,
            last_updated=datetime.now(),
        )

        balance.add_package(package)
        self.storage.save_credit_balance(balance)

        logger.info(f"Updated {package_name}: {credits} {credit_type.value} credits")

    def use_credit(self, preferred_type: CreditType = None) -> bool:
        balance = self.get_credit_balance()
        if not balance:
            logger.warning("No credit balance available")
            return False

        if balance.use_credit(preferred_type):
            self.storage.save_credit_balance(balance)
            logger.info(f"Used 1 credit, {balance.total_remaining_credits} remaining")
            return True
        else:
            logger.warning("No credits available to use")
            return False

    def needs_credit_refill(self) -> bool:
        balance = self.get_credit_balance()
        return balance is None or balance.needs_refill

    def get_credit_summary(self) -> str:
        balance = self.get_credit_balance()
        if not balance:
            return "No credit information available"

        lines = [f"Total credits: {balance.total_remaining_credits}"]
        for name, package in balance.packages.items():
            lines.append(
                f"  - {name}: {package.remaining_credits} ({package.type.value})"
            )

        return "\n".join(lines)
