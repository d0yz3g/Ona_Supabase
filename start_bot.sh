#!/bin/bash

# Simple Railway deployment script for the ONA bot

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
export PYTHONIOENCODING=utf-8
export PYTHONPATH=/app

echo "=== STARTING ONA BOT ON RAILWAY ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Install required packages with specific versions for compatibility
echo "=== INSTALLING DEPENDENCIES ==="
pip install pydantic==1.10.12 aiogram==3.0.0
pip install python-dotenv APScheduler requests openai

# Try to install Supabase, but continue if it fails
echo "=== TRYING TO INSTALL SUPABASE ==="
pip install postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2 || {
    echo "⚠️ Warning: Supabase installation failed, will use SQLite fallback"
}

# Create necessary directories
mkdir -p logs tmp

# Start the bot
echo "=== STARTING BOT ==="
python main.py 