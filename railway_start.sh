#!/bin/bash

# Скрипт запуска для Railway
# Выполняет предварительные проверки и запускает бота

echo "=== ONA2.0 TELEGRAM BOT RAILWAY LAUNCHER ==="
echo "Дата запуска: $(date)"
echo "Рабочая директория: $(pwd)"

# Вывод информации о рабочей директории
echo "Содержимое рабочей директории:"
ls -la

# Проверка наличия файлов бота
echo "Проверка наличия ключевых файлов бота..."
REQUIRED_FILES=("main.py" "restart_bot.py" "railway_helper.py" "railway_logging.py" "create_placeholders.py")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ОШИБКА: Файл $file не найден!"
        MISSING_FILES+=("$file")
    else
        echo "✓ Файл $file найден"
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "ВНИМАНИЕ: Отсутствуют некоторые ключевые файлы: ${MISSING_FILES[*]}"
    echo "Попытка найти файлы в проекте..."
    
    # Поиск файлов в проекте
    for file in "${MISSING_FILES[@]}"; do
        FOUND_FILE=$(find . -name "$file" -type f | head -n 1)
        if [ -n "$FOUND_FILE" ]; then
            echo "Найден файл $file по пути $FOUND_FILE, копирование..."
            cp "$FOUND_FILE" .
            echo "✓ Файл $file скопирован в рабочую директорию"
        else
            echo "ОШИБКА: Файл $file не найден в проекте!"
        fi
    done
fi

# Создание необходимых директорий
echo "Создание необходимых директорий..."
mkdir -p logs tmp
echo "✓ Директории logs и tmp созданы"

# Запуск railway_helper.py для инициализации
echo "Запуск Railway Helper для инициализации..."
if [ -f "railway_helper.py" ]; then
    python railway_helper.py
    echo "✓ Railway Helper выполнен"
else
    echo "ВНИМАНИЕ: Файл railway_helper.py не найден, пропускаем инициализацию"
    
    # Запуск скрипта создания заглушек
    echo "Запуск скрипта создания заглушек для недостающих модулей..."
    if [ -f "create_placeholders.py" ]; then
        python create_placeholders.py
        echo "✓ Скрипт создания заглушек выполнен"
    else
        echo "ВНИМАНИЕ: Файл create_placeholders.py не найден, пропускаем создание заглушек"
    fi
    
    # Запуск скрипта исправления импортов
    echo "Запуск скрипта исправления импортов..."
    if [ -f "fix_imports.py" ]; then
        python fix_imports.py
        echo "✓ Скрипт исправления импортов выполнен"
    else
        echo "ВНИМАНИЕ: Файл fix_imports.py не найден, пропускаем исправление импортов"
    fi
fi

# Проверка наличия ключевых переменных окружения
echo "Проверка переменных окружения..."
if [ -z "$BOT_TOKEN" ]; then
    echo "ОШИБКА: Переменная BOT_TOKEN не установлена!"
else
    echo "✓ Переменная BOT_TOKEN установлена"
fi

# Проверка установленных пакетов Python
echo "Проверка установленных пакетов Python..."
pip list | grep aiogram
pip list | grep openai
pip list | grep elevenlabs
pip list | grep psutil

# Создание списка импортированных модулей
echo "Проверка доступности модулей через импорт..."
python -c "import sys; print('sys.path =', sys.path); import aiogram; print('aiogram импортирован успешно')" || echo "ОШИБКА: Не удалось импортировать aiogram"

# Запуск бота с перезапуском
echo "=== ЗАПУСК БОТА С МОНИТОРИНГОМ ПЕРЕЗАПУСКА ==="
echo "Используется Python: $(python --version)"
python restart_bot.py --debug 