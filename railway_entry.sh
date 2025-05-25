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

# Run dependency check first
echo "=== Running dependency check ==="
python check_dependencies.py || {
    echo "⚠️ Warning: Some dependencies are missing or incompatible"
    echo "⚠️ Attempting to install critical dependencies individually..."
}

# Install critical dependencies
echo "=== Installing critical dependencies ==="
pip install --no-cache-dir pydantic==1.10.12 || echo "⚠️ Failed to install pydantic"
pip install --no-cache-dir aiogram==3.0.0 || echo "⚠️ Failed to install aiogram"
pip install --no-cache-dir python-dotenv || {
    echo "⚠️ Warning: python-dotenv installation failed, will use fallback"
}
pip install --no-cache-dir APScheduler || echo "⚠️ Failed to install APScheduler"

# Check if python-dotenv is available
python -c "import dotenv; print('✅ python-dotenv is available')" 2>/dev/null || {
    echo "⚠️ python-dotenv is not available, using fallback"
    
    # Create dotenv.py if it doesn't exist
    if [ ! -f "dotenv.py" ]; then
        echo "Creating dotenv.py fallback module..."
        cat > dotenv.py << EOL
"""
Прямая замена для модуля python-dotenv.
"""
import os
import sys

def load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False, **kwargs):
    """Загружает переменные из .env файла."""
    print("[dotenv.py] Using fallback implementation")
    return True

def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False):
    """Ищет .env файл."""
    if os.path.isfile(filename):
        return os.path.abspath(filename)
    return ""
EOL
        echo "✅ Created dotenv.py fallback module"
    fi
    
    # Apply patch to main.py if fix_dotenv_import.py exists
    if [ -f "fix_dotenv_import.py" ]; then
        echo "Applying dotenv import patch to main.py..."
        python fix_dotenv_import.py || {
            echo "⚠️ Warning: Failed to apply dotenv import patch"
        }
    fi
}

# Create a backup of main.py
if [ -f "main.py" ]; then
    cp main.py main.py.bak
    echo "✅ Created backup of main.py"
    
    # Check for dotenv import in main.py and patch it if needed
    if grep -q "from dotenv import load_dotenv" main.py; then
        echo "Patching dotenv import in main.py..."
        sed -i 's/from dotenv import load_dotenv/try:\n    from dotenv import load_dotenv\n    print("Using standard python-dotenv")\nexcept ImportError:\n    print("python-dotenv not found, using fallback")\n    def load_dotenv(dotenv_path=None):\n        print("Using fallback load_dotenv")\n        return True/g' main.py || {
            echo "⚠️ Warning: Failed to patch main.py, restoring backup"
            cp main.py.bak main.py
        }
    fi
fi

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

# Final check if dotenv is available
python -c "import dotenv; print('✅ Final check: dotenv is available')" 2>/dev/null || {
    echo "⚠️ Final check: dotenv is still not available. Adding current directory to Python path."
    export PYTHONPATH=$PYTHONPATH:$(pwd)
}

# Start the bot
echo "=== Starting ONA Bot ==="
python main.py 