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

# Копирование скриптов запуска
COPY startup.sh extra_setup.sh ./
RUN chmod +x startup.sh extra_setup.sh && \
    ls -la

# Копирование файлов проекта
COPY . .

# Делаем скрипты исполняемыми - ВАЖНО: Это должно выполняться ПОСЛЕ копирования файлов
RUN chmod +x *.py && \
    ls -la && \
    echo "Права установлены для скриптов Python"

# Экспорт переменной PORT для Railway
ENV PORT=8080

# Запуск бота через shell-скрипт
CMD ["/bin/bash", "startup.sh"] 