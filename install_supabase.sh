#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== INSTALLING SUPABASE DEPENDENCIES ==="
echo "Installing postgrest-py..."
pip install postgrest-py==0.10.6 || echo "Warning: Failed to install postgrest-py"

echo "Installing realtime-py..."
pip install realtime-py==0.1.3 || echo "Warning: Failed to install realtime-py"

echo "Installing storage3..."
pip install storage3==0.5.2 || echo "Warning: Failed to install storage3"

echo "Installing gotrue-py..."
pip install gotrue-py==0.6.1 || echo "Warning: Failed to install gotrue-py"

echo "Installing supafunc..."
pip install supafunc==0.2.2 || echo "Warning: Failed to install supafunc"

echo "Installing supabase-py..."
pip install supabase-py==0.7.1 || echo "Warning: Failed to install supabase-py"

echo "=== VERIFYING INSTALLATION ==="
echo "Supabase modules installed:"
pip list | grep -E 'supabase|postgrest|realtime|storage3|gotrue|supafunc' || echo "No Supabase modules found"

# Check if supabase-py is installed
if pip list | grep -q supabase-py; then
    echo "✅ Supabase successfully installed"
else
    echo "⚠️ Supabase installation failed. Will use SQLite fallback."
    # Make sure SQLite is available
    python -c "import sqlite3; print('✅ SQLite version:', sqlite3.sqlite_version)"
fi

echo "Supabase dependencies installation completed." 