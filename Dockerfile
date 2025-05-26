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

# Копируем сначала критические файлы для патчинга
COPY pre_import_fix.py patch_main.py fix_imports_global.py modify_site_packages.py fix_problem_modules.py ./

# Проверяем версию openai и наличие AsyncOpenAI
RUN pip show openai && python -c "import pre_import_fix; from openai import AsyncOpenAI; print('AsyncOpenAI доступен')" || echo "AsyncOpenAI недоступен, будут использованы патчи"

# Копируем остальные файлы
COPY . .

# Make the startup script executable
RUN chmod +x railway_start.sh

# Запускаем бота с нашим скриптом запуска
CMD ["./railway_start.sh"] 