#!/bin/bash

echo "=== ONA Bot - Installing Required Dependencies ==="

# Установка основных зависимостей
pip install --no-cache-dir pydantic==1.10.12
pip install --no-cache-dir aiogram==3.0.0
pip install --no-cache-dir python-dotenv
pip install --no-cache-dir APScheduler

# Установка OpenAI и HTTPX (с точными версиями)
pip install --no-cache-dir openai==0.28.1
pip install --no-cache-dir httpx==0.23.3

# Установка Supabase
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2

# Установка дополнительных зависимостей
pip install --no-cache-dir elevenlabs==0.2.24 gTTS==2.3.2 ephem==4.1.4 PyYAML==6.0.1

# Проверка установки ключевых модулей
echo "=== Проверка установки ключевых модулей ==="
python -c "import openai; print('✅ OpenAI установлен успешно')" || echo "❌ OpenAI не установлен"
python -c "import httpx; print('✅ HTTPX установлен успешно')" || echo "❌ HTTPX не установлен"
python -c "import dotenv; print('✅ python-dotenv установлен успешно')" || echo "❌ python-dotenv не установлен"
python -c "import aiogram; print('✅ aiogram установлен успешно')" || echo "❌ aiogram не установлен"

echo "=== Установка зависимостей завершена ===" 