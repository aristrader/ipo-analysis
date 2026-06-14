#!/bin/bash
echo "Starting Moneycontrol fallback scraper..."
source .venv/bin/activate
nohup python3 pipeline/03j_moneycontrol_corp_actions.py > moneycontrol_scraper.log 2>&1 &
echo "Scraper started in background! You can close this terminal."
