#!/usr/bin/env python3

import argparse
import logging
import sys
from typing import List

from src.application.config import AppConfig
from src.application.scheduler import SchedulerService
from src.domain.models import BookingCriteria, CreditType, StudioLocation, User
from src.domain.services import BookingService, CreditService
from src.infrastructure.storage import FileStorage
from src.infrastructure.web_scraper import RideBerlinScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_arguments():
    parser = argparse.ArgumentParser(description="RideBerlin Booking System")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Book command
    book_parser = subparsers.add_parser("book", help="Book a single ride")
    book_parser.add_argument(
        "--weekday", type=str, required=True, help="Weekday (e.g., mo, tu, we)"
    )
    book_parser.add_argument(
        "--instructor", type=str, required=True, help="Instructor name"
    )
    book_parser.add_argument(
        "--time", type=str, required=True, help="Time (e.g., 18:00)"
    )
    book_parser.add_argument(
        "--studio",
        type=str,
        required=True,
        choices=["CHARLOTTENBURG", "MITTE", "PRENZLAUER_BERG"],
    )
    book_parser.add_argument(
        "--spots", type=int, nargs="+", default=[1, 2, 3], help="Preferred spot numbers"
    )

    # Schedule commands
    subparsers.add_parser("hourly", help="Run hourly booking check")
    subparsers.add_parser("monthly", help="Load monthly credits")
    subparsers.add_parser("status", help="Show current status")

    # Credit management commands
    credits_parser = subparsers.add_parser("credits", help="Manage credit packages")
    credits_parser.add_argument(
        "--add", action="store_true", help="Add a credit package"
    )
    credits_parser.add_argument("--name", type=str, help="Package name")
    credits_parser.add_argument("--amount", type=int, help="Number of credits")
    credits_parser.add_argument(
        "--type",
        type=str,
        choices=["usc", "purchased", "gift", "package"],
        help="Credit type",
    )

    # Management commands
    subparsers.add_parser("history", help="Show booking history")
    subparsers.add_parser("cleanup", help="Clean up old bookings")

    parser.add_argument(
        "--config", type=str, default="settings.toml", help="Config file path"
    )
    parser.add_argument(
        "--browser-url", type=str, help="Selenium browser URL (overrides config)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )

    return parser


def create_services(config: AppConfig, browser_url: str = None):
    actual_browser_url = browser_url or config.browser_url

    storage = FileStorage(config.data_dir)
    user = User(email=config.user_email, password=config.user_password)

    scraper = RideBerlinScraper(actual_browser_url)

    return scraper, storage, user


def handle_book_command(args, config: AppConfig):
    # Convert CLI studio format to enum format
    studio_mapping = {
        "CHARLOTTENBURG": StudioLocation.CHARLOTTENBURG,
        "MITTE": StudioLocation.MITTE,
        "PRENZLAUER_BERG": StudioLocation.PRENZLAUER_BERG,
    }

    criteria = BookingCriteria(
        weekday=args.weekday,
        instructor=args.instructor,
        time=args.time,
        studio=studio_mapping[args.studio],
        preferred_spots=args.spots,
    )

    logger.info(f"Booking request: {criteria}")

    if args.dry_run:
        logger.info("DRY RUN: Would attempt to book this ride")
        return

    scraper, storage, user = create_services(config, args.browser_url)

    try:
        with scraper:
            booking_service = BookingService(scraper, storage, user)
            booking = booking_service.search_and_book(criteria)

            if booking:
                if booking.status.value == "booked":
                    logger.info(f"✅ Successfully booked spot {booking.spot_number}")
                else:
                    logger.error(f"❌ Booking failed: {booking.error_message}")
            else:
                logger.info("ℹ️ No booking needed (already exists)")

    except Exception as e:
        logger.error(f"Failed to book: {e}")
        sys.exit(1)


def handle_scheduler_command(command: str, config: AppConfig, args):
    scheduler = SchedulerService(
        browser_url=args.browser_url or config.browser_url,
        user=User(email=config.user_email, password=config.user_password),
        booking_criteria=config.booking_criteria,
        auto_purchase_credits=config.auto_purchase_credits,
        data_dir=config.data_dir,
    )

    if args.dry_run:
        logger.info(f"DRY RUN: Would run {command}")
        return

    try:
        if command == "hourly":
            scheduler.run_hourly_check()
        elif command == "monthly":
            scheduler.run_monthly_credit_load()
        elif command == "status":
            scheduler.run_status_check()
        elif command == "cleanup":
            scheduler.cleanup_old_bookings()

    except Exception as e:
        logger.error(f"Scheduler command failed: {e}")
        sys.exit(1)


def handle_credits_command(args, config: AppConfig):
    _, storage, user = create_services(config, args.browser_url)
    credit_service = CreditService(None, storage, user)

    if args.add:
        if not all([args.name, args.amount, args.type]):
            logger.error("--add requires --name, --amount, and --type")
            sys.exit(1)

        credit_type = CreditType(args.type)
        credit_service.update_credit_package(args.name, args.amount, credit_type)
        logger.info(f"Added {args.amount} {args.type} credits to package '{args.name}'")
    else:
        # Show credit summary
        summary = credit_service.get_credit_summary()
        logger.info("Credit Summary:")
        for line in summary.split("\n"):
            logger.info(f"  {line}")


def handle_history_command(config: AppConfig):
    storage = FileStorage(config.data_dir)
    bookings = storage.get_recent_bookings(20)

    if not bookings:
        logger.info("No booking history found")
        return

    logger.info("Recent booking history:")
    for booking in bookings:
        status_emoji = {
            "booked": "✅",
            "failed": "❌",
            "pending": "⏳",
            "cancelled": "🚫",
        }.get(booking.status.value, "❓")

        spot_info = f" (spot {booking.spot_number})" if booking.spot_number else ""
        logger.info(
            f"  {status_emoji} {booking.criteria}{spot_info} - {booking.created_at.strftime('%Y-%m-%d %H:%M')}"
        )


def main():
    parser = setup_arguments()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        config = AppConfig.from_file(args.config)
        config.setup_logging()
    except Exception as e:
        logger.error(f"Failed to load config from {args.config}: {e}")
        sys.exit(1)

    # Handle different commands
    if args.command == "book":
        handle_book_command(args, config)
    elif args.command in ["hourly", "monthly", "status", "cleanup"]:
        handle_scheduler_command(args.command, config, args)
    elif args.command == "credits":
        handle_credits_command(args, config)
    elif args.command == "history":
        handle_history_command(config)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
