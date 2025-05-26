#!/usr/bin/env python
"""
Скрипт для создания резервной копии базы данных PostgreSQL
"""

import os
import sys
import logging
import json
import datetime
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [DB_BACKUP] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("db_backup")

# Загружаем переменные окружения
load_dotenv()

async def backup_database():
    """
    Создает резервную копию базы данных PostgreSQL
    """
    # Проверяем наличие DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная окружения DATABASE_URL не найдена!")
        logger.error("Установите DATABASE_URL с вашей строкой подключения PostgreSQL")
        return False
    
    logger.info(f"Найдена переменная DATABASE_URL")
    
    try:
        # Импортируем Database из db_postgres.py
        from db_postgres import Database
        logger.info("Импортирован модуль db_postgres")
        
        # Получаем экземпляр базы данных
        db = Database()
        logger.info("Создан экземпляр Database")
        
        # Создаем директорию для бэкапов, если она не существует
        backup_dir = os.path.join(os.getcwd(), "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Директория для бэкапов: {backup_dir}")
        
        # Генерируем имя файла для бэкапа
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"pg_backup_{timestamp}.json")
        
        logger.info("Получение данных из базы данных...")
        
        # Получаем всех пользователей
        logger.info("Получение списка пользователей...")
        users_query = "SELECT id, tg_id, username, first_name, last_name, created_at FROM users"
        users = await db.fetch_dict_all(users_query, ())
        logger.info(f"Получено {len(users)} пользователей")
        
        # Получаем все ответы
        logger.info("Получение ответов пользователей...")
        answers_query = "SELECT id, q_code, value FROM answers"
        answers = await db.fetch_dict_all(answers_query, ())
        logger.info(f"Получено {len(answers)} ответов")
        
        # Получаем все профили
        logger.info("Получение профилей пользователей...")
        profiles_query = "SELECT id, user_id, data, created_at FROM profiles"
        profiles = await db.fetch_dict_all(profiles_query, ())
        logger.info(f"Получено {len(profiles)} профилей")
        
        # Получаем все напоминания
        logger.info("Получение напоминаний...")
        reminders_query = "SELECT id, user_id, cron, message, active, created_at FROM reminders"
        reminders = await db.fetch_dict_all(reminders_query, ())
        logger.info(f"Получено {len(reminders)} напоминаний")
        
        # Создаем словарь с данными для бэкапа
        backup_data = {
            "backup_date": datetime.datetime.now().isoformat(),
            "database_type": "PostgreSQL",
            "users": users,
            "answers": answers,
            "profiles": profiles,
            "reminders": reminders
        }
        
        # Сохраняем данные в JSON-файл
        logger.info(f"Сохранение данных в файл {backup_file}...")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Резервная копия успешно создана: {backup_file}")
        
        # Выводим статистику
        logger.info(f"Статистика бэкапа:")
        logger.info(f"- Пользователей: {len(users)}")
        logger.info(f"- Ответов: {len(answers)}")
        logger.info(f"- Профилей: {len(profiles)}")
        logger.info(f"- Напоминаний: {len(reminders)}")
        
        return backup_file
    
    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Основная функция для запуска создания резервной копии
    """
    logger.info("Запуск создания резервной копии базы данных PostgreSQL...")
    
    # Запускаем асинхронную функцию
    backup_file = asyncio.run(backup_database())
    
    if backup_file:
        logger.info(f"Резервная копия базы данных PostgreSQL успешно создана: {backup_file}")
        return 0
    else:
        logger.error("Не удалось создать резервную копию базы данных PostgreSQL")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 