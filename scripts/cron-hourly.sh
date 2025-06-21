#!/bin/bash

# Hourly booking check script for RideBerlin
# Add to crontab with: 0 * * * * /path/to/ridebln/scripts/cron-hourly.sh

# Change to script directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run hourly check
python3 ridebln.py hourly --config settings.toml

# Log completion
echo "$(date): Hourly check completed" >> logs/cron.log 
