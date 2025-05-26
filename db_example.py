import asyncio
from db import db

async def example():
    """
    Пример использования базы данных
    """
    print("Начало примера использования БД...")
    
    # Создание или получение пользователя
    user_id = await db.get_or_create_user(
        tg_id=12345,
        username="test_user",
        first_name="Тест",
        last_name="Тестов"
    )
    print(f"Создан/получен пользователь с ID: {user_id}")
    
    # Сохранение ответов пользователя
    await db.save_answer(user_id, "q1", "Ответ на вопрос 1")
    await db.save_answer(user_id, "q2", "Ответ на вопрос 2")
    await db.save_answer(user_id, "q3", "Ответ на вопрос 3")
    print("Ответы сохранены")
    
    # Получение всех ответов
    answers = await db.get_answers(user_id)
    print(f"Ответы пользователя: {answers}")
    
    # Сохранение профиля
    profile_data = {
        "personality_type": "Интеллектуальный",
        "profile_text": "Подробный текст профиля пользователя...",
        "strengths": ["Аналитическое мышление", "Стратегическое планирование", "Объективность"],
        "areas_of_growth": ["Эмоциональный интеллект", "Баланс между анализом и действием"]
    }
    profile_id = await db.save_profile(user_id, profile_data)
    print(f"Сохранен профиль с ID: {profile_id}")
    
    # Получение профиля
    profile = await db.get_profile(user_id)
    print(f"Профиль пользователя: {profile}")
    
    # Создание напоминания
    reminder_id = await db.create_reminder(user_id, "0 9 * * *", "Утреннее напоминание о практике")
    print(f"Создано напоминание с ID: {reminder_id}")
    
    # Получение всех активных напоминаний
    reminders = await db.get_active_reminders()
    print(f"Активные напоминания: {reminders}")
    
    # Деактивация напоминания
    await db.deactivate_reminder(reminder_id)
    print(f"Напоминание {reminder_id} деактивировано")
    
    # Получение обновленного списка активных напоминаний
    reminders = await db.get_active_reminders()
    print(f"Активные напоминания после деактивации: {reminders}")
    
    print("Пример завершен!")

if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(example()) 