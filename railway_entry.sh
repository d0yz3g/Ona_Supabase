#!/bin/bash

# Railway entry point script for ONA bot
# This script runs the dependency check and starts the bot

set -e

echo "=== ONA Bot Railway Entry Point ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Current Python path: $PYTHONPATH"

# Ensure required environment variables
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ ERROR: BOT_TOKEN environment variable is not set!"
    exit 1
else
    echo "✅ BOT_TOKEN is set"
fi

# Install critical dependencies
echo "=== Installing critical dependencies ==="
pip install --no-cache-dir pydantic==1.10.12 aiogram==3.0.0 python-dotenv APScheduler

# Try to install Supabase dependencies
echo "=== Attempting to install Supabase dependencies ==="
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2 || {
    echo "⚠️ Warning: Supabase installation failed, will use SQLite fallback"
}

# Create necessary directories
mkdir -p logs tmp

# Apply pydantic patch if necessary
if [ -f "patch_pydantic.py" ]; then
    echo "=== Applying pydantic patch ==="
    python patch_pydantic.py || {
        echo "⚠️ Warning: Failed to apply pydantic patch"
    }
fi

# Start the bot
echo "=== Starting ONA Bot ==="
python main.py 