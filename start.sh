#!/bin/bash

echo "=== INSTALLING DEPENDENCIES ==="
pip install -r requirements.txt

echo "=== INSTALLING SUPABASE DEPENDENCIES ==="
pip install supabase-py==2.3.5 postgrest-py==0.15.0 realtime-py==0.1.3 storage3==0.7.0 gotrue-py==1.2.0 supafunc==0.3.1 || echo "WARNING: Some Supabase dependencies couldn't be installed. Will use SQLite fallback."

echo "=== VERIFYING SUPABASE INSTALLATION ==="
if pip list | grep -q supabase-py; then
    echo "✅ Supabase installed successfully"
    pip list | grep supabase
    pip list | grep postgrest
    pip list | grep realtime
    pip list | grep storage3
    pip list | grep gotrue
    pip list | grep supafunc
else
    echo "⚠️ Supabase is not installed, will use SQLite fallback"
    # Make sure SQLite is available
    python -c "import sqlite3; print('✅ SQLite version:', sqlite3.sqlite_version)"
fi

echo "=== CHECKING DATABASE TABLES ==="
# Create the SQLite database and tables if they don't exist
python -c "
import sqlite3
import os

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
    cursor.execute(table_sql)
    
conn.commit()
conn.close()
print('✅ SQLite tables verified')
"

echo "=== STARTING BOT ==="
python main.py 