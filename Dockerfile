FROM python:3.11-slim

WORKDIR /app

# Копируем сначала только requirements.txt для кэширования слоя с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Принудительно устанавливаем критические зависимости в правильном порядке
RUN pip install --no-cache-dir --force-reinstall python-dotenv==1.0.0 httpx==0.23.3 openai==1.3.3 pydantic==2.1.1 aiogram==3.0.0

# Копируем остальные файлы
COPY . .

# Проверяем установку openai
RUN python -c "from openai import AsyncOpenAI; print('AsyncOpenAI is available')"

# Запускаем бота с нашими патчами
CMD ["python", "safe_startup.py"] 