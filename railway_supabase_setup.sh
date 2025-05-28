#!/bin/bash
# Script to set up Supabase on Railway

echo "=== RAILWAY SUPABASE SETUP ==="
echo "Date: $(date)"
echo "Current directory: $(pwd)"

# Install system dependencies
echo "Installing system dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    git

# Install Supabase and its dependencies
echo "Installing Supabase and dependencies..."
pip install --no-cache-dir httpx==0.24.1
pip install --no-cache-dir postgrest-py==0.10.3
pip install --no-cache-dir gotrue==0.5.4 
pip install --no-cache-dir storage3==0.5.4
# Removing realtime==0.1.3 as it's incompatible with Python 3.11
# It's not required as a separate dependency when using supabase-py
pip install --no-cache-dir supabase-py==2.0.0

# Check if installation was successful
echo "Verifying Supabase installation..."
if python -c "import supabase; print(f'Supabase version: {supabase.__version__ if hasattr(supabase, \"__version__\") else \"unknown\"}')"; then
    echo "✅ Supabase module installed successfully"
else
    echo "❌ Supabase module installation failed"
    exit 1
fi

# Verify all dependencies are installed
echo "Checking Supabase dependencies..."
for module in postgrest httpx gotrue storage3; do
    if python -c "import $module; version = getattr($module, '__version__', 'unknown'); print(f'$module installed successfully (version: {version})')" 2>/dev/null; then
        echo "✅ $module dependency installed successfully"
    else
        echo "❌ $module dependency installation failed"
    fi
done

# Check for environment variables
echo "Checking Supabase environment variables..."
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL environment variable not set"
    echo "Please set it in Railway dashboard or .env file"
else
    echo "✅ SUPABASE_URL environment variable is set"
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "❌ SUPABASE_KEY environment variable not set"
    echo "Please set it in Railway dashboard or .env file"
else
    echo "✅ SUPABASE_KEY environment variable is set"
fi

# Run the test script
echo "Running Supabase connection test..."
python test_supabase_connection.py

echo "=== RAILWAY SUPABASE SETUP COMPLETED ==="
echo ""
echo "Instructions for Railway deployment:"
echo "1. Make sure all Supabase dependencies are in requirements.txt with compatible versions:"
echo "   - supabase-py==2.0.0"
echo "   - postgrest-py==0.10.3"
echo "   - httpx==0.24.1"
echo "   - gotrue==0.5.4"
echo "   - storage3==0.5.4"
echo "2. Set SUPABASE_URL and SUPABASE_KEY environment variables in Railway dashboard"
echo "3. Deploy your application"
echo ""
echo "If you're still having issues, check Railway logs for specific error messages" 