#!/usr/bin/env python
"""
Скрипт для проверки соединения с PostgreSQL
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [DB_TEST] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("pg_test")

# Загружаем переменные окружения
load_dotenv()

async def test_postgres_connection():
    """
    Проверяет соединение с PostgreSQL и наличие таблиц
    """
    # Проверяем наличие DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная окружения DATABASE_URL не найдена!")
        logger.error("Установите DATABASE_URL с вашей строкой подключения PostgreSQL")
        return False
    
    logger.info(f"Найдена переменная DATABASE_URL: {database_url[:20]}...")
    
    try:
        # Пробуем импортировать psycopg2
        try:
            import psycopg2
            import psycopg2.extras
            logger.info("Библиотека psycopg2 найдена")
        except ImportError:
            logger.error("Библиотека psycopg2 не установлена!")
            logger.error("Установите psycopg2: pip install psycopg2-binary")
            return False
        
        # Проверяем соединение напрямую через psycopg2
        logger.info("Проверка соединения с PostgreSQL...")
        try:
            conn = psycopg2.connect(database_url)
            logger.info("Соединение с PostgreSQL установлено успешно!")
            
            # Проверяем наличие таблиц
            with conn.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                
                if not tables:
                    logger.warning("В базе данных нет таблиц!")
                    logger.warning("Необходимо запустить инициализацию: python init_postgres.py")
                else:
                    table_names = [table[0] for table in tables]
                    logger.info(f"Обнаружены таблицы: {', '.join(table_names)}")
                    
                    # Проверяем, есть ли все необходимые таблицы
                    required_tables = ['users', 'answers', 'profiles', 'reminders']
                    missing_tables = [table for table in required_tables if table not in table_names]
                    
                    if missing_tables:
                        logger.warning(f"Отсутствуют таблицы: {', '.join(missing_tables)}")
                        logger.warning("Необходимо запустить инициализацию: python init_postgres.py")
                    else:
                        logger.info("Все необходимые таблицы присутствуют в базе данных")
                        
                        # Проверяем количество записей в таблицах
                        for table in required_tables:
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                logger.info(f"Таблица {table}: {count} записей")
                            except Exception as e:
                                logger.error(f"Ошибка при проверке таблицы {table}: {e}")
            
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"Ошибка соединения с PostgreSQL: {e}")
            
            # Проверяем распространенные проблемы
            error_str = str(e)
            if "could not connect to server" in error_str:
                logger.error("Не удалось подключиться к серверу PostgreSQL")
                logger.error("Проверьте, что сервер запущен и доступен")
            elif "password authentication failed" in error_str:
                logger.error("Ошибка аутентификации: неверный пароль")
                logger.error("Проверьте правильность строки подключения DATABASE_URL")
            elif "database" in error_str and "does not exist" in error_str:
                logger.error("Указанная база данных не существует")
                logger.error("Проверьте имя базы данных в строке подключения")
            elif "SSL" in error_str:
                logger.error("Проблема с SSL-соединением")
                logger.error("Попробуйте добавить ?sslmode=require к строке подключения")
            
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Основная функция для запуска проверки соединения
    """
    logger.info("Запуск проверки соединения с PostgreSQL...")
    
    # Запускаем асинхронную функцию
    success = asyncio.run(test_postgres_connection())
    
    if success:
        logger.info("Проверка соединения с PostgreSQL завершена успешно!")
        return 0
    else:
        logger.error("Проверка соединения с PostgreSQL завершилась с ошибками")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 