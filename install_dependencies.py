#!/usr/bin/env python
"""
Скрипт для установки необходимых зависимостей для бота ОНА (Осознанный Наставник и Аналитик)
"""

import sys
import subprocess
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [INSTALLER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("installer")

def install_package(package_name):
    """
    Устанавливает пакет с помощью pip
    """
    logger.info(f"Установка пакета {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Пакет {package_name} успешно установлен")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при установке пакета {package_name}: {e}")
        return False

def main():
    """
    Основная функция для установки зависимостей
    """
    logger.info("Начало установки зависимостей для бота ОНА")
    
    # Создаем директории, если они не существуют
    directories = ["backups", "docs"]
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"Создана директория {directory}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории {directory}: {e}")
    
    # Список основных зависимостей
    dependencies = [
        "aiogram==3.2.0",
        "python-dotenv",
        "psycopg2-binary",
        "pydantic",
        "openai",
        "APScheduler",
        "elevenlabs",
        "gTTS"
    ]
    
    # Устанавливаем зависимости из requirements.txt, если файл существует
    if os.path.exists("requirements.txt"):
        logger.info("Найден файл requirements.txt, установка зависимостей из него...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Зависимости из requirements.txt успешно установлены")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при установке зависимостей из requirements.txt: {e}")
            logger.info("Продолжаем установку основных зависимостей...")
            
            # Устанавливаем основные зависимости одну за другой
            for dependency in dependencies:
                install_package(dependency)
    else:
        logger.warning("Файл requirements.txt не найден, установка основных зависимостей...")
        
        # Устанавливаем основные зависимости одну за другой
        for dependency in dependencies:
            install_package(dependency)
    
    # Проверяем, что psycopg2 установлен
    logger.info("Проверка установки psycopg2...")
    try:
        import psycopg2
        logger.info("Модуль psycopg2 успешно импортирован")
    except ImportError:
        logger.warning("Модуль psycopg2 не установлен, попытка установки psycopg2-binary...")
        install_package("psycopg2-binary")
        
        # Повторная проверка
        try:
            import psycopg2
            logger.info("Модуль psycopg2 успешно импортирован после установки")
        except ImportError:
            logger.error("Не удалось установить psycopg2. Пожалуйста, установите его вручную.")
    
    logger.info("Установка зависимостей завершена")
    
    # Проверяем наличие файла .env
    if not os.path.exists(".env"):
        logger.warning("Файл .env не найден")
        logger.info("Создание примера файла .env...")
        
        # Создаем пример файла .env
        env_example = """# Telegram Bot API ключ (получите у @BotFather)
BOT_TOKEN=your_bot_token_here

# URL подключения к PostgreSQL базе данных (при развертывании на Railway)
# Формат: postgresql://username:password@hostname:port/database_name
DATABASE_URL=postgresql://postgres:password@localhost:5432/ona_bot

# OpenAI API ключ (для генерации текстов)
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API ключ (для генерации голоса)
ELEVEN_TOKEN=your_elevenlabs_token_here
"""
        
        try:
            with open(".env.example", "w") as f:
                f.write(env_example)
            logger.info("Создан файл .env.example")
            logger.info("Пожалуйста, скопируйте его в .env и заполните своими значениями")
        except Exception as e:
            logger.error(f"Ошибка при создании файла .env.example: {e}")
    
    logger.info("")
    logger.info("=== УСТАНОВКА ЗАВЕРШЕНА ===")
    logger.info("Теперь вы можете запустить бота командой:")
    logger.info("python start_bot.py")
    logger.info("")
    logger.info("Перед запуском убедитесь, что:")
    logger.info("1. Файл .env содержит правильные значения")
    logger.info("2. PostgreSQL сервер запущен (если используется)")
    logger.info("")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 