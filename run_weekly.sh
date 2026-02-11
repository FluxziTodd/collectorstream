#!/bin/bash
# Sports Card Scout — Weekly automated scrape and report generation
# Runs via macOS launchd every Monday at 8am

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../.venv"
LOG_DIR="$HOME/Desktop/WNBA-Scout/logs"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/last-run.log"

# Redirect all output to log
exec > >(tee "$LOG_FILE") 2>&1

echo "=========================================="
echo "Sports Card Scout — Weekly Run"
echo "$(date)"
echo "=========================================="

# Activate virtual environment
source "$VENV_DIR/bin/activate"
cd "$SCRIPT_DIR"

# Load .env
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

echo ""
echo "--- Scraping all sources ---"
python main.py scrape 2>&1 || echo "Some scrapes failed (this is normal)"

echo ""
echo "--- Normalizing player names ---"
python main.py normalize

echo ""
echo "--- Searching eBay for card prices ---"
python main.py cards 2>&1 || echo "Some eBay searches failed (this is normal)"

echo ""
echo "--- Searching eBay for watchlist players ---"
python main.py watchlist --search 2>&1 || echo "Some watchlist searches failed (this is normal)"

echo ""
echo "--- Importing portfolio submissions ---"
python main.py portfolio --import-submissions 2>&1 || echo "Portfolio import skipped"

echo ""
echo "--- Checking portfolio card prices ---"
python main.py portfolio --price-check 2>&1 || echo "Portfolio price check failed"

echo ""
echo "--- Exporting portfolio data ---"
python main.py portfolio --export 2>&1 || echo "Portfolio export failed"

echo ""
echo "--- Scraping player stats ---"
python main.py stats 2>&1 || echo "Stats scrape failed"

echo ""
echo "--- Running hot/cold detection ---"
python main.py stats --detect 2>&1 || echo "Detection failed"

echo ""
echo "--- Generating HTML reports ---"
python main.py report

echo ""
echo "--- Syncing to S3 / CloudFront ---"
AWS_PROFILE=fluxzi aws s3 sync "$HOME/Desktop/WNBA-Scout/" s3://collectorstream-site/ --delete --exclude "logs/*" --exclude ".DS_Store" --exclude "private/pipeline-trigger.json" --exclude "private/pipeline-status.json" --exclude "private/portfolio-submissions/*" --exclude "private/portfolio-data.json" 2>&1 || echo "S3 sync failed"
AWS_PROFILE=fluxzi aws cloudfront create-invalidation --distribution-id E26VWZLVN1SVFJ --paths "/*" 2>&1 || echo "CloudFront invalidation failed"

echo ""
echo "=========================================="
echo "Complete at $(date)"
echo "Reports at: $HOME/Desktop/WNBA-Scout/"
echo "Live at: https://collectorstream.com"
echo "=========================================="
