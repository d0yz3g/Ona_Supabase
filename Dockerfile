FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libc-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Обновим pip
RUN pip install --upgrade pip setuptools wheel

# Копируем только requirements.txt
COPY requirements.txt .

# Установка зависимостей в оптимальном порядке
# Сначала базовые и критичные зависимости
RUN pip install --no-cache-dir python-dotenv pytz pre-commit pytest
RUN pip install --no-cache-dir httpx==0.25.2 aiohttp==3.9.1
RUN pip install --no-cache-dir aiogram==3.2.0
RUN pip install --no-cache-dir openai==1.3.5
RUN pip install --no-cache-dir ephem elevenlabs aiofiles apscheduler

# Явная установка psutil с нужными зависимостями
RUN pip install --no-cache-dir --force-reinstall psutil==5.9.5

# Создаем директорию для временных файлов
RUN mkdir -p tmp
RUN mkdir -p logs

# Настройка вывода логов для контейнера
# Обеспечиваем правильное перенаправление stdout и stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONIOENCODING=utf-8

# Копируем все исходные файлы проекта
COPY . .

# Проверка наличия обязательных файлов
RUN echo "Проверка обязательных файлов проекта..." && \
    for file in main.py railway_logging.py restart_bot.py survey_handler.py meditation_handler.py conversation_handler.py reminder_handler.py; do \
        if [ ! -f "$file" ]; then \
            echo "ОШИБКА: Файл $file не найден!"; \
            ls -la; \
        else \
            echo "✓ Файл $file найден"; \
        fi; \
    done

# Создание списка файлов в контейнере для отладки
RUN echo "Структура файлов в контейнере:" > /app/container_files.txt && \
    ls -la >> /app/container_files.txt && \
    echo "\nСодержимое рабочей директории:" >> /app/container_files.txt && \
    find . -type f -name "*.py" | sort >> /app/container_files.txt

# Дополнительная информация для логов
RUN echo "Ona2.0 Telegram Bot - Railway Deployment" > /app/railway_info.txt
RUN echo "Build date: $(date)" >> /app/railway_info.txt
RUN echo "Python version: $(python --version)" >> /app/railway_info.txt

# Проверка наличия psutil перед запуском
RUN python -c "import psutil; print('psutil успешно установлен, версия:', psutil.__version__)" >> /app/railway_info.txt

# Проверка импорта ключевых модулей
RUN echo "Проверка импорта ключевых модулей:" >> /app/railway_info.txt
RUN python -c "import sys; sys.path.insert(0, '/app'); import railway_logging; print('railway_logging импортирован успешно')" >> /app/railway_info.txt || echo "ОШИБКА: railway_logging не импортируется" >> /app/railway_info.txt

# Делаем railway_start.sh исполняемым
RUN chmod +x railway_start.sh

# Настройка логирования для Railway
RUN touch /app/logs/bot.log /app/logs/restart.log

# Запуск скрипта railway_start.sh для старта бота
CMD ["/bin/bash", "railway_start.sh"] 