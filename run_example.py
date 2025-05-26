#!/usr/bin/env python
"""
Пример запуска и тестирования базы данных.
Поддерживает как SQLite, так и PostgreSQL (через переменную окружения DATABASE_URL).
"""

import os
import asyncio
import sys
import time
from datetime import datetime

# Устанавливаем переменную окружения для тестирования PostgreSQL при необходимости
# (закомментируйте эту строку для использования SQLite)
# os.environ["DATABASE_URL"] = "postgresql://username:password@localhost:5432/dbname"

# Импортируем модуль базы данных
try:
    from db_postgres import db
    print("Используем модуль db_postgres.py с поддержкой PostgreSQL")
except ImportError:
    try:
        from db import db
        print("Используем модуль db.py с поддержкой только SQLite")
    except ImportError:
        print("Ошибка: не найден модуль базы данных. Убедитесь, что файл db.py или db_postgres.py существует.")
        sys.exit(1)

async def run_example():
    """
    Пример использования базы данных
    """
    print("=" * 50)
    print(f"Начало тестирования базы данных: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Создание или получение пользователя
        user_id = await db.get_or_create_user(
            tg_id=12345,
            username="test_user",
            first_name="Тест",
            last_name="Тестов"
        )
        print(f"✅ Создан/получен пользователь с ID: {user_id}")
        
        # Сохранение ответов пользователя
        await db.save_answer(user_id, "q1", "Ответ на вопрос 1")
        await db.save_answer(user_id, "q2", "Ответ на вопрос 2")
        await db.save_answer(user_id, "q3", "Ответ на вопрос 3")
        print("✅ Ответы сохранены")
        
        # Получение всех ответов
        answers = await db.get_answers(user_id)
        print(f"✅ Ответы пользователя: {answers}")
        
        # Сохранение профиля
        profile_data = {
            "personality_type": "Интеллектуальный",
            "profile_text": "Подробный текст профиля пользователя...",
            "strengths": ["Аналитическое мышление", "Стратегическое планирование", "Объективность"],
            "areas_of_growth": ["Эмоциональный интеллект", "Баланс между анализом и действием"]
        }
        profile_id = await db.save_profile(user_id, profile_data)
        print(f"✅ Сохранен профиль с ID: {profile_id}")
        
        # Получение профиля
        profile = await db.get_profile(user_id)
        print(f"✅ Профиль пользователя получен. Тип личности: {profile.get('personality_type')}")
        
        # Создание напоминания
        reminder_id = await db.create_reminder(user_id, "0 9 * * *", "Утреннее напоминание о практике")
        print(f"✅ Создано напоминание с ID: {reminder_id}")
        
        # Получение всех активных напоминаний
        reminders = await db.get_active_reminders()
        print(f"✅ Активные напоминания: {len(reminders)} шт.")
        
        # Деактивация напоминания
        await db.deactivate_reminder(reminder_id)
        print(f"✅ Напоминание {reminder_id} деактивировано")
        
        # Получение обновленного списка активных напоминаний
        reminders = await db.get_active_reminders()
        print(f"✅ Активные напоминания после деактивации: {len(reminders)} шт.")
        
        # Создание бэкапа (только для SQLite)
        backup_result = await db.backup_database()
        print(f"✅ Результат создания бэкапа: {backup_result}")
        
        print("\n✅ Тестирование успешно завершено!")
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(run_example())
    execution_time = time.time() - start_time
    print(f"\nВремя выполнения: {execution_time:.2f} секунд") 