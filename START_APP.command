#!/bin/bash
# ═══════════════════════════════════════════════════════
# Campus Dining Budget App — One-Click Launcher
# ═══════════════════════════════════════════════════════
# Double-click this file to start the app.
# It will open automatically in your browser.
# To stop: close this Terminal window.
# ═══════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo ""
echo "  🍽  Campus Dining Budget & Operations App"
echo "  ─────────────────────────────────────────"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 is not installed."
    echo ""
    echo "  Please install it from: https://www.python.org/downloads/"
    echo ""
    echo "  Press any key to exit..."
    read -n 1
    exit 1
fi

echo "  ✓ Python 3 found: $(python3 --version)"

# Install dependencies if needed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo ""
    echo "  📦 Installing required packages (first time only)..."
    echo "     This may take 1-2 minutes..."
    echo ""
    python3 -m pip install --user -r requirements.txt --quiet
    echo ""
    echo "  ✓ Packages installed!"
fi

# Initialize database if needed
if [ ! -f "budget.db" ]; then
    echo "  📊 Setting up database (first time only)..."
    python3 -c "import init_db; init_db.init_database()"
    echo "  ✓ Database ready!"
fi

echo ""
echo "  🚀 Starting app..."
echo "  📍 Opening in your browser at: http://localhost:8501"
echo ""
echo "  ⚠️  Keep this window open while using the app."
echo "  To stop the app, close this window or press Ctrl+C."
echo ""

# Open browser after a short delay
(sleep 2 && open http://localhost:8501) &

# Start the app
python3 -m streamlit run app.py --server.headless true --server.port 8501
