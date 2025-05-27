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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Обновим pip
RUN pip install --upgrade pip setuptools wheel

# Копируем только requirements.txt
COPY requirements.txt .

# Установка зависимостей по группам для лучшей отладки
RUN pip install --no-cache-dir python-dotenv requests
RUN pip install --no-cache-dir aiogram==3.2.0 aiohttp
RUN pip install --no-cache-dir pydantic psutil
RUN pip install --no-cache-dir APScheduler
RUN pip install --no-cache-dir openai httpx

# Установка оставшихся зависимостей
RUN pip install --no-cache-dir -r requirements.txt || echo "Некоторые зависимости не установлены, продолжаем сборку"

# Создаем директорию для временных файлов и логов
RUN mkdir -p tmp logs data

# Настройка вывода логов для контейнера
# Обеспечиваем правильное перенаправление stdout и stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH=/app
ENV RAILWAY=true

# Копируем все исходные файлы проекта
COPY . .

# Создаем файл для проверки состояния
RUN echo '#!/bin/bash\n\
curl -s http://localhost:8080/health || exit 1' > /app/healthcheck.sh && \
chmod +x /app/healthcheck.sh

# Проверка наличия ключевых файлов
RUN echo "Проверка наличия ключевых файлов..." && \
ls -la *.py

# Создаем файл для запуска сервера
RUN echo '#!/bin/bash\n\
echo "Запуск бота в режиме webhook..."\n\
export WEBHOOK_MODE=true\n\
# Проверка наличия переменных окружения\n\
if [ -z "$BOT_TOKEN" ]; then\n\
  echo "ОШИБКА: Переменная BOT_TOKEN не установлена!"\n\
  exit 1\n\
fi\n\
\n\
# Запуск webhook сервера\n\
python webhook_server.py\n' > /app/start_webhook.sh && \
chmod +x /app/start_webhook.sh

# Создание диагностического скрипта
RUN echo '#!/bin/bash\n\
echo "Диагностика бота..."\n\
echo "Python version: $(python --version)"\n\
echo "Current directory: $(pwd)"\n\
echo "Environment variables:"\n\
env | grep -v "TOKEN"\n\
echo "Installed packages:"\n\
pip list\n\
echo "Files in directory:"\n\
ls -la\n\
echo "Network connections:"\n\
netstat -tulpn || echo "netstat не установлен"\n\
echo "Running processes:"\n\
ps aux\n\
echo "Health check:"\n\
curl -v http://localhost:8080/health || echo "Health check failed"\n' > /app/diagnose.sh && \
chmod +x /app/diagnose.sh

# Создаем стартовый скрипт, который будет выполнять диагностику перед запуском
RUN echo '#!/bin/bash\n\
echo "=== Запуск диагностики перед стартом ==="\n\
echo "Проверка доступности порта 8080..."\n\
if netstat -tulpn | grep -q ":8080 "; then\n\
  echo "ВНИМАНИЕ: Порт 8080 уже занят!"\n\
  netstat -tulpn | grep ":8080 "\n\
  echo "Попытка остановить процесс..."\n\
  PID=$(netstat -tulpn | grep ":8080 " | awk "{print \$7}" | cut -d"/" -f1)\n\
  if [ ! -z "$PID" ]; then\n\
    echo "Остановка процесса с PID $PID"\n\
    kill -15 $PID\n\
    sleep 2\n\
  fi\n\
fi\n\
\n\
echo "Запуск webhook сервера..."\n\
exec /app/start_webhook.sh\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Проверка наличия psutil перед запуском
RUN python -c "import psutil; print('psutil успешно установлен, версия:', psutil.__version__)" || pip install psutil

# Установка webhook_server.py как точки входа
ENTRYPOINT ["/app/entrypoint.sh"]

# Предоставляем информацию о состоянии для Docker и Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD /app/healthcheck.sh 