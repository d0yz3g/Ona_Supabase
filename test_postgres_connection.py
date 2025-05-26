#!/usr/bin/env python
"""
Скрипт для тестирования соединения с PostgreSQL на Railway.
Запустите этот скрипт после настройки переменной окружения DATABASE_URL.
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяем наличие переменной окружения DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

async def test_postgres_connection():
    """
    Проверяет соединение с PostgreSQL или SQLite в зависимости от переменной окружения
    """
    print("=" * 50)
    print(f"Начало теста соединения с базой данных: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not DATABASE_URL:
        print("\n❌ Переменная окружения DATABASE_URL не найдена.")
        print("   Будет использоваться локальная SQLite база данных.")
        print("\n   Для настройки PostgreSQL выполните следующие шаги:")
        print("   1. Создайте базу данных PostgreSQL в Railway")
        print("   2. Получите строку подключения")
        print("   3. Добавьте в .env файл строку:")
        print("      DATABASE_URL=postgres://username:password@hostname:port/database_name")
        print("\n   Подробные инструкции: docs/railway_postgres_setup.md")
        
        # Проверяем соединение с SQLite
        try:
            from db_postgres import db
            print("\n✅ Подключение к SQLite успешно установлено")
            print(f"   Путь к файлу базы данных: {db._db_path}")
            
            # Создаем тестового пользователя
            user_id = await db.get_or_create_user(
                tg_id=99999,
                username="test_postgres",
                first_name="PostgreSQL",
                last_name="Test"
            )
            print(f"✅ Тестовый пользователь создан с ID: {user_id}")
            
        except Exception as e:
            print(f"\n❌ Ошибка при подключении к SQLite: {e}")
            return
    else:
        print("\n✅ Переменная окружения DATABASE_URL найдена.")
        print(f"   Значение: {DATABASE_URL[:20]}...")  # Показываем только начало URL для безопасности
        
        # Проверяем соединение с PostgreSQL
        try:
            import psycopg2
            print("\n✅ Библиотека psycopg2 успешно импортирована")
        except ImportError:
            print("\n❌ Библиотека psycopg2 не установлена.")
            print("   Установите ее командой: pip install psycopg2-binary")
            return
        
        try:
            from db_postgres import db
            
            if db._use_postgres:
                print("✅ Модуль db_postgres настроен для работы с PostgreSQL")
            else:
                print("❌ Модуль db_postgres не использует PostgreSQL, несмотря на наличие DATABASE_URL")
                return
            
            # Создаем тестового пользователя
            user_id = await db.get_or_create_user(
                tg_id=99999,
                username="test_postgres",
                first_name="PostgreSQL",
                last_name="Test"
            )
            print(f"✅ Тестовый пользователь создан с ID: {user_id}")
            
            # Сохраняем и получаем тестовый ответ
            await db.save_answer(user_id, "test_question", f"Test answer at {datetime.now()}")
            answers = await db.get_answers(user_id)
            print(f"✅ Тестовый ответ сохранен и получен: {answers.get('test_question')}")
            
            # Создаем тестовый профиль
            profile_data = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "db_type": "PostgreSQL"
            }
            profile_id = await db.save_profile(user_id, profile_data)
            print(f"✅ Тестовый профиль создан с ID: {profile_id}")
            
            print("\n✅ Соединение с PostgreSQL работает корректно!")
            
        except Exception as e:
            print(f"\n❌ Ошибка при подключении к PostgreSQL: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print("\n" + "=" * 50)
    print("Тест соединения завершен")
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(test_postgres_connection())
    except KeyboardInterrupt:
        print("\nТест прерван пользователем")
    except Exception as e:
        print(f"\nОшибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc() 