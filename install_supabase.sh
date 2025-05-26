#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== INSTALLING SUPABASE DEPENDENCIES ==="
echo "Installing postgrest-py..."
pip install postgrest-py==0.10.3 || echo "Warning: Failed to install postgrest-py"

echo "Installing realtime-py..."
pip install realtime-py==0.1.2 || echo "Warning: Failed to install realtime-py"

echo "Installing storage3..."
pip install storage3==0.5.0 || echo "Warning: Failed to install storage3"

echo "Installing supafunc..."
pip install supafunc==0.2.2 || echo "Warning: Failed to install supafunc"

echo "=== VERIFYING INSTALLATION ==="
echo "Supabase modules installed:"
pip list | grep -E 'postgrest|realtime|storage3|supafunc' || echo "No Supabase modules found"

# Check if key components are installed
SUPABASE_READY=0
if pip list | grep -q 'postgrest-py' && pip list | grep -q 'storage3'; then
    echo "✅ Основные компоненты Supabase успешно установлены"
    SUPABASE_READY=1
else
    echo "⚠️ Не все компоненты Supabase установлены. Будет использован SQLite."
    # Make sure SQLite is available
    python -c "import sqlite3; print('✅ SQLite version:', sqlite3.sqlite_version)"
fi

# Проверяем наличие pydantic
echo "=== CHECKING PYDANTIC ==="
python -c "import pydantic; print('✅ Pydantic version:', pydantic.__version__)" || echo "⚠️ Pydantic не установлен или недоступен"

echo "Supabase dependencies installation completed." 