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

# Копируем остальные файлы
COPY . .

# Создаем директорию для временных файлов
RUN mkdir -p tmp

# Настройка вывода логов для контейнера
# Обеспечиваем правильное перенаправление stdout и stderr
ENV PYTHONUNBUFFERED=1

# Дополнительная информация для логов
RUN echo "Ona2.0 Telegram Bot - Railway Deployment" > /app/railway_info.txt
RUN echo "Build date: $(date)" >> /app/railway_info.txt
RUN echo "Python version: $(python --version)" >> /app/railway_info.txt

# Запуск с выводом информации для Railway
CMD echo "=== ONA2.0 TELEGRAM BOT STARTING ===" && \
    echo "$(cat /app/railway_info.txt)" && \
    echo "=== STARTING RESTART MONITOR ===" && \
    python restart_bot.py 