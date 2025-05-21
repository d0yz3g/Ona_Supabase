import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat
from unittest.mock import AsyncMock, patch, MagicMock

from states import QuestionnaireStates
from handlers import (
    start_questionnaire, 
    process_demo_answer, 
    ask_next_demo_question,
    ask_next_strength_question,
    process_questionnaire_results,
    build_profile
)
from questions import get_demo_questions, get_strength_questions
from db import Database

class MockMessage(MagicMock):
    """Mock для сообщений Telegram."""
    def __init__(self, text="", from_user=None, chat=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.from_user = from_user or User(id=1, is_bot=False, first_name="Test", last_name="User")
        self.chat = chat or Chat(id=1, type="private")
        self.answer = AsyncMock(return_value=None)
        
    async def answer(self, text, **kwargs):
        return None

class MockFSMContext(MagicMock):
    """Mock для FSMContext."""
    def __init__(self, state=None, data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = state
        self._data = data or {}
        
    async def get_state(self):
        return self._state
        
    async def set_state(self, state):
        self._state = state
        return None
        
    async def get_data(self):
        return self._data
        
    async def update_data(self, **kwargs):
        self._data.update(kwargs)
        return None
        
    async def clear(self):
        self._state = None
        self._data = {}
        return None

@pytest.fixture
def mock_db():
    """Фикстура для мок-объекта базы данных."""
    with patch("handlers.db") as mock_db:
        # Настройка моков для методов базы данных
        mock_db.get_user_by_tg_id.return_value = {"id": 1, "tg_id": 1}
        mock_db.add_user.return_value = 1
        mock_db.get_profile.return_value = None
        mock_db.add_answer.return_value = 1
        mock_db.get_answers_by_user_id.return_value = []
        mock_db.add_profile.return_value = 1
        yield mock_db

@pytest.mark.asyncio
async def test_start_questionnaire(mock_db):
    """Тест запуска опроса."""
    message = MockMessage()
    state = MockFSMContext()
    
    await start_questionnaire(message, state)
    
    # Проверяем вызов методов БД
    mock_db.get_user_by_tg_id.assert_called_once_with(1)
    mock_db.get_profile.assert_called_once_with(1)
    
    # Проверяем установку состояния
    assert await state.get_state() == QuestionnaireStates.started
    
    # Проверяем сохраненные данные
    data = await state.get_data()
    assert data.get("user_id") == 1

@pytest.mark.asyncio
async def test_ask_next_demo_question_first(mock_db):
    """Тест запроса первого демо-вопроса."""
    message = MockMessage()
    state = MockFSMContext(data={"user_id": 1})
    
    await ask_next_demo_question(message, state)
    
    # Проверяем установку состояния
    assert await state.get_state() == QuestionnaireStates.demo_questions
    
    # Проверяем сохраненные данные
    data = await state.get_data()
    assert data.get("current_demo_question_index") == 1
    assert data.get("current_question_id") == get_demo_questions()[0]["id"]

@pytest.mark.asyncio
async def test_process_demo_answer(mock_db):
    """Тест обработки ответа на демо-вопрос."""
    message = MockMessage(text="Test Answer")
    state = MockFSMContext(
        state=QuestionnaireStates.demo_questions,
        data={
            "user_id": 1,
            "current_question_id": "name",
            "current_demo_question_index": 1
        }
    )
    
    await process_demo_answer(message, state)
    
    # Проверяем вызов метода БД
    mock_db.add_answer.assert_called_once_with(1, "name", "Test Answer")

@pytest.mark.asyncio
async def test_ask_next_strength_question(mock_db):
    """Тест запроса вопроса о сильных сторонах."""
    message = MockMessage()
    state = MockFSMContext(
        data={
            "user_id": 1,
            "current_demo_question_index": len(get_demo_questions())
        }
    )
    
    await ask_next_strength_question(message, state)
    
    # Проверяем установку состояния
    assert await state.get_state() == QuestionnaireStates.strength_questions
    
    # Проверяем сохраненные данные
    data = await state.get_data()
    assert data.get("current_strength_question_index") == 1
    assert data.get("current_question_id") == get_strength_questions()[0]["id"]

@pytest.mark.asyncio
async def test_process_questionnaire_results(mock_db):
    """Тест обработки результатов опроса."""
    message = MockMessage()
    state = MockFSMContext(
        state=QuestionnaireStates.processing,
        data={"user_id": 1}
    )
    
    # Настройка моков для получения ответов
    answers = [
        {"question_id": "name", "answer_text": "Test User"},
        {"question_id": "age", "answer_text": "30"},
        {"question_id": "birthdate", "answer_text": "01.01.1990"},
        {"question_id": "birthplace", "answer_text": "Moscow, Russia"},
        {"question_id": "timezone", "answer_text": "UTC+3"},
        # Ответы на вопросы о сильных сторонах
        {"question_id": "strength_1", "answer_text": "5"},
        {"question_id": "strength_2", "answer_text": "4"},
        {"question_id": "strength_3", "answer_text": "3"},
    ]
    mock_db.get_answers_by_user_id.return_value = answers
    
    await process_questionnaire_results(message, state)
    
    # Проверяем вызов методов БД
    mock_db.get_answers_by_user_id.assert_called_once_with(1)
    mock_db.add_profile.assert_called_once()
    
    # Проверяем установку состояния
    assert await state.get_state() == QuestionnaireStates.completed

@pytest.mark.asyncio
@patch("handlers.generate_profile")
@patch("handlers.make_natal_chart")
async def test_build_profile_with_ai_and_natal(mock_make_natal_chart, mock_generate_profile, mock_db):
    """Тест построения профиля с интеграцией AI и натальной карты."""
    user_id = 1
    # Мокаем ответы на вопросы
    answers = [
        {"question_id": "name", "answer_text": "Test User"},
        {"question_id": "age", "answer_text": "30"},
        {"question_id": "birthdate", "answer_text": "01.01.1990"},
        {"question_id": "birthplace", "answer_text": "Moscow, Russia"},
        {"question_id": "timezone", "answer_text": "UTC+3"},
        # Ответы на вопросы о сильных сторонах
        {"question_id": "strength_1", "answer_text": "5"},
        {"question_id": "strength_7", "answer_text": "5"},
        {"question_id": "strength_10", "answer_text": "5"},
        {"question_id": "strength_2", "answer_text": "2"},
        {"question_id": "strength_3", "answer_text": "2"},
    ]
    
    # Настройка моков
    mock_make_natal_chart.return_value = {
        "sun_long": 280.123,
        "moon_long": 120.456,
        "mercury_long": 300.789,
        "coordinates": {
            "latitude": 55.7558,
            "longitude": 37.6173
        },
        "date": "1990-01-01 12:00"
    }
    
    mock_generate_profile.return_value = {
        "summary": "Тестовый психологический профиль.",
        "strengths": ["Коммуникабельность", "Эмпатия", "Творчество"],
        "growth_areas": ["Организованность", "Аналитические навыки"]
    }
    
    profile_data = await build_profile(user_id, answers)
    
    # Проверяем содержимое профиля
    assert "summary_data" in profile_data
    assert "natal_data" in profile_data
    assert "category_names" in profile_data
    
    # Проверяем вызов функции make_natal_chart
    mock_make_natal_chart.assert_called_once()
    
    # Проверяем вызов функции generate_profile
    mock_generate_profile.assert_called_once()
    
    # Проверяем, что результаты AI и натальной карты добавлены в профиль
    assert profile_data["summary_data"]["ai_analysis"] == mock_generate_profile.return_value
    assert profile_data["natal_data"] == mock_make_natal_chart.return_value
    
    # Проверяем обновление профиля в БД
    mock_db.update_profile_natal.assert_called_once_with(user_id, mock_make_natal_chart.return_value)
    mock_db.update_profile_summary.assert_called_once() 