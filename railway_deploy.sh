#!/bin/bash

# ONA Bot Railway Deployment Script
# This script prepares and deploys the ONA bot to Railway

set -e

echo "=== Подготовка к деплою на Railway ==="

# Проверка git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Пожалуйста, установите Git и попробуйте снова."
    exit 1
fi

# Проверка railway CLI
if ! command -v railway &> /dev/null; then
    echo "⚠️ Railway CLI не найден. Хотите установить? (y/n)"
    read -r answer
    if [ "$answer" != "${answer#[Yy]}" ]; then
        echo "Установка Railway CLI..."
        curl -fsSL https://railway.app/install.sh | sh
    else
        echo "⚠️ Вы можете установить Railway CLI позже и запустить скрипт повторно."
        echo "   Инструкции по установке: https://docs.railway.app/develop/cli"
    fi
fi

# Подготовка файлов для Railway
echo "Создание .env файла для Railway..."
if [ ! -f .env ]; then
    echo "BOT_TOKEN=your_bot_token_here" > .env
    echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
    echo "ELEVEN_API_KEY=your_eleven_api_key_here" >> .env
    echo "⚠️ Создан пустой .env файл. Пожалуйста, заполните его своими ключами API."
else
    echo "✅ Файл .env уже существует."
fi

# Проверка и обновление requirements.txt
echo "Проверка requirements.txt..."
if grep -q "openai==1.3.3" requirements.txt; then
    echo "✅ requirements.txt уже содержит правильную версию openai."
else
    # Обновление версии openai в requirements.txt
    if grep -q "openai==" requirements.txt; then
        sed -i 's/openai==.*/openai==1.3.3/g' requirements.txt
        echo "✅ Версия openai в requirements.txt обновлена до 1.3.3."
    else
        echo "openai==1.3.3" >> requirements.txt
        echo "✅ Добавлена зависимость openai==1.3.3 в requirements.txt."
    fi
fi

# Проверка наличия всех необходимых файлов
echo "Проверка наличия всех необходимых файлов для патчинга..."
required_files=("fix_imports_global.py" "modify_site_packages.py" "fix_problem_modules.py" "safe_startup.py" "railway_bootstrap.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️ Отсутствуют следующие файлы:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "Продолжить? (y/n)"
    read -r answer
    if [ "$answer" != "${answer#[Yy]}" ]; then
        echo "Продолжаем..."
    else
        echo "❌ Отмена. Пожалуйста, убедитесь, что все необходимые файлы присутствуют."
        exit 1
    fi
else
    echo "✅ Все необходимые файлы присутствуют."
fi

# Проверка наличия Dockerfile
if [ ! -f Dockerfile ]; then
    echo "⚠️ Dockerfile не найден. Создать автоматически? (y/n)"
    read -r answer
    if [ "$answer" != "${answer#[Yy]}" ]; then
        cat > Dockerfile << 'EOF'
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
EOF
        echo "✅ Dockerfile создан."
    else
        echo "⚠️ Вы можете создать Dockerfile вручную."
    fi
else
    echo "✅ Dockerfile уже существует."
fi

# Проверка git-репозитория
if [ ! -d .git ]; then
    echo "⚠️ Это не git-репозиторий. Инициализировать? (y/n)"
    read -r answer
    if [ "$answer" != "${answer#[Yy]}" ]; then
        git init
        echo "✅ Git-репозиторий инициализирован."
    else
        echo "⚠️ Вы можете инициализировать git-репозиторий позже."
    fi
fi

# Добавление файлов в .gitignore
if [ ! -f .gitignore ]; then
    echo "Создание .gitignore..."
    cat > .gitignore << 'EOF'
# Environments
.env
.venv
env/
venv/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Logs
logs/
*.log

# OS specific
.DS_Store
Thumbs.db
EOF
    echo "✅ .gitignore создан."
else
    echo "✅ .gitignore уже существует."
fi

# Подготовка коммита
echo "Подготовка коммита..."
git add .
git status

echo ""
echo "=== Готово к деплою на Railway ==="
echo ""
echo "Для деплоя на Railway выполните следующие шаги:"
echo "1. Создайте коммит: git commit -m 'Подготовка для Railway'"
echo "2. Создайте новый проект на Railway: railway init"
echo "3. Настройте переменные окружения на Railway: railway vars set BOT_TOKEN=your_bot_token OPENAI_API_KEY=your_openai_key ELEVEN_API_KEY=your_eleven_key"
echo "4. Разверните приложение: railway up"
echo ""
echo "Или используйте web-интерфейс Railway для деплоя из GitHub:"
echo "1. Создайте коммит и отправьте его в GitHub: git push origin main"
echo "2. На https://railway.app создайте новый проект из GitHub"
echo "3. Выберите репозиторий и настройте переменные окружения"
echo ""
echo "Спасибо за использование скрипта подготовки деплоя!" 