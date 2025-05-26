FROM python:3.11-slim

WORKDIR /app

# Установка базовых зависимостей более лаконично
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование файла с зависимостями
COPY requirements.txt .

# Обновление pip и установка критических зависимостей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir python-dotenv==1.0.0 httpx==0.23.3 openai==1.3.3 pydantic==2.1.1 aiogram==3.0.0 && \
    pip install --no-cache-dir -r requirements.txt || echo "Некоторые пакеты не установлены, продолжаем"

# Копирование скриптов исправления импортов
COPY fix_imports_global.py pre_import_fix.py direct_start.py patch_main.py ./

# Копирование всех остальных файлов
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x *.py

# Проверка версии OpenAI (не блокирует сборку при ошибке)
RUN pip show openai || echo "OpenAI не установлен" && \
    python -c "import openai; print('OpenAI версия:', openai.__version__)" || echo "Не удалось проверить версию OpenAI"

# Запуск бота
CMD ["python", "direct_start.py"] 