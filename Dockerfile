FROM python:3.11-slim

WORKDIR /app

# Установка базовых зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование минимального файла зависимостей
COPY requirements.txt.minimal ./requirements.txt

# Обновление pip и установка минимальных зависимостей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x *.py || echo "Не удалось установить права"
RUN chmod +x *.sh || echo "Не найдены shell-скрипты"

# Порт для веб-сервера
ENV PORT=8080

# Запуск бота напрямую через Python
CMD ["python", "direct_start.py"] 