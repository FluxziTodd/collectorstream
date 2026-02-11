#!/bin/bash
# Setup script for Sports Card Scout

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../.venv"

echo "=== Sports Card Scout Setup ==="

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Install playwright browsers if playwright is being used
if python -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Initialize database
echo "Initializing database..."
cd "$SCRIPT_DIR"
python -c "from db.models import init_db; init_db()"

# Check for .env
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "NOTE: No .env file found."
    echo "For LLM-powered parsing (recommended), create .env with:"
    echo "  cp .env.example .env"
    echo "  # Then add your ANTHROPIC_API_KEY"
    echo ""
    echo "Without it, the scraper will use basic pattern matching which"
    echo "works on some sites but not all."
fi

echo ""
echo "Setup complete! Usage:"
echo "  source $VENV_DIR/bin/activate"
echo "  cd $SCRIPT_DIR"
echo "  python main.py import              # Import your spreadsheet"
echo "  python main.py players             # List all players"
echo "  python main.py scrape              # Run all scrapers"
echo "  python main.py board 2026          # Show consensus board"
echo "  python main.py movers              # Show rising/falling players"
echo "  python main.py signals             # Show card buy signals"
