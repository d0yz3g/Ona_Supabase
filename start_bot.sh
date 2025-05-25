#!/bin/bash

# Этот скрипт специально для Railway - простой запуск бота без лишних проверок

# Устанавливаем базовые переменные окружения
export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
export PYTHONIOENCODING=utf-8
export PYTHONPATH=/app

echo "=== STARTING ONA BOT ON RAILWAY ==="
echo "Python version: $(python --version)"
echo "Bot token is set: $(if [ -z "$BOT_TOKEN" ]; then echo "NO"; else echo "YES"; fi)"
echo "Current directory: $(pwd)"
echo "Current Python path: $PYTHONPATH"

# Устанавливаем необходимые пакеты
pip install pydantic==1.10.12 aiogram==3.0.0

# Запускаем бота
python main.py 