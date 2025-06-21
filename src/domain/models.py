from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class BookingStatus(Enum):
    PENDING = "pending"
    BOOKED = "booked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StudioLocation(Enum):
    CHARLOTTENBURG = "CHARLOTTENBURG"
    MITTE = "MITTE"
    PRENZLAUER_BERG = "PRENZLAUER BERG"


class CreditType(Enum):
    USC = "usc"  # Urban Sports Club
    PURCHASED = "purchased"
    GIFT = "gift"
    PACKAGE = "package"


@dataclass
class User:
    email: str
    password: str


@dataclass
class BookingCriteria:
    weekday: str
    instructor: str
    time: str
    studio: StudioLocation
    preferred_spots: List[int] = field(default_factory=list)
    
    def __str__(self):
        return f"{self.weekday} {self.time} with {self.instructor} at {self.studio.value}"


@dataclass
class RideClass:
    url: str
    weekday: str
    instructor: str
    time: str
    studio: StudioLocation
    available_spots: List[int] = field(default_factory=list)


@dataclass
class Booking:
    id: Optional[str]
    criteria: BookingCriteria
    ride_class: Optional[RideClass]
    spot_number: Optional[int]
    status: BookingStatus
    created_at: datetime
    booked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = f"{self.created_at.isoformat()}_{hash(str(self.criteria))}"


@dataclass
class CreditPackage:
    type: CreditType
    name: str
    remaining_credits: int
    last_updated: datetime
    
    @property
    def is_empty(self) -> bool:
        return self.remaining_credits <= 0


@dataclass
class CreditBalance:
    packages: Dict[str, CreditPackage] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def total_remaining_credits(self) -> int:
        return sum(pkg.remaining_credits for pkg in self.packages.values())
    
    @property
    def needs_refill(self) -> bool:
        return self.total_remaining_credits <= 2
        
    def add_package(self, package: CreditPackage):
        self.packages[package.name] = package
        self.last_updated = datetime.now()
        
    def use_credit(self, preferred_type: CreditType = None) -> bool:
        # Try to use preferred type first, then any available
        available_packages = [pkg for pkg in self.packages.values() if not pkg.is_empty]
        
        if not available_packages:
            return False
            
        if preferred_type:
            preferred_packages = [pkg for pkg in available_packages if pkg.type == preferred_type]
            if preferred_packages:
                preferred_packages[0].remaining_credits -= 1
                self.last_updated = datetime.now()
                return True
                
        # Use first available package
        available_packages[0].remaining_credits -= 1
        self.last_updated = datetime.now()
        return True 
