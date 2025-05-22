from aiogram.fsm.state import State, StatesGroup

class SurveyStates(StatesGroup):
    """
    Состояния для прохождения опроса
    """
    # Ожидание начала опроса
    waiting_start = State()
    # Общий опрос
    answering_questions = State()
    # Завершение опроса
    completed = State()

class MeditationStates(StatesGroup):
    """
    Состояния для медитаций
    """
    # Выбор медитации
    choosing = State()
    # Прослушивание медитации
    listening = State()

class ReminderStates(StatesGroup):
    """
    Состояния для настройки напоминаний
    """
    # Настройка времени
    setting_time = State()
    # Выбор типа напоминаний
    choosing_type = State() 