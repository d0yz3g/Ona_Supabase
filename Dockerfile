FROM python:3.11-slim

WORKDIR /app

# Установка базовых зависимостей и утилит
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Обновление pip и установка базовых инструментов
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копирование файла с зависимостями
COPY requirements.txt .

# Установка критических зависимостей
RUN pip install --no-cache-dir python-dotenv==1.0.0 httpx==0.23.3 openai==1.3.3 pydantic==2.1.1 aiogram==3.0.0

# Установка остальных зависимостей
RUN pip install --no-cache-dir -r requirements.txt || echo "Some packages failed to install, continuing anyway"

# Копирование файлов для исправления импортов
COPY pre_import_fix.py patch_main.py fix_imports_global.py direct_start.py ./

# Проверка доступности AsyncOpenAI
RUN pip show openai && python -c "import openai; print(f'OpenAI version: {openai.__version__}')" || echo "OpenAI not available"

# Копирование всех остальных файлов
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x direct_start.py railway_final.py patch_main.py main.py

# Запуск бота
CMD ["python", "direct_start.py"] 