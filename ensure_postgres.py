#!/usr/bin/env python
"""
Скрипт для проверки и настройки PostgreSQL подключения для бота ОНА

Этот скрипт:
1. Проверяет наличие переменной окружения DATABASE_URL
2. Если она есть, проверяет подключение к PostgreSQL
3. Если подключение успешно, проверяет наличие необходимых таблиц
4. Если таблиц нет, создает их
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POSTGRES_SETUP] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_setup")

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

-- Индексы для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
CREATE INDEX IF NOT EXISTS idx_answers_id ON answers(id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
"""

def ensure_postgres():
    """
    Проверяет и настраивает подключение к PostgreSQL
    
    Returns:
        bool: True если PostgreSQL настроен и готов к использованию, False в противном случае
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие переменной DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.warning("Переменная DATABASE_URL не найдена. PostgreSQL не будет использоваться.")
        return False
    
    logger.info(f"Найдена переменная DATABASE_URL. Проверяем подключение к PostgreSQL...")
    
    try:
        # Импортируем psycopg2 только если нужно
        import psycopg2
        import psycopg2.extras
        
        # Пытаемся подключиться к PostgreSQL
        conn = psycopg2.connect(database_url)
        logger.info("✅ Подключение к PostgreSQL успешно установлено")
        
        # Создаем таблицы
        with conn.cursor() as cursor:
            logger.info("Создаем таблицы в PostgreSQL...")
            cursor.execute(POSTGRES_CREATE_TABLES_SQL)
            conn.commit()
            logger.info("✅ Таблицы успешно созданы или уже существуют")
        
        # Проверяем созданные таблицы
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]
            
            logger.info(f"Таблицы в базе данных: {', '.join(table_names)}")
            
            # Проверяем наличие необходимых таблиц
            required_tables = ['users', 'answers', 'profiles', 'reminders']
            missing_tables = [t for t in required_tables if t not in table_names]
            
            if missing_tables:
                logger.error(f"❌ Отсутствуют таблицы: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("✅ Все необходимые таблицы присутствуют")
        
        # Закрываем соединение
        conn.close()
        logger.info("✅ PostgreSQL настроен и готов к использованию")
        return True
        
    except ImportError:
        logger.error("❌ Ошибка импорта psycopg2. Установите пакет: pip install psycopg2-binary")
        return False
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
        logger.error("Убедитесь, что PostgreSQL сервер запущен и URL подключения корректен")
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск проверки и настройки PostgreSQL...")
    
    success = ensure_postgres()
    
    if success:
        logger.info("✅ PostgreSQL успешно настроен и готов к использованию")
        sys.exit(0)
    else:
        logger.error("❌ Не удалось настроить PostgreSQL")
        sys.exit(1) 