#!/bin/bash
# Скрипт для настройки и тестирования Supabase в Railway

echo "=== НАСТРОЙКА И ТЕСТИРОВАНИЕ SUPABASE ==="
echo "Дата запуска: $(date)"

# Проверка и установка зависимостей
echo "Установка модуля supabase-py и его зависимостей..."
pip install supabase-py==2.3.1 python-dotenv httpx postgrest-py storage3 gotrue realtime

# Проверка наличия .env файла
if [ -f ".env" ]; then
    echo "✓ Файл .env найден"
else
    echo "❌ Файл .env не найден"
    echo "Создание файла .env из sample.env..."
    if [ -f "sample.env" ]; then
        cp sample.env .env
        echo "✓ Файл .env создан из sample.env"
        echo "⚠️ Не забудьте указать корректные значения SUPABASE_URL и SUPABASE_KEY в файле .env"
    else
        echo "❌ Файл sample.env не найден"
        echo "Создание файла .env с минимальными настройками..."
        cat > .env << EOL
# Токен телеграм-бота (обязательно)
BOT_TOKEN=your_telegram_bot_token_here

# Параметры подключения к Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_api_key_here
EOL
        echo "✓ Файл .env создан с минимальными настройками"
        echo "⚠️ Укажите корректные значения в файле .env"
    fi
fi

# Запуск скрипта тестирования подключения к Supabase
echo "Запуск скрипта тестирования подключения к Supabase..."
python test_supabase.py

# Инструкции для Railway
echo ""
echo "=== ИНСТРУКЦИИ ДЛЯ НАСТРОЙКИ SUPABASE В RAILWAY ==="
echo "1. Перейдите в Railway Dashboard → ваш проект → Variables"
echo "2. Добавьте следующие переменные окружения:"
echo "   - SUPABASE_URL: URL вашего проекта Supabase (например, https://xyzproject.supabase.co)"
echo "   - SUPABASE_KEY: Сервисный ключ Supabase (не публичный ключ!)"
echo "3. Сохраните изменения"
echo ""
echo "Для тестирования подключения, выполните команду: python test_supabase.py" 