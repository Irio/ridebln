import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.domain.models import (
    Booking,
    BookingStatus,
    CreditBalance,
    CreditPackage,
    CreditType,
)


class FileStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.bookings_file = self.data_dir / "bookings.json"
        self.credits_file = self.data_dir / "credits.json"

    def _load_json(self, file_path: Path) -> dict:
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_json(self, file_path: Path, data: dict):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def save_booking(self, booking: Booking) -> None:
        bookings_data = self._load_json(self.bookings_file)

        bookings_data[booking.id] = {
            "id": booking.id,
            "criteria": {
                "weekday": booking.criteria.weekday,
                "instructor": booking.criteria.instructor,
                "time": booking.criteria.time,
                "studio": booking.criteria.studio.value,
                "preferred_spots": booking.criteria.preferred_spots,
            },
            "ride_class": (
                {
                    "url": booking.ride_class.url,
                    "weekday": booking.ride_class.weekday,
                    "instructor": booking.ride_class.instructor,
                    "time": booking.ride_class.time,
                    "studio": booking.ride_class.studio.value,
                    "available_spots": booking.ride_class.available_spots,
                }
                if booking.ride_class
                else None
            ),
            "spot_number": booking.spot_number,
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat(),
            "booked_at": booking.booked_at.isoformat() if booking.booked_at else None,
            "error_message": booking.error_message,
        }

        self._save_json(self.bookings_file, bookings_data)

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        bookings_data = self._load_json(self.bookings_file)

        if booking_id not in bookings_data:
            return None

        return self._dict_to_booking(bookings_data[booking_id])

    def get_all_bookings(self) -> List[Booking]:
        bookings_data = self._load_json(self.bookings_file)
        return [self._dict_to_booking(data) for data in bookings_data.values()]

    def get_bookings_by_status(self, status: BookingStatus) -> List[Booking]:
        all_bookings = self.get_all_bookings()
        return [b for b in all_bookings if b.status == status]

    def has_existing_booking_for_criteria(self, criteria) -> bool:
        all_bookings = self.get_all_bookings()

        for booking in all_bookings:
            if (
                booking.criteria.weekday == criteria.weekday
                and booking.criteria.instructor == criteria.instructor
                and booking.criteria.time == criteria.time
                and booking.criteria.studio == criteria.studio
                and booking.status in [BookingStatus.PENDING, BookingStatus.BOOKED]
            ):
                return True

        return False

    def get_recent_bookings(self, limit: int = 50) -> List[Booking]:
        all_bookings = self.get_all_bookings()
        # Sort by creation date, most recent first
        sorted_bookings = sorted(all_bookings, key=lambda b: b.created_at, reverse=True)
        return sorted_bookings[:limit]

    def _dict_to_booking(self, data: dict) -> Booking:
        from src.domain.models import BookingCriteria, RideClass, StudioLocation

        criteria_data = data["criteria"]
        criteria = BookingCriteria(
            weekday=criteria_data["weekday"],
            instructor=criteria_data["instructor"],
            time=criteria_data["time"],
            studio=StudioLocation(criteria_data["studio"]),
            preferred_spots=criteria_data.get("preferred_spots", []),
        )

        ride_class = None
        if data["ride_class"]:
            ride_data = data["ride_class"]
            ride_class = RideClass(
                url=ride_data["url"],
                weekday=ride_data["weekday"],
                instructor=ride_data["instructor"],
                time=ride_data["time"],
                studio=StudioLocation(ride_data["studio"]),
                available_spots=ride_data.get("available_spots", []),
            )

        return Booking(
            id=data["id"],
            criteria=criteria,
            ride_class=ride_class,
            spot_number=data["spot_number"],
            status=BookingStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            booked_at=(
                datetime.fromisoformat(data["booked_at"]) if data["booked_at"] else None
            ),
            error_message=data["error_message"],
        )

    def save_credit_balance(self, balance: CreditBalance) -> None:
        credits_data = {
            "packages": {},
            "last_updated": balance.last_updated.isoformat(),
        }

        for name, package in balance.packages.items():
            credits_data["packages"][name] = {
                "type": package.type.value,
                "name": package.name,
                "remaining_credits": package.remaining_credits,
                "last_updated": package.last_updated.isoformat(),
            }

        self._save_json(self.credits_file, credits_data)

    def get_credit_balance(self) -> Optional[CreditBalance]:
        credits_data = self._load_json(self.credits_file)

        if not credits_data:
            return None

        balance = CreditBalance(
            last_updated=datetime.fromisoformat(credits_data["last_updated"])
        )

        for name, pkg_data in credits_data["packages"].items():
            package = CreditPackage(
                type=CreditType(pkg_data["type"]),
                name=pkg_data["name"],
                remaining_credits=pkg_data["remaining_credits"],
                last_updated=datetime.fromisoformat(pkg_data["last_updated"]),
            )
            balance.add_package(package)

        return balance
