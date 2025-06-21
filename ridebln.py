#!/usr/bin/env python3
"""
RideBerlin Booking System
Automated booking for ride.berlin.com fitness classes
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.application.cli import main

if __name__ == "__main__":
    main() 
