#!/bin/bash
# ============================================================
#  Video Downloader Pro — One-click launcher
#  Double-click this file to open the app.
# ============================================================

# Go to the folder where this script lives (the video_download dir)
cd "$(dirname "$0")"

# Make BBDown executable (safe to run multiple times)
chmod +x ./BBDown 2>/dev/null

# Activate virtual environment and launch GUI
PYTHON_EXEC="./venv/bin/python3"

if [ -f "$PYTHON_EXEC" ]; then
    echo "🚀 Launching Video Downloader Pro..."
    "$PYTHON_EXEC" video_downloader_gui.py
else
    echo "⚠️  Virtual environment not found at: ./venv"
    echo "Trying system python3..."
    
    # Check if customtkinter is available on system python
    if python3 -c "import customtkinter" 2>/dev/null; then
        python3 video_downloader_gui.py
    else
        echo ""
        echo "❌ Missing dependencies. Please run:"
        echo "   cd $(pwd)"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install customtkinter"
        echo ""
        echo "Press any key to close..."
        read -n 1
    fi
fi
