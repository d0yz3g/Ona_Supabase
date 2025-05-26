#!/bin/bash

# Скрипт запуска для Railway с исправлением проблем зависимостей

echo "=== ONA Bot Railway Starter with Fixed Dependencies ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Установка всех зависимостей
echo "=== Installing all dependencies ==="
pip install --no-cache-dir -r requirements.txt

# Установка pydantic 2.1.1 (совместимого с aiogram 3.0.0)
echo "=== Installing compatible pydantic version ==="
pip install --no-cache-dir --force-reinstall pydantic==2.1.1

# Установка критических зависимостей вручную
echo "=== Forcing installation of critical dependencies ==="
pip install --no-cache-dir openai==0.28.1
pip install --no-cache-dir httpx==0.23.3
pip install --no-cache-dir python-dotenv==1.0.0
pip install --no-cache-dir aiogram==3.0.0

# Установка Supabase
echo "=== Installing Supabase dependencies ==="
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2

# Запуск скрипта для проверки и исправления совместимости pydantic и aiogram
echo "=== Running pydantic compatibility fix ==="
python fix_pydantic.py

# Запуск скрипта для исправления импортов openai
echo "=== Running openai imports fix ==="
python fix_openai_imports.py

# Запуск скрипта для исправления railway_helper.py
echo "=== Running railway_helper fix ==="
python fix_railway_helper.py

# Запуск скрипта для исправления main.py
echo "=== Running main.py fix ==="
python fix_main_openai.py

# Запуск скрипта для исправления всех импортов OpenAI
echo "=== Running comprehensive OpenAI imports fix ==="
python fix_all_openai_imports.py

# Прямое исправление проблемных модулей
echo "=== Running direct module fixes ==="
python fix_direct_modules.py

# Патчинг самого модуля openai
echo "=== Patching openai module directly ==="
python fix_openai_module.py

# Запуск скрипта для проверки установки зависимостей
echo "=== Running dependency verification script ==="
python install_all_deps.py

# Проверка импорта aiogram
echo "=== Testing aiogram import ==="
python -c "from aiogram import Bot, Dispatcher, F; from aiogram.types.base import TelegramObject; print('✅ Aiogram импортирован успешно')" || echo "❌ Ошибка импорта aiogram"

# Запуск скрипта подготовки окружения
echo "=== Running pre-startup environment preparation ==="
python pre_startup.py

# Запуск бота
echo "=== Starting ONA Bot ==="
python -c "
try:
    # Предварительный импорт openai с monkey-патчингом
    import openai
    if not hasattr(openai, 'AsyncOpenAI'):
        class AsyncOpenAI: pass
        openai.AsyncOpenAI = AsyncOpenAI
    if not hasattr(openai, 'OpenAI'):
        class OpenAI: pass
        openai.OpenAI = OpenAI
    print('OpenAI monkey-patched successfully')
except:
    print('Failed to patch openai')
"

# Запуск через безопасную обертку
python safe_startup.py 