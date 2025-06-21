# RideBerlin Booking System

An automated booking system for [ride.berlin.com](https://www.ride-berlin.com) fitness studio classes.

## Architecture Overview

This system uses a **layered architecture** for maintainability and extensibility:

- **Domain Layer**: Core business logic (bookings, credits, user management)
- **Infrastructure Layer**: External dependencies (web scraping, file storage)
- **Application Layer**: User interfaces (CLI, scheduler)

```
├── src/
│   ├── domain/          # Business logic
│   │   ├── models.py    # Data models (Booking, Credit, User)
│   │   └── services.py  # Business services
│   ├── infrastructure/  # External dependencies
│   │   ├── web_scraper.py  # Selenium-based scraping
│   │   └── storage.py      # JSON file storage
│   └── application/     # User interfaces
│       ├── cli.py       # Command-line interface
│       ├── scheduler.py # Automation service
│       └── config.py    # Configuration management
├── scripts/             # Deployment scripts
├── data/               # JSON storage files
└── logs/               # Application logs
```

## Features

### Current
- ✅ **Automated Booking**: Book spinning classes based on criteria
- ✅ **Multiple Credit Types**: Support USC, purchased, gift credits
- ✅ **Duplicate Prevention**: Avoid booking the same class twice
- ✅ **Robust Sign-in**: Handle flaky login with retries
- ✅ **iFrame Handling**: Navigate complex page structure
- ✅ **CLI Interface**: Command-line tools for all operations
- ✅ **File-based Storage**: Simple JSON storage for personal use
- ✅ **Scheduling Ready**: Cron scripts for automation

### Planned Extensions
- ⏳ **Hourly Checks**: Automated hourly booking attempts
- ⏳ **Monthly Credit Loading**: Automatic credit purchases
- ⏳ **Credit Purchase**: Buy additional credits when low

## Installation

### Prerequisites
- Python 3.8+
- Selenium WebDriver (Chrome/Firefox)
- Docker (optional, for Selenium Grid)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ridebln
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Selenium Grid** (optional):
   ```bash
   docker-compose up -d
   ```

5. **Configure settings**:
   ```bash
   cp settings.toml.example settings.toml
   # Edit settings.toml with your credentials and preferences
   ```

## Configuration

Edit `settings.toml`:

```toml
[user]
email = "your_email@example.com"
password = "your_secret_password"

[system]
browser_url = "http://localhost:4444"  # Selenium Grid URL
data_dir = "data"  # Directory for JSON storage

[automation]
auto_purchase_credits = false
credit_threshold = 2
monthly_credit_amount = 20

# Define multiple booking criteria
[[booking_criteria]]
weekday = "mo"
instructor = "Juan" 
time = "18:00"
studio = "PRENZLAUER BERG"
preferred_spots = [1, 2, 3, 4, 5]
```

## Usage

### Command Line Interface

**Book a single ride**:
```bash
python3 ridebln.py book --weekday mo --instructor Juan --time 18:00 --studio PRENZLAUER_BERG --spots 1 2 3
```

**Manage credits**:
```bash
# View credit balance
python3 ridebln.py credits

# Add credit package
python3 ridebln.py credits --add --name "USC March" --amount 8 --type usc
python3 ridebln.py credits --add --name "Purchased Pack" --amount 10 --type purchased
```

**Check status**:
```bash
python3 ridebln.py status
```

**View booking history**:
```bash
python3 ridebln.py history
```

**Run scheduled tasks**:
```bash
python3 ridebln.py hourly   # Check for new bookings
python3 ridebln.py monthly  # Load monthly credits
python3 ridebln.py cleanup  # Clean old bookings
```

### Automation (Raspberry Pi)

1. **Install on Raspberry Pi**:
   ```bash
   # Transfer files to Pi
   scp -r ridebln/ pi@raspberrypi.local:~/
   
   # SSH to Pi and setup
   ssh pi@raspberrypi.local
   cd ridebln
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup Selenium** (headless Chrome):
   ```bash
   # Install Chrome
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install google-chrome-stable
   
   # Install ChromeDriver
   sudo apt install chromium-chromedriver
   ```

3. **Setup cron jobs**:
   ```bash
   crontab -e
   
   # Add these lines:
   # Hourly booking check (every hour)
   0 * * * * /home/pi/ridebln/scripts/cron-hourly.sh
   
   # Monthly credit load (1st of each month)
   0 0 1 * * /home/pi/ridebln/scripts/cron-monthly.sh
   ```

## Data Storage

The system uses simple JSON files in the `data/` directory:

- `data/bookings.json`: All booking records
- `data/credits.json`: Credit package information

### Credit Management

The system supports multiple credit packages:

```json
{
  "packages": {
    "USC March": {
      "type": "usc",
      "name": "USC March", 
      "remaining_credits": 8,
      "last_updated": "2024-03-01T10:00:00"
    },
    "Purchased Pack": {
      "type": "purchased",
      "name": "Purchased Pack",
      "remaining_credits": 12,
      "last_updated": "2024-03-01T10:00:00"
    }
  }
}
```

## Web Scraping Details

The system handles several challenges of the ride-berlin.com website:

### iFrame Navigation
Most content is inside iframes. The scraper automatically:
- Detects iframes on pages
- Switches context when needed
- Returns to main context after operations

### Flaky Sign-in
The login system is inconsistent. The scraper:
- Checks if sign-in is needed before each operation
- Retries failed sign-ins up to 3 times
- Clears form fields before entering credentials

### Spot Booking
- Detects available spots (clickable `<a>` elements)
- Books preferred spots in order of preference
- Handles USC credit usage automatically

## Troubleshooting

**Common Issues**:

1. **Sign-in failures**: 
   - Check credentials in `settings.toml`
   - Verify website is accessible
   - Try manual login to test account

2. **No spots available**:
   - Check if preferred spots are realistic
   - Verify class times and instructors exist
   - Use `--dry-run` to test criteria

3. **Selenium errors**:
   - Ensure Selenium Grid is running
   - Check browser compatibility
   - Verify ChromeDriver installation

4. **Storage issues**:
   - Ensure `data/` directory is writable
   - Check JSON file corruption
   - Clear data files if needed: `rm data/*.json`

## Development

**Adding new features**:

1. **Domain changes**: Add to `src/domain/models.py` and `src/domain/services.py`
2. **Web scraping**: Extend `src/infrastructure/web_scraper.py`
3. **CLI commands**: Add to `src/application/cli.py`
4. **Configuration**: Update `src/application/config.py`

**Testing**:
```bash
# Dry run to test configuration
python3 ridebln.py book --weekday mo --instructor Juan --time 18:00 --studio PRENZLAUER_BERG --dry-run

# Test status without booking
python3 ridebln.py status
```

## License

This project is for personal use only. Please respect the terms of service of ride-berlin.com.

## Contributing

This is a personal project, but suggestions for improvements are welcome via issues.
