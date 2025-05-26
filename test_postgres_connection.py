#!/usr/bin/env python
"""
Скрипт для тестирования подключения к PostgreSQL и проверки состояния таблиц
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POSTGRES_TEST] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_test")

def test_postgres_connection():
    """
    Тестирует подключение к PostgreSQL и проверяет наличие таблиц
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем URL базы данных
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная DATABASE_URL не найдена в .env или переменных окружения")
        return False
    
    logger.info(f"Тестирование подключения к PostgreSQL базе данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        logger.info("✅ Подключение к PostgreSQL успешно установлено")
        
        # Проверяем наличие таблиц
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            
            # Извлекаем имена таблиц
            table_names = [table[0] for table in tables]
            logger.info(f"Таблицы в базе данных: {', '.join(table_names) if table_names else 'таблицы отсутствуют'}")
            
            # Проверяем наличие необходимых таблиц
            required_tables = ['users', 'answers', 'profiles', 'reminders']
            missing_tables = [table for table in required_tables if table not in table_names]
            
            if missing_tables:
                logger.warning(f"❌ Отсутствуют таблицы: {', '.join(missing_tables)}")
                logger.info("Рекомендуется запустить init_postgres.py для создания таблиц")
            else:
                logger.info("✅ Все необходимые таблицы присутствуют")
                
                # Проверяем структуру таблиц
                for table in required_tables:
                    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                    columns = cursor.fetchall()
                    logger.info(f"Структура таблицы {table}:")
                    for column in columns:
                        logger.info(f"  - {column[0]}: {column[1]}")
        
        # Проверяем версию PostgreSQL
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"Версия PostgreSQL: {version}")
        
        # Закрываем соединение
        conn.close()
        logger.info("Соединение с PostgreSQL закрыто")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при подключении к PostgreSQL: {e}")
        
        # Более подробная диагностика для psycopg2.OperationalError
        if isinstance(e, psycopg2.OperationalError):
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            logger.error("Проверьте правильность DATABASE_URL и доступность сервера PostgreSQL")
            
            # Проверка формата DATABASE_URL
            if database_url:
                # Маскируем пароль для логирования
                masked_url = database_url
                if "://" in database_url and "@" in database_url:
                    parts = database_url.split("@")
                    auth_parts = parts[0].split("://")
                    if len(auth_parts) > 1:
                        protocol = auth_parts[0]
                        if ":" in auth_parts[1]:
                            username = auth_parts[1].split(":")[0]
                            masked_url = f"{protocol}://{username}:***@{parts[1]}"
                
                logger.info(f"Используемый формат DATABASE_URL: {masked_url}")
                
                # Проверка на наличие корректного формата
                if not database_url.startswith(("postgresql://", "postgres://")):
                    logger.error("❌ DATABASE_URL должен начинаться с 'postgresql://' или 'postgres://'")
                    
                # Проверка доступности хоста
                if "@" in database_url and "/" in database_url.split("@")[1]:
                    host_part = database_url.split("@")[1].split("/")[0]
                    host = host_part.split(":")[0] if ":" in host_part else host_part
                    
                    logger.info(f"Проверка доступности хоста PostgreSQL: {host}")
                    import socket
                    try:
                        # Пытаемся подключиться к хосту на порт PostgreSQL (по умолчанию 5432)
                        port = int(host_part.split(":")[1]) if ":" in host_part else 5432
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        result = sock.connect_ex((host, port))
                        if result == 0:
                            logger.info(f"✅ Хост {host}:{port} доступен")
                        else:
                            logger.error(f"❌ Хост {host}:{port} недоступен (код ошибки: {result})")
                        sock.close()
                    except Exception as se:
                        logger.error(f"❌ Ошибка при проверке доступности хоста: {se}")
        
        return False

if __name__ == "__main__":
    logger.info("Запуск теста подключения к PostgreSQL...")
    success = test_postgres_connection()
    
    if success:
        logger.info("✅ Тест подключения к PostgreSQL успешно завершен")
        sys.exit(0)
    else:
        logger.error("❌ Тест подключения к PostgreSQL завершился с ошибкой")
        sys.exit(1) 