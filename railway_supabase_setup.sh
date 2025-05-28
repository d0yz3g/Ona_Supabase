#!/bin/bash
# Script to set up Supabase on Railway

echo "=== RAILWAY SUPABASE SETUP ==="
echo "Date: $(date)"
echo "Current directory: $(pwd)"

# Install Supabase and its dependencies
echo "Installing Supabase and dependencies..."
pip install supabase-py==2.3.1 postgrest-py==0.11.0 httpx gotrue==1.3.0 storage3==0.6.1 realtime==1.0.0

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
for module in postgrest httpx gotrue storage3 realtime; do
    if python -c "import $module" 2>/dev/null; then
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
echo "1. Make sure supabase-py and its dependencies are in requirements.txt"
echo "2. Set SUPABASE_URL and SUPABASE_KEY environment variables in Railway dashboard"
echo "3. Deploy your application"
echo ""
echo "If you're still having issues, check Railway logs for specific error messages" 