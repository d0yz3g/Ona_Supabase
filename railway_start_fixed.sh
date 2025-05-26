#!/bin/bash

# Скрипт запуска для Railway с исправлением проблем зависимостей

echo "=== ONA Bot Railway Starter with Fixed Dependencies ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Установка всех зависимостей
echo "=== Installing all dependencies ==="
pip install --no-cache-dir -r requirements.txt

# Установка критических зависимостей вручную
echo "=== Forcing installation of critical dependencies ==="
pip install --no-cache-dir openai==0.28.1
pip install --no-cache-dir httpx==0.23.3
pip install --no-cache-dir python-dotenv==1.0.0
pip install --no-cache-dir aiogram==3.0.0

# Установка Supabase
echo "=== Installing Supabase dependencies ==="
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2

# Запуск скрипта для проверки установки зависимостей
echo "=== Running dependency verification script ==="
python install_all_deps.py

# Запуск бота
echo "=== Starting ONA Bot ==="
python main.py 