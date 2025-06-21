import logging
from datetime import datetime, timedelta
from typing import List

from src.domain.models import BookingCriteria, User
from src.domain.services import BookingService, CreditService
from src.infrastructure.storage import FileStorage
from src.infrastructure.web_scraper import RideBerlinScraper

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(
        self,
        browser_url: str,
        user: User,
        booking_criteria: List[BookingCriteria],
        auto_purchase_credits: bool = False,
        data_dir: str = "data"
    ):
        self.browser_url = browser_url
        self.user = user
        self.booking_criteria = booking_criteria
        self.auto_purchase_credits = auto_purchase_credits
        self.storage = FileStorage(data_dir)
        
    def run_hourly_check(self):
        logger.info("Starting hourly booking check...")
        
        with RideBerlinScraper(self.browser_url) as scraper:
            booking_service = BookingService(scraper, self.storage, self.user)
            credit_service = CreditService(scraper, self.storage, self.user)
            
            # Check credit balance first
            if credit_service.needs_credit_refill():
                balance = credit_service.get_credit_balance()
                total_credits = balance.total_remaining_credits if balance else 0
                logger.warning(f"⚠️ Low credits: {total_credits} remaining")
                
                if not self.auto_purchase_credits:
                    logger.warning("Auto-purchase disabled, skipping booking attempts")
                    return
                    
            # Try to book matching classes
            bookings_made = 0
            for criteria in self.booking_criteria:
                try:
                    booking = booking_service.search_and_book(criteria)
                    if booking:
                        if booking.status.value == "booked":
                            bookings_made += 1
                            logger.info(f"✅ Booked: {criteria} - Spot {booking.spot_number}")
                        else:
                            logger.warning(f"❌ Failed: {criteria} - {booking.error_message}")
                except Exception as e:
                    logger.error(f"Error processing {criteria}: {e}")
                    
            logger.info(f"Hourly check completed - {bookings_made} new bookings made")
        
    def run_monthly_credit_load(self):
        logger.info("Starting monthly credit load...")
        
        # For now, just log that this needs manual implementation
        # In a real scenario, you'd navigate to the credit purchase page
        logger.info("Monthly credit load requires manual implementation")
        logger.info("Navigate to https://www.ride-berlin.com/ to purchase credits")
        
    def run_status_check(self):
        logger.info("=== Booking System Status ===")
        
        # Show booking status
        active_bookings = self.storage.get_bookings_by_status("booked")
        pending_bookings = self.storage.get_bookings_by_status("pending")
        
        logger.info(f"Active bookings: {len(active_bookings)}")
        logger.info(f"Pending bookings: {len(pending_bookings)}")
        
        # Show credit balance
        credit_service = CreditService(None, self.storage, self.user)
        balance = credit_service.get_credit_balance()
        
        if balance:
            logger.info(f"Credit summary:")
            for line in credit_service.get_credit_summary().split('\n'):
                logger.info(f"  {line}")
        else:
            logger.warning("No credit balance information available")
            
        # Show recent bookings
        recent = self.storage.get_recent_bookings(5)
        if recent:
            logger.info("Recent bookings:")
            for booking in recent:
                status_emoji = {
                    'booked': '✅',
                    'failed': '❌',
                    'pending': '⏳',
                    'cancelled': '🚫'
                }.get(booking.status.value, '❓')
                
                spot_info = f" (spot {booking.spot_number})" if booking.spot_number else ""
                logger.info(f"  {status_emoji} {booking.criteria}{spot_info}")
                
        # Show configured criteria
        logger.info(f"Configured criteria ({len(self.booking_criteria)}):")
        for criteria in self.booking_criteria:
            logger.info(f"  - {criteria}")
            
    def cleanup_old_bookings(self, days_old: int = 30):
        logger.info(f"Cleaning up bookings older than {days_old} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        all_bookings = self.storage.get_all_bookings()
        
        old_bookings = [
            booking for booking in all_bookings 
            if booking.created_at < cutoff_date
        ]
        
        logger.info(f"Found {len(old_bookings)} old bookings")
        
        if old_bookings:
            logger.info("Old bookings cleanup would need implementation")
            logger.info("Consider archiving or deleting old booking records")
            
    def add_booking_criteria(self, criteria: BookingCriteria):
        """Add new booking criteria to the active list"""
        self.booking_criteria.append(criteria)
        logger.info(f"Added booking criteria: {criteria}")
        
    def remove_booking_criteria(self, criteria: BookingCriteria):
        """Remove booking criteria from the active list"""
        if criteria in self.booking_criteria:
            self.booking_criteria.remove(criteria)
            logger.info(f"Removed booking criteria: {criteria}")
        else:
            logger.warning(f"Criteria not found: {criteria}")
