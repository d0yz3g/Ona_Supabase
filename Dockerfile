FROM python:3.11-slim

WORKDIR /app

# Установка базовых зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY . .

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir python-dotenv httpx openai pydantic aiogram

# Делаем скрипты исполняемыми
RUN chmod +x *.py && \
    chmod +x *.sh && \
    ls -la

# Порт для веб-сервера
ENV PORT=8080

# Запуск бота напрямую через Python
CMD ["python", "railway_final.py"] 