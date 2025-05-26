#!/usr/bin/env python
"""
Скрипт для инициализации таблиц в PostgreSQL
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [DB_INIT] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("db_init")

# Загружаем переменные окружения
load_dotenv()

async def init_database():
    """
    Инициализирует базу данных PostgreSQL, создавая необходимые таблицы
    """
    # Проверяем наличие DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная окружения DATABASE_URL не найдена!")
        logger.error("Установите DATABASE_URL с вашей строкой подключения PostgreSQL")
        return False
    
    logger.info(f"Найдена переменная DATABASE_URL: {database_url[:20]}...")
    
    try:
        # Импортируем класс Database из модуля db_postgres
        from db_postgres import Database
        logger.info("Импортирован модуль db_postgres")
        
        # Получаем экземпляр базы данных
        db = Database()
        logger.info("Создан экземпляр Database")
        
        # Принудительно создаем таблицы
        if hasattr(db, '_create_postgres_tables'):
            logger.info("Принудительное создание таблиц в PostgreSQL...")
            # Используем приватный метод для создания таблиц
            await db._create_postgres_tables()
            logger.info("Таблицы в PostgreSQL успешно созданы!")
        else:
            logger.error("Метод _create_postgres_tables не найден в классе Database")
            return False
        
        # Проверяем, что таблицы действительно созданы
        try:
            # Подключаемся к базе данных напрямую через psycopg2
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                
                table_names = [table[0] for table in tables]
                logger.info(f"Обнаружены таблицы в базе данных: {', '.join(table_names)}")
                
                if 'users' in table_names and 'answers' in table_names and 'profiles' in table_names and 'reminders' in table_names:
                    logger.info("Все необходимые таблицы созданы успешно!")
                else:
                    logger.warning("Не все необходимые таблицы были созданы.")
                    missing = set(['users', 'answers', 'profiles', 'reminders']) - set(table_names)
                    logger.warning(f"Отсутствуют таблицы: {', '.join(missing)}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка при проверке созданных таблиц: {e}")
        
        # Создаем тестового пользователя для проверки
        logger.info("Создание тестового пользователя для проверки...")
        user_id = await db.get_or_create_user(
            tg_id=12345678, 
            username="test_railway", 
            first_name="Railway", 
            last_name="Test"
        )
        logger.info(f"Тестовый пользователь создан с ID: {user_id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Основная функция для запуска инициализации базы данных
    """
    logger.info("Запуск инициализации базы данных PostgreSQL...")
    
    # Запускаем асинхронную функцию
    success = asyncio.run(init_database())
    
    if success:
        logger.info("Инициализация базы данных PostgreSQL завершена успешно!")
        return 0
    else:
        logger.error("Не удалось инициализировать базу данных PostgreSQL.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 