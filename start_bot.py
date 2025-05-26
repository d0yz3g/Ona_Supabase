#!/usr/bin/env python
"""
Скрипт для запуска бота с предварительной проверкой версии aiogram
и инициализацией базы данных PostgreSQL
"""

import sys
import os
import logging
import subprocess
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [STARTER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("bot_starter")

# Проверка режима работы (webhook или polling)
WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "false").lower() in ("true", "1", "yes")

def check_postgres_initialization():
    """
    Проверяет и инициализирует базу данных PostgreSQL, если она используется
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.info("Переменная DATABASE_URL не найдена, используется SQLite")
        return True
    
    logger.info(f"Обнаружена переменная DATABASE_URL, проверка базы данных PostgreSQL...")
    
    # Проверяем наличие psycopg2-binary
    try:
        import psycopg2
        logger.info("Модуль psycopg2 успешно импортирован")
    except ImportError:
        logger.error("Не найден модуль psycopg2, требуется для работы с PostgreSQL")
        logger.error("Установка psycopg2-binary...")
        
        try:
            # Пытаемся установить psycopg2-binary
            subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
            logger.info("psycopg2-binary успешно установлен")
            
            # Пытаемся снова импортировать psycopg2
            import psycopg2
            logger.info("Модуль psycopg2 успешно импортирован после установки")
        except Exception as e:
            logger.error(f"Ошибка при установке psycopg2-binary: {e}")
            logger.warning("Продолжаем запуск бота с использованием SQLite вместо PostgreSQL")
            # Устанавливаем временную переменную, чтобы бот использовал SQLite
            os.environ.pop("DATABASE_URL", None)
            return True
    
    # Проверяем наличие файла ensure_postgres.py для нового подхода
    if os.path.exists("ensure_postgres.py"):
        logger.info("Используем ensure_postgres.py для настройки PostgreSQL...")
        
        try:
            # Запускаем ensure_postgres.py
            result = subprocess.run(
                [sys.executable, "ensure_postgres.py"], 
                capture_output=True, 
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("PostgreSQL успешно настроен через ensure_postgres.py")
                return True
            else:
                logger.warning(f"Настройка PostgreSQL через ensure_postgres.py завершилась с ошибкой (код {result.returncode})")
                logger.warning(f"Вывод: {result.stdout}")
                logger.error(f"Ошибки: {result.stderr}")
                
                # Пробуем запустить init_postgres.py как запасной вариант
                if os.path.exists("init_postgres.py"):
                    logger.info("Пробуем использовать init_postgres.py в качестве запасного варианта...")
                    return _use_init_postgres()
                else:
                    logger.warning("init_postgres.py не найден, продолжаем без PostgreSQL")
                    os.environ.pop("DATABASE_URL", None)
                    return True
        except Exception as e:
            logger.error(f"Ошибка при запуске ensure_postgres.py: {e}")
            
            # Пробуем запустить init_postgres.py как запасной вариант
            if os.path.exists("init_postgres.py"):
                logger.info("Пробуем использовать init_postgres.py в качестве запасного варианта...")
                return _use_init_postgres()
            else:
                logger.warning("init_postgres.py не найден, продолжаем без PostgreSQL")
                os.environ.pop("DATABASE_URL", None)
                return True
    elif os.path.exists("init_postgres.py"):
        # Если ensure_postgres.py отсутствует, но есть init_postgres.py
        logger.info("ensure_postgres.py не найден, используем init_postgres.py...")
        return _use_init_postgres()
    else:
        logger.warning("Ни ensure_postgres.py, ни init_postgres.py не найдены, пропускаем инициализацию PostgreSQL")
        os.environ.pop("DATABASE_URL", None)
        return True

def _use_init_postgres():
    """
    Вспомогательная функция для использования init_postgres.py
    """
    try:
        result = subprocess.run(
            [sys.executable, "init_postgres.py"], 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Инициализация PostgreSQL через init_postgres.py успешно завершена")
            return True
        else:
            logger.warning(f"Инициализация PostgreSQL через init_postgres.py завершилась с ошибкой (код {result.returncode})")
            logger.warning(f"Вывод: {result.stdout}")
            logger.error(f"Ошибки: {result.stderr}")
            
            # Продолжаем работу с SQLite вместо PostgreSQL
            logger.warning("Продолжаем запуск бота с использованием SQLite вместо PostgreSQL")
            os.environ.pop("DATABASE_URL", None)
            return True
    except Exception as e:
        logger.error(f"Ошибка при запуске init_postgres.py: {e}")
        logger.warning("Продолжаем запуск бота с использованием SQLite вместо PostgreSQL")
        os.environ.pop("DATABASE_URL", None)
        return True

def setup_webhook():
    """
    Настраивает webhook для бота, если выбран режим webhook
    
    Returns:
        bool: True если webhook успешно настроен или не требуется, False в противном случае
    """
    if not WEBHOOK_MODE:
        logger.info("Режим webhook не активирован, пропускаем настройку webhook")
        return True
    
    logger.info("Настройка webhook...")
    
    # Проверяем наличие файла webhook_setup.py
    if not os.path.exists("webhook_setup.py"):
        logger.error("Файл webhook_setup.py не найден")
        return False
    
    # Запускаем скрипт настройки webhook
    try:
        result = subprocess.run(
            [sys.executable, "webhook_setup.py"], 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Webhook успешно настроен")
            return True
        else:
            logger.warning(f"Настройка webhook завершилась с ошибкой (код {result.returncode})")
            logger.warning(f"Вывод: {result.stdout}")
            logger.error(f"Ошибки: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при настройке webhook: {e}")
        return False

def main():
    """
    Основная функция для запуска бота с проверкой совместимости
    """
    logger.info("Запуск бота с проверкой совместимости версии aiogram и инициализацией базы данных")
    logger.info(f"Режим работы: {'webhook' if WEBHOOK_MODE else 'polling'}")
    
    # Инициализируем PostgreSQL, если она используется
    if not check_postgres_initialization():
        logger.error("Не удалось инициализировать PostgreSQL")
        return 1
    
    # Проверяем наличие файла проверки версии aiogram
    if not os.path.exists("check_aiogram_version.py"):
        logger.error("Файл check_aiogram_version.py не найден")
        return 1
    
    # Запускаем скрипт проверки версии aiogram
    logger.info("Запуск проверки версии aiogram...")
    try:
        subprocess.run([sys.executable, "check_aiogram_version.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при проверке версии aiogram: {e}")
        return 1
    
    # Настраиваем webhook, если выбран режим webhook
    if WEBHOOK_MODE:
        if not setup_webhook():
            logger.error("Не удалось настроить webhook")
            return 1
        
        # Запускаем webhook сервер
        logger.info("Запуск webhook сервера...")
        try:
            if os.path.exists("webhook_server.py"):
                subprocess.run([sys.executable, "webhook_server.py"], check=True)
            else:
                logger.error("Файл webhook_server.py не найден")
                return 1
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при запуске webhook сервера: {e}")
            return 1
    else:
        # Запускаем основной скрипт в режиме polling
        logger.info("Запуск основного скрипта main.py в режиме polling...")
        try:
            subprocess.run([sys.executable, "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при запуске main.py: {e}")
            return 1
    
    logger.info("Бот успешно завершил работу")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 