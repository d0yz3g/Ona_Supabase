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

# Установка базовых зависимостей и корректной версии httpx
RUN pip install --no-cache-dir httpx>=0.24.0

# Установка остальных зависимостей
RUN pip install --no-cache-dir python-dotenv pytz pre-commit pytest
RUN pip install --no-cache-dir aiogram==3.2.0
RUN pip install --no-cache-dir openai==1.3.5
RUN pip install --no-cache-dir ephem elevenlabs aiofiles apscheduler

# Копируем остальные файлы
COPY . .

CMD ["python", "main.py"] 