#!/usr/bin/env python
"""
Скрипт инициализации PostgreSQL для бота ОНА (Осознанный Наставник и Аналитик)
Создает необходимые таблицы в PostgreSQL базе данных
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POSTGRES_INIT] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_init")

# SQL для создания таблиц в PostgreSQL
POSTGRES_CREATE_TABLES_SQL = """
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ответов пользователей
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER NOT NULL,
    q_code TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (id, q_code),
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица профилей пользователей
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица напоминаний
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    cron TEXT NOT NULL,
    message TEXT NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Индексы для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
CREATE INDEX IF NOT EXISTS idx_answers_id ON answers(id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
"""

def init_postgres():
    """
    Инициализирует PostgreSQL базу данных - создает необходимые таблицы
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем URL базы данных
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная DATABASE_URL не найдена в .env или переменных окружения")
        return False
    
    logger.info(f"Подключение к PostgreSQL базе данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        
        # Создаем таблицы
        with conn.cursor() as cursor:
            logger.info("Создание необходимых таблиц...")
            cursor.execute(POSTGRES_CREATE_TABLES_SQL)
        
        # Фиксируем изменения
        conn.commit()
        logger.info("Таблицы успешно созданы в PostgreSQL")
        
        # Проверяем созданные таблицы
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            logger.info(f"Таблицы в базе данных: {', '.join(table_names)}")
            
            # Проверяем наличие необходимых таблиц
            required_tables = ['users', 'answers', 'profiles', 'reminders']
            missing_tables = [table for table in required_tables if table not in table_names]
            
            if missing_tables:
                logger.error(f"Не удалось создать следующие таблицы: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("Все необходимые таблицы успешно созданы")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации PostgreSQL: {e}")
        
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
                    logger.error("DATABASE_URL должен начинаться с 'postgresql://' или 'postgres://'")
        
        return False

if __name__ == "__main__":
    logger.info("Запуск инициализации PostgreSQL...")
    success = init_postgres()
    
    if success:
        logger.info("Инициализация PostgreSQL успешно завершена")
        sys.exit(0)
    else:
        logger.error("Инициализация PostgreSQL завершилась с ошибкой")
        sys.exit(1) 