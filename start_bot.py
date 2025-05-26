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

def check_postgres_initialization():
    """
    Проверяет и инициализирует базу данных PostgreSQL, если она используется
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.info("Переменная DATABASE_URL не найдена, используется SQLite")
        return True
    
    logger.info(f"Обнаружена переменная DATABASE_URL, проверка базы данных PostgreSQL...")
    
    # Проверяем наличие файла инициализации
    if not os.path.exists("init_postgres.py"):
        logger.warning("Файл init_postgres.py не найден, пропускаем инициализацию PostgreSQL")
        return True
    
    # Проверяем таблицы в PostgreSQL
    try:
        import psycopg2
        import psycopg2.extras
        
        # Проверяем наличие таблиц
        try:
            logger.info("Проверка наличия таблиц в PostgreSQL...")
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                
                # Извлекаем имена таблиц
                table_names = [table[0] for table in tables]
                
                # Проверяем наличие необходимых таблиц
                required_tables = ['users', 'answers', 'profiles', 'reminders']
                missing_tables = [table for table in required_tables if table not in table_names]
                
                if missing_tables:
                    logger.warning(f"В базе данных отсутствуют таблицы: {', '.join(missing_tables)}")
                    logger.warning("Требуется инициализация базы данных PostgreSQL")
                    
                    # Запускаем инициализацию PostgreSQL
                    logger.info("Запуск автоматической инициализации PostgreSQL...")
                    result = subprocess.run(
                        [sys.executable, "init_postgres.py"], 
                        capture_output=True, 
                        text=True,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        logger.info("Автоматическая инициализация PostgreSQL успешно завершена")
                    else:
                        logger.warning(f"Автоматическая инициализация PostgreSQL завершилась с ошибкой (код {result.returncode})")
                        logger.warning(f"Вывод: {result.stdout}")
                        logger.error(f"Ошибки: {result.stderr}")
                else:
                    logger.info(f"Обнаружены все необходимые таблицы в PostgreSQL: {', '.join(required_tables)}")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке таблиц в PostgreSQL: {e}")
            
            # Запускаем скрипт инициализации PostgreSQL
            logger.info("Запуск инициализации PostgreSQL...")
            result = subprocess.run(
                [sys.executable, "init_postgres.py"], 
                capture_output=True, 
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Инициализация PostgreSQL успешно завершена")
                return True
            else:
                logger.warning(f"Инициализация PostgreSQL завершилась с ошибкой (код {result.returncode})")
                logger.warning(f"Вывод: {result.stdout}")
                logger.error(f"Ошибки: {result.stderr}")
                
                # Продолжаем работу, даже если инициализация не удалась
                logger.info("Продолжаем запуск бота, несмотря на ошибки инициализации PostgreSQL")
                return True
    except ImportError:
        logger.error("Не найден модуль psycopg2, требуется для работы с PostgreSQL")
        logger.error("Установите его командой: pip install psycopg2-binary")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске инициализации PostgreSQL: {e}")
        # Продолжаем работу, даже если инициализация не удалась
        return True

def main():
    """
    Основная функция для запуска бота с проверкой совместимости
    """
    logger.info("Запуск бота с проверкой совместимости версии aiogram и инициализацией базы данных")
    
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
    
    # Запускаем основной скрипт
    logger.info("Запуск основного скрипта main.py...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при запуске main.py: {e}")
        return 1
    
    logger.info("Бот успешно завершил работу")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 