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

# Копируем остальные файлы
COPY . .

# Создаем директорию для временных файлов
RUN mkdir -p tmp

# Настройка вывода логов для контейнера
# Обеспечиваем правильное перенаправление stdout и stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONIOENCODING=utf-8

# Проверка файла restart_bot.py
RUN echo "Проверка файла restart_bot.py..."
RUN cat restart_bot.py | grep -q "parse_log_level" || echo "ВНИМАНИЕ: функция parse_log_level не найдена в restart_bot.py!"

# Дополнительная информация для логов
RUN echo "Ona2.0 Telegram Bot - Railway Deployment" > /app/railway_info.txt
RUN echo "Build date: $(date)" >> /app/railway_info.txt
RUN echo "Python version: $(python --version)" >> /app/railway_info.txt

# Проверка наличия psutil перед запуском
RUN python -c "import psutil; print('psutil успешно установлен, версия:', psutil.__version__)" >> /app/railway_info.txt

# Настройка логирования для Railway
RUN mkdir -p /app/logs
RUN touch /app/logs/bot.log /app/logs/restart.log

# Запуск с выводом информации для Railway и включенным режимом отладки
CMD echo "=== ONA2.0 TELEGRAM BOT STARTING ===" && \
    echo "" && \
    echo "$(cat /app/railway_info.txt)" && \
    echo "" && \
    echo "=== STARTING RESTART MONITOR ===" && \
    echo "" && \
    python restart_bot.py --debug 