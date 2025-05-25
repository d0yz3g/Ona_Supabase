#!/bin/bash

# Exit on error, but not for pip commands
set -e

echo "=== CHECKING ENVIRONMENT ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Проверяем наличие файла railway_requirements.txt
if [ -f "railway_requirements.txt" ]; then
    echo "=== INSTALLING RAILWAY REQUIREMENTS ==="
    # Use --no-cache-dir to reduce memory usage on Railway
    pip install --no-cache-dir -r railway_requirements.txt || {
        echo "⚠️ Warning: Some Railway requirements failed to install. Trying standard requirements."
        pip install --no-cache-dir -r requirements.txt || {
            echo "⚠️ Warning: Some standard requirements failed to install. Continuing anyway."
        }
    }
else
    echo "=== INSTALLING DEPENDENCIES ==="
    # Use --no-cache-dir to reduce memory usage on Railway
    pip install --no-cache-dir -r requirements.txt || {
        echo "⚠️ Warning: Some dependencies failed to install. Continuing anyway."
    }
fi

echo "=== CHECKING FOR SQLITE ==="
# Make sure SQLite is available
python -c "import sqlite3; print('✅ SQLite version:', sqlite3.sqlite_version)" || {
    echo "❌ ERROR: SQLite is not available. This is required even as a fallback."
    exit 1
}

echo "=== TRYING TO INSTALL SUPABASE DEPENDENCIES ==="
# Try to install dependencies from supabase_requirements.txt
pip install --no-cache-dir -r supabase_requirements.txt || {
    echo "⚠️ Warning: Supabase dependencies failed to install from requirements file. Will try individual installations."
}

# Try individual installations only if the above failed
if ! pip list | grep -q supabase-py; then
    echo "⚠️ Supabase not found. Trying individual installation..."
    ./install_supabase.sh || {
        echo "⚠️ Warning: Supabase installation script failed. Will use SQLite fallback."
    }
fi

echo "=== VERIFYING SUPABASE INSTALLATION ==="
if pip list | grep -q supabase-py; then
    echo "✅ Supabase installed successfully"
    pip list | grep -E 'supabase|postgrest|realtime|storage3|gotrue|supafunc'
else
    echo "⚠️ Supabase is not installed, will use SQLite fallback"
    # Make sure SQLite is available (double-check)
    python -c "import sqlite3; print('✅ SQLite version:', sqlite3.sqlite_version)"
    
    # Ensure the fallback module is available
    if [ -f "supabase_fallback.py" ]; then
        echo "✅ SQLite fallback module (supabase_fallback.py) is available"
    else
        echo "❌ ERROR: SQLite fallback module (supabase_fallback.py) is missing!"
    fi
fi

echo "=== CHECKING DATABASE TABLES ==="
# Create the SQLite database and tables if they don't exist
python -c "
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_setup')

try:
    db_path = os.getenv('SQLITE_DB_PATH', 'ona.db')
    print(f'Checking SQLite database at {db_path}')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = [
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            profile_text TEXT,
            details_text TEXT,
            answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )''',
        '''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            time TEXT,
            days TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )''',
        '''CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            answer_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )'''
    ]

    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            logger.info(f'Table created or already exists')
        except sqlite3.Error as e:
            logger.error(f'Error creating table: {e}')
        
    conn.commit()
    conn.close()
    print('✅ SQLite tables verified')
except Exception as e:
    print(f'❌ Error setting up SQLite: {e}')
"

# Make sure the bot token is available
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ ERROR: BOT_TOKEN environment variable is not set!"
    exit 1
else
    echo "✅ BOT_TOKEN is set"
fi

echo "=== APPLYING PYDANTIC PATCH ==="
# Attempt to apply pydantic patch
if [ -f "patch_pydantic.py" ]; then
    python patch_pydantic.py || {
        echo "⚠️ Warning: Failed to apply pydantic patch. Bot may not work correctly."
    }
else
    echo "⚠️ Warning: patch_pydantic.py not found. Skipping patch."
fi

echo "=== STARTING BOT ==="
# Execute with proper error handling
python main.py || {
    echo "❌ Bot crashed with error code $?"
    echo "Check logs for details"
    exit 1
} 