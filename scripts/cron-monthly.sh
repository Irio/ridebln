#!/bin/bash

# Monthly credit loading script for RideBerlin
# Add to crontab with: 0 0 1 * * /path/to/ridebln/scripts/cron-monthly.sh

# Change to script directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run monthly credit load
python3 ridebln.py monthly --config settings.toml

# Log completion
echo "$(date): Monthly credit load completed" >> logs/cron.log 
