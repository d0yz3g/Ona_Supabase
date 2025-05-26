FROM python:3.11-slim

WORKDIR /app

# Update pip and install essential build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем сначала только requirements.txt для кэширования слоя с зависимостями
COPY requirements.txt .

# Устанавливаем критические зависимости сначала
RUN pip install --no-cache-dir python-dotenv==1.0.0 httpx==0.23.3 openai==1.3.3 pydantic==2.1.1 aiogram==3.0.0

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt || echo "Some packages failed to install, continuing anyway"

# Копируем остальные файлы
COPY . .

# Make the startup script executable
RUN chmod +x railway_start.sh

# Проверяем установку openai
RUN python -c "from openai import AsyncOpenAI; print('AsyncOpenAI is available')" || echo "AsyncOpenAI check failed, will use patch system"

# Запускаем бота с нашим скриптом запуска
CMD ["./railway_start.sh"] 