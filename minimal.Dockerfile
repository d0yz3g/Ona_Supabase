FROM python:3.10-slim

WORKDIR /app

# Копируем только минимальный скрипт
COPY bare_minimal.py .

# Делаем скрипт исполняемым
RUN chmod +x bare_minimal.py

# Порт для веб-сервера
EXPOSE 8080

# Запуск минимального скрипта
CMD ["python", "bare_minimal.py"] 