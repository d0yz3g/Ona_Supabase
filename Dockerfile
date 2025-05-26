FROM python:3.11-slim

WORKDIR /app

# Копируем только необходимые файлы
COPY ultrabasic_bot.py .
COPY requirements.txt.minimal requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Делаем скрипт исполняемым
RUN chmod +x ultrabasic_bot.py

# Запуск бота
CMD ["python", "ultrabasic_bot.py"] 