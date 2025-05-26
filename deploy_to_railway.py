#!/usr/bin/env python3
"""
Скрипт для подготовки и деплоя бота на Railway с обеспечением совместимости AsyncOpenAI.
Этот скрипт автоматизирует процесс подготовки и деплоя на Railway.
"""
import os
import sys
import shutil
import platform
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("deploy_to_railway")

# Список необходимых файлов для деплоя
REQUIRED_FILES = [
    "fix_imports_global.py",
    "modify_site_packages.py",
    "fix_problem_modules.py",
    "safe_startup.py",
    "railway_bootstrap.py",
    "railway_bootstrap.sh",
    "main.py",
    "requirements.txt",
    "Dockerfile"
]

# Содержимое requirements.txt с правильной версией openai
REQUIREMENTS_CONTENT = """aiogram==3.0.0
python-dotenv==1.0.0
APScheduler==3.10.4
pydantic==2.1.1
requests==2.31.0
openai==1.3.3
httpx==0.23.3
elevenlabs==0.2.24
gTTS==2.3.2
ephem==4.1.4
PyYAML==6.0.1
postgrest-py==0.10.3
realtime-py==0.1.2
storage3==0.5.0
supafunc==0.2.2
"""

# Содержимое Dockerfile
DOCKERFILE_CONTENT = """FROM python:3.11-slim

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
"""

def check_railway_cli():
    """Проверяет наличие Railway CLI"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run("where railway", shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run("which railway", shell=True, capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception:
        return False

def check_git():
    """Проверяет наличие Git"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def check_required_files():
    """Проверяет наличие всех необходимых файлов"""
    missing_files = []
    
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def create_requirements_txt():
    """Создает или обновляет requirements.txt"""
    try:
        # Сначала создаем резервную копию, если файл существует
        if os.path.exists("requirements.txt"):
            shutil.copy2("requirements.txt", "requirements.txt.bak")
            logger.info("Создана резервная копия requirements.txt.bak")
        
        # Записываем содержимое с правильной версией openai
        with open("requirements.txt", "w") as f:
            f.write(REQUIREMENTS_CONTENT)
        
        logger.info("Создан/обновлен файл requirements.txt с openai==1.3.3")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании requirements.txt: {e}")
        return False

def create_dockerfile():
    """Создает Dockerfile"""
    try:
        # Сначала создаем резервную копию, если файл существует
        if os.path.exists("Dockerfile"):
            shutil.copy2("Dockerfile", "Dockerfile.bak")
            logger.info("Создана резервная копия Dockerfile.bak")
        
        # Записываем содержимое Dockerfile
        with open("Dockerfile", "w") as f:
            f.write(DOCKERFILE_CONTENT)
        
        logger.info("Создан/обновлен файл Dockerfile")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании Dockerfile: {e}")
        return False

def git_init_if_needed():
    """Инициализирует Git репозиторий, если он не существует"""
    if not os.path.exists(".git"):
        try:
            subprocess.run(["git", "init"], check=True)
            logger.info("Инициализирован Git репозиторий")
            return True
        except Exception as e:
            logger.error(f"Ошибка при инициализации Git репозитория: {e}")
            return False
    else:
        logger.info("Git репозиторий уже существует")
        return True

def create_gitignore():
    """Создает .gitignore файл"""
    try:
        # Проверяем, существует ли уже файл
        if os.path.exists(".gitignore"):
            logger.info("Файл .gitignore уже существует")
            return True
        
        # Создаем .gitignore с типичным содержимым для Python проектов
        with open(".gitignore", "w") as f:
            f.write("""# Environments
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
""")
        
        logger.info("Создан файл .gitignore")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании .gitignore: {e}")
        return False

def create_env_sample():
    """Создает пример .env файла"""
    try:
        # Проверяем, существует ли уже файл
        if os.path.exists(".env.sample"):
            logger.info("Файл .env.sample уже существует")
            return True
        
        # Создаем .env.sample с примерами переменных окружения
        with open(".env.sample", "w") as f:
            f.write("""# Telegram Bot Token from BotFather
BOT_TOKEN=your_bot_token_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Key (for voice features)
ELEVEN_API_KEY=your_elevenlabs_api_key_here
""")
        
        logger.info("Создан файл .env.sample")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании .env.sample: {e}")
        return False

def prepare_for_railway():
    """Подготавливает проект к деплою на Railway"""
    logger.info("=== Начало подготовки к деплою на Railway ===")
    
    # Проверяем наличие Git
    if not check_git():
        logger.error("Git не установлен. Пожалуйста, установите Git и попробуйте снова.")
        return False
    
    # Проверяем наличие Railway CLI
    if not check_railway_cli():
        logger.warning("Railway CLI не найден. Рекомендуется установить Railway CLI для деплоя.")
    
    # Проверяем наличие всех необходимых файлов
    missing_files = check_required_files()
    if missing_files:
        logger.warning(f"Отсутствуют следующие файлы: {', '.join(missing_files)}")
        
        # Создаем файлы по умолчанию, если это возможно
        for file in missing_files:
            if file == "requirements.txt":
                create_requirements_txt()
            elif file == "Dockerfile":
                create_dockerfile()
            else:
                logger.error(f"Не удается автоматически создать файл {file}")
    else:
        logger.info("Все необходимые файлы присутствуют")
    
    # Создаем/обновляем requirements.txt
    create_requirements_txt()
    
    # Создаем/обновляем Dockerfile
    create_dockerfile()
    
    # Инициализируем Git репозиторий, если нужно
    git_init_if_needed()
    
    # Создаем .gitignore
    create_gitignore()
    
    # Создаем .env.sample
    create_env_sample()
    
    # Добавляем файлы в Git
    try:
        subprocess.run(["git", "add", "."], check=True)
        logger.info("Файлы добавлены в Git")
    except Exception as e:
        logger.error(f"Ошибка при добавлении файлов в Git: {e}")
    
    logger.info("=== Подготовка к деплою на Railway завершена ===")
    
    # Выводим инструкции для пользователя
    print("\nДля деплоя на Railway выполните следующие шаги:")
    print("1. Создайте коммит: git commit -m 'Подготовка для Railway'")
    print("2. Создайте новый проект на Railway: railway init")
    print("3. Настройте переменные окружения на Railway:")
    print("   railway vars set BOT_TOKEN=your_bot_token OPENAI_API_KEY=your_openai_key ELEVEN_API_KEY=your_eleven_key")
    print("4. Разверните приложение: railway up")
    print("\nИли используйте web-интерфейс Railway для деплоя из GitHub:")
    print("1. Создайте коммит и отправьте его в GitHub: git push origin main")
    print("2. На https://railway.app создайте новый проект из GitHub")
    print("3. Выберите репозиторий и настройте переменные окружения")
    
    return True

def main():
    """Основная функция скрипта"""
    prepare_for_railway()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 