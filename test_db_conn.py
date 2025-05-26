#!/usr/bin/env python
"""
Тест подключения к PostgreSQL и создания таблиц
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [TEST] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_db")

# SQL для создания таблиц в PostgreSQL
POSTGRES_CREATE_TABLES_SQL = """
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ответов на вопросы
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER,
    q_code TEXT,
    value TEXT,
    PRIMARY KEY(id, q_code),
    FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица профилей
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица напоминаний
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    cron TEXT NOT NULL,
    message TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

def test_postgres_connection():
    """
    Проверяет подключение к PostgreSQL и создает таблицы
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем тестовый DATABASE_URL для демонстрации
    test_database_url = os.environ.get('DATABASE_URL')
    if not test_database_url:
        # Создаем временный тестовый URL только для демонстрации
        test_database_url = "postgresql://postgres:postgres@localhost:5432/postgres"
        logger.warning(f"DATABASE_URL не найден, используем тестовый URL для демонстрации: {test_database_url}")
        
        # Устанавливаем переменную окружения, чтобы её могли использовать другие модули
        os.environ['DATABASE_URL'] = test_database_url
    
    logger.info(f"Тестируем подключение к PostgreSQL с URL: {test_database_url}")
    
    try:
        # Пытаемся подключиться к PostgreSQL
        conn = psycopg2.connect(test_database_url)
        logger.info("✅ Подключение к PostgreSQL успешно установлено")
        
        # Создаем таблицы
        with conn.cursor() as cursor:
            logger.info("Создаем таблицы в PostgreSQL...")
            cursor.execute(POSTGRES_CREATE_TABLES_SQL)
            conn.commit()
            logger.info("✅ Таблицы успешно созданы")
        
        # Проверяем созданные таблицы
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            if tables:
                logger.info(f"Таблицы в базе данных: {', '.join([t[0] for t in tables])}")
            else:
                logger.warning("Таблицы не найдены в базе данных")
        
        conn.close()
        logger.info("Подключение к PostgreSQL закрыто")
        return True
    
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
        logger.error("Убедитесь, что PostgreSQL сервер запущен и URL подключения корректен")
        return False
    
    except Exception as e:
        logger.error(f"❌ Ошибка при работе с PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    if success:
        logger.info("✅ Тест подключения к PostgreSQL и создания таблиц успешно завершен")
        sys.exit(0)
    else:
        logger.error("❌ Тест подключения к PostgreSQL не пройден")
        sys.exit(1) 