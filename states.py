from aiogram.fsm.state import StatesGroup, State


class QuestionnaireStates(StatesGroup):
    """Состояния для опросника."""
    # Стартовое состояние
    started = State()
    # Базовые демо-вопросы
    demo_questions = State()
    # Вопросы для определения сильных сторон
    strength_questions = State()
    # Анализ ответов и формирование профиля
    processing = State()
    # Завершение опроса
    completed = State() 