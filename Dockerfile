FROM python:3.11-slim

WORKDIR /app

# Установка базовых зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir python-dotenv==1.0.0 httpx==0.23.3 openai==1.3.3 pydantic==2.1.1 aiogram==3.0.0 && \
    pip install --no-cache-dir -r requirements.txt || echo "Некоторые пакеты не установлены, продолжаем"

# Копирование файлов проекта
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x *.py

# Экспорт переменной PORT для Railway
ENV PORT=8080

# Запуск бота
CMD ["python", "direct_start.py"] 