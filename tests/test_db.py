import os
import pytest
import json
from datetime import datetime
from db import Database

# Тестовая база данных
TEST_DB = "test_ona_bot.db"

@pytest.fixture
def db():
    """Фикстура для создания тестовой базы данных."""
    # Убедимся, что тестовая база не существует
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Создание новой БД
    db = Database(TEST_DB)
    
    # Возвращаем БД для тестов
    yield db
    
    # Закрываем соединение после тестов
    db.close()
    
    # Удаляем тестовую БД
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# Тесты для пользователей

def test_add_user(db):
    """Тест добавления пользователя."""
    user_id = db.add_user(123456789, "Test User")
    assert user_id is not None
    assert isinstance(user_id, int)
    
    # Проверка получения пользователя
    user = db.get_user_by_id(user_id)
    assert user is not None
    assert user["tg_id"] == 123456789
    assert user["full_name"] == "Test User"
    
    # Проверка, что повторное добавление вернет тот же id
    same_user_id = db.add_user(123456789)
    assert same_user_id == user_id
    
    # Проверка обновления имени
    updated_user_id = db.add_user(123456789, "Updated Name")
    assert updated_user_id == user_id
    updated_user = db.get_user_by_id(user_id)
    assert updated_user["full_name"] == "Updated Name"

def test_get_user_by_tg_id(db):
    """Тест получения пользователя по TG ID."""
    user_id = db.add_user(123456789, "Test User")
    
    user = db.get_user_by_tg_id(123456789)
    assert user is not None
    assert user["id"] == user_id
    assert user["tg_id"] == 123456789
    
    # Проверка несуществующего пользователя
    nonexistent_user = db.get_user_by_tg_id(999999999)
    assert nonexistent_user is None

def test_get_all_users(db):
    """Тест получения всех пользователей."""
    # Добавляем несколько пользователей
    db.add_user(111111, "User One")
    db.add_user(222222, "User Two")
    db.add_user(333333, "User Three")
    
    users = db.get_all_users()
    assert len(users) == 3
    
    # Проверка что все пользователи возвращаются корректно
    user_ids = [user["tg_id"] for user in users]
    assert 111111 in user_ids
    assert 222222 in user_ids
    assert 333333 in user_ids

# Тесты для ответов

def test_add_answer(db):
    """Тест добавления ответа."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавление ответа
    answer_id = db.add_answer(user_id, "q1", "Test answer")
    assert answer_id is not None
    
    # Получение ответа
    answer = db.get_answer(user_id, "q1")
    assert answer is not None
    assert answer["question_id"] == "q1"
    assert answer["answer_text"] == "Test answer"
    
    # Проверка обновления ответа
    updated_answer_id = db.add_answer(user_id, "q1", "Updated answer")
    assert updated_answer_id == answer_id
    
    updated_answer = db.get_answer(user_id, "q1")
    assert updated_answer["answer_text"] == "Updated answer"

def test_get_answers_by_user_id(db):
    """Тест получения всех ответов пользователя."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавляем несколько ответов
    db.add_answer(user_id, "q1", "Answer 1")
    db.add_answer(user_id, "q2", "Answer 2")
    db.add_answer(user_id, "q3", "Answer 3")
    
    answers = db.get_answers_by_user_id(user_id)
    assert len(answers) == 3
    
    # Проверка содержимого ответов
    question_ids = [answer["question_id"] for answer in answers]
    assert "q1" in question_ids
    assert "q2" in question_ids
    assert "q3" in question_ids

# Тесты для профилей

def test_add_profile(db):
    """Тест добавления профиля."""
    user_id = db.add_user(123456789, "Test User")
    
    # Тестовые данные профиля
    summary_data = {
        "strengths": ["Аналитик", "Организатор"],
        "scores": {"analytical": 85, "creative": 70}
    }
    
    natal_data = {
        "ascendant": "Leo",
        "moon": "Taurus",
        "sun": "Gemini"
    }
    
    # Добавление профиля
    profile_id = db.add_profile(user_id, summary_data, natal_data)
    assert profile_id is not None
    
    # Получение профиля
    profile = db.get_profile(user_id)
    assert profile is not None
    assert profile["summary_json"] == summary_data
    assert profile["natal_json"] == natal_data
    
    # Обновление профиля
    updated_summary = {"strengths": ["Лидер", "Коммуникатор"]}
    db.add_profile(user_id, updated_summary, natal_data)
    
    updated_profile = db.get_profile(user_id)
    assert updated_profile["summary_json"] == updated_summary
    
def test_get_nonexistent_profile(db):
    """Тест получения несуществующего профиля."""
    user_id = db.add_user(123456789, "Test User")
    
    # Профиль еще не создан
    profile = db.get_profile(user_id)
    assert profile is None

# Тесты для напоминаний

def test_add_reminder(db):
    """Тест добавления напоминания."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавление напоминания
    reminder_time = "2023-12-31 12:00:00"
    reminder_text = "Test reminder"
    
    reminder_id = db.add_reminder(user_id, reminder_time, reminder_text)
    assert reminder_id is not None
    
    # Получение напоминания
    reminder = db.get_reminder(reminder_id)
    assert reminder is not None
    assert reminder["reminder_time"] == reminder_time
    assert reminder["text"] == reminder_text
    assert reminder["is_sent"] == 0  # Изначально не отправлено

def test_get_reminders_by_user_id(db):
    """Тест получения напоминаний пользователя."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавляем несколько напоминаний
    db.add_reminder(user_id, "2023-12-31 10:00:00", "Reminder 1")
    db.add_reminder(user_id, "2023-12-31 11:00:00", "Reminder 2")
    db.add_reminder(user_id, "2023-12-31 12:00:00", "Reminder 3")
    
    reminders = db.get_reminders_by_user_id(user_id)
    assert len(reminders) == 3
    
    # Проверка фильтрации по отправленным
    reminder_id = reminders[0]["id"]
    db.mark_reminder_sent(reminder_id)
    
    unsent_reminders = db.get_reminders_by_user_id(user_id, only_unsent=True)
    assert len(unsent_reminders) == 2

def test_mark_reminder_sent(db):
    """Тест отметки напоминания как отправленного."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавление напоминания
    reminder_id = db.add_reminder(user_id, "2023-12-31 12:00:00", "Test reminder")
    
    # Отметка как отправленного
    db.mark_reminder_sent(reminder_id)
    
    # Проверка статуса
    reminder = db.get_reminder(reminder_id)
    assert reminder["is_sent"] == 1

def test_delete_reminder(db):
    """Тест удаления напоминания."""
    user_id = db.add_user(123456789, "Test User")
    
    # Добавление напоминания
    reminder_id = db.add_reminder(user_id, "2023-12-31 12:00:00", "Test reminder")
    
    # Удаление напоминания
    result = db.delete_reminder(reminder_id)
    assert result is True
    
    # Проверка, что напоминание удалено
    reminder = db.get_reminder(reminder_id)
    assert reminder is None
    
    # Проверка удаления несуществующего напоминания
    result = db.delete_reminder(999999)
    assert result is False 