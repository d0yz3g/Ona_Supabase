#!/usr/bin/env python3
"""
Скрипт для создания заглушек (placeholders) для модулей,
которые не удалось импортировать.
"""
import os
import sys
import importlib
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [PLACEHOLDER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("placeholder_creator")

# Список модулей, для которых нужно создать заглушки
REQUIRED_MODULES = [
    "survey_handler",
    "meditation_handler",
    "conversation_handler",
    "reminder_handler",
    "voice_handler",
    "communication_handler"
]

def is_module_available(module_name):
    """Проверяет доступность модуля без его полного импорта"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def create_survey_handler_placeholder():
    """Создает заглушку для survey_handler.py"""
    if os.path.exists("survey_handler.py"):
        logger.info("Файл survey_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем роутер для опроса
survey_router = Router()

def get_main_keyboard():
    """Возвращает основную клавиатуру бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="🧘 Медитации")],
            [KeyboardButton(text="⏰ Напоминания"), KeyboardButton(text="💬 Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

@survey_router.message(Command("survey"))
@survey_router.message(F.text == "📝 Опрос")
async def cmd_survey(message: Message):
    """Обработчик команды /survey и кнопки Опрос"""
    await message.answer(
        "⚠️ Заглушка для функции опроса. Реальная функциональность временно недоступна.",
        reply_markup=get_main_keyboard()
    )

@survey_router.message(Command("profile"))
@survey_router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message):
    """Обработчик команды /profile и кнопки Профиль"""
    await message.answer(
        "⚠️ Заглушка для функции профиля. Реальная функциональность временно недоступна.",
        reply_markup=get_main_keyboard()
    )
    """

    with open("survey_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для survey_handler.py")

def create_conversation_handler_placeholder():
    """Создает заглушку для conversation_handler.py"""
    if os.path.exists("conversation_handler.py"):
        logger.info("Файл conversation_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для обработки сообщений
conversation_router = Router()

@conversation_router.message(Command("advice"))
@conversation_router.message(F.text == "💡 Советы")
async def cmd_advice(message: Message):
    """Обработчик команды /advice и кнопки Советы"""
    await message.answer("⚠️ Заглушка для функции советов. Реальная функциональность временно недоступна.")

@conversation_router.message()
async def process_message(message: Message):
    """Обработчик всех текстовых сообщений"""
    await message.answer(
        "⚠️ Бот работает в ограниченном режиме. "
        "Некоторые функции временно недоступны из-за проблем с зависимостями."
    )
    """

    with open("conversation_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для conversation_handler.py")

def create_voice_handler_placeholder():
    """Создает заглушку для voice_handler.py"""
    if os.path.exists("voice_handler.py"):
        logger.info("Файл voice_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router
from aiogram.types import Message, Voice

# Создаем роутер для голосовых сообщений
voice_router = Router()

@voice_router.message(lambda message: message.voice is not None)
async def process_voice(message: Message):
    """Обработчик голосовых сообщений"""
    await message.answer(
        "⚠️ Обработка голосовых сообщений временно недоступна из-за проблем с зависимостями."
    )
    """

    with open("voice_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для voice_handler.py")

def create_meditation_handler_placeholder():
    """Создает заглушку для meditation_handler.py"""
    if os.path.exists("meditation_handler.py"):
        logger.info("Файл meditation_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для медитаций
meditation_router = Router()

@meditation_router.message(Command("meditate"))
@meditation_router.message(F.text == "🧘 Медитации")
async def cmd_meditate(message: Message):
    """Обработчик команды /meditate и кнопки Медитации"""
    await message.answer(
        "⚠️ Функция медитаций временно недоступна из-за проблем с зависимостями."
    )
    """

    with open("meditation_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для meditation_handler.py")

def create_reminder_handler_placeholder():
    """Создает заглушку для reminder_handler.py"""
    if os.path.exists("reminder_handler.py"):
        logger.info("Файл reminder_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для напоминаний
reminder_router = Router()

async def load_reminders_from_db(bot):
    """Загрузка напоминаний из БД (заглушка)"""
    return []

@reminder_router.message(Command("reminders"))
@reminder_router.message(F.text == "⏰ Напоминания")
async def cmd_reminders(message: Message):
    """Обработчик команды /reminders и кнопки Напоминания"""
    await message.answer(
        "⚠️ Функция напоминаний временно недоступна из-за проблем с зависимостями."
    )
    """

    with open("reminder_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для reminder_handler.py")

def create_communication_handler_placeholder():
    """Создает заглушку для communication_handler.py"""
    if os.path.exists("communication_handler.py"):
        logger.info("Файл communication_handler.py уже существует, пропуск создания")
        return

    content = """
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для коммуникаций
communication_router = Router()

@communication_router.message()
async def process_message(message: Message):
    """Обработчик текстовых сообщений (используется если другие обработчики не сработали)"""
    # Этот обработчик сработает только если сообщение не обработано другими роутерами
    await message.answer(
        "⚠️ Бот работает в ограниченном режиме. Некоторые функции временно недоступны."
    )
    """

    with open("communication_handler.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создана заглушка для communication_handler.py")

def main():
    """Основная функция для создания всех заглушек"""
    logger.info("Создание заглушек для отсутствующих модулей...")
    
    # Создаем заглушки для всех необходимых модулей
    create_survey_handler_placeholder()
    create_conversation_handler_placeholder()
    create_voice_handler_placeholder()
    create_meditation_handler_placeholder()
    create_reminder_handler_placeholder()
    create_communication_handler_placeholder()
    
    logger.info("Все заглушки созданы успешно")

if __name__ == "__main__":
    main() 