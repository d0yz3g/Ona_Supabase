#!/usr/bin/env python
"""
Скрипт для создания заглушек недостающих модулей бота.
Запускается в начале сборки в Railway.
"""

import os
import logging
import sys
from pathlib import Path

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [PLACEHOLDER] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("placeholders")

# Список модулей, которые должны быть в проекте
REQUIRED_MODULES = {
    "survey_handler.py": """
import logging
from typing import Dict, Any, Optional, List, Tuple
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки опроса
survey_router = Router(name="survey")

# Функция для получения основной клавиатуры
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает основную клавиатуру бота.
    
    Returns:
        ReplyKeyboardMarkup: Основная клавиатура бота
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard

# Обработчик команды опроса
@survey_router.message(Command("survey"))
@survey_router.message(F.text == "📝 Опрос")
async def cmd_survey(message: Message):
    """
    Обработчик команды /survey
    """
    await message.answer(
        "Это заглушка для функции опроса. Реальный модуль не загружен.",
        reply_markup=get_main_keyboard()
    )
""",

    "meditation_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки медитаций
meditation_router = Router(name="meditation")

@meditation_router.message(Command("meditate"))
@meditation_router.message(F.text == "🧘 Медитации")
async def cmd_meditate(message: Message):
    """
    Обработчик команды /meditate
    """
    await message.answer(
        "Это заглушка для функции медитации. Реальный модуль не загружен."
    )
""",

    "conversation_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки диалогов
conversation_router = Router(name="conversation")

@conversation_router.message()
async def handle_message(message: Message):
    """
    Обработчик сообщений пользователя
    """
    # Заглушка для обработки обычных сообщений
    if message.text and not message.text.startswith('/') and not message.text.startswith('📝') and not message.text.startswith('👤') and not message.text.startswith('🧘') and not message.text.startswith('⏰') and not message.text.startswith('💡') and not message.text.startswith('💬'):
        await message.answer(
            "Это заглушка для функции диалога. Реальный модуль не загружен."
        )
""",

    "reminder_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем планировщик заданий
scheduler = AsyncIOScheduler()

# Создаем роутер для обработки напоминаний
reminder_router = Router(name="reminder")

@reminder_router.message(Command("reminder"))
@reminder_router.message(F.text == "⏰ Напоминания")
async def cmd_reminder(message: Message):
    """
    Обработчик команды /reminder
    """
    await message.answer(
        "Это заглушка для функции напоминаний. Реальный модуль не загружен."
    )
""",

    "voice_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.filters import Command

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки голосовых сообщений
voice_router = Router(name="voice")

@voice_router.message(F.voice)
async def handle_voice(message: Message):
    """
    Обработчик голосовых сообщений
    """
    await message.answer(
        "Это заглушка для функции обработки голосовых сообщений. Реальный модуль не загружен."
    )
""",

    "profile_generator.py": """
import logging
from typing import Dict, Any, Optional

# Настройка логирования
logger = logging.getLogger(__name__)

async def generate_profile(user_id: int, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Генерирует профиль пользователя на основе ответов.
    
    Args:
        user_id: ID пользователя
        answers: Ответы пользователя
        
    Returns:
        Optional[Dict[str, Any]]: Профиль пользователя или None в случае ошибки
    """
    logger.info(f"Генерация профиля для пользователя {user_id} (заглушка)")
    
    # Создаем базовый профиль (заглушка)
    profile = {
        "user_id": user_id,
        "personality_type": "Не определен",
        "strengths": ["Аналитическое мышление", "Коммуникабельность", "Творческий подход"],
        "created": "2025-05-23"
    }
    
    return profile
"""
}

def create_placeholder_files():
    """
    Создает заглушки для недостающих модулей бота.
    """
    logger.info("Начало создания заглушек для модулей бота")
    
    # Проверяем и создаем заглушки для каждого модуля
    for module_file, module_content in REQUIRED_MODULES.items():
        if not os.path.exists(module_file):
            try:
                logger.info(f"Создание заглушки для {module_file}")
                
                with open(module_file, "w", encoding="utf-8") as f:
                    f.write(f"# Placeholder for {module_file}\n")
                    f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                    f.write(module_content.strip())
                
                logger.info(f"Заглушка для {module_file} успешно создана")
                
                # Проверка, что файл действительно создан
                if os.path.exists(module_file):
                    file_size = os.path.getsize(module_file)
                    logger.info(f"Заглушка {module_file} создана успешно. Размер файла: {file_size} байт")
                else:
                    logger.error(f"Не удалось создать заглушку {module_file} (файл не найден после создания)")
            except Exception as e:
                logger.error(f"Ошибка при создании заглушки для {module_file}: {e}")
        else:
            logger.info(f"Файл {module_file} уже существует, проверка содержимого...")
            try:
                # Проверяем размер файла
                file_size = os.path.getsize(module_file)
                if file_size == 0:
                    logger.warning(f"Файл {module_file} существует, но имеет нулевой размер. Создаем заглушку заново.")
                    with open(module_file, "w", encoding="utf-8") as f:
                        f.write(f"# Placeholder for {module_file} (re-created due to zero size)\n")
                        f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                        f.write(module_content.strip())
                    logger.info(f"Заглушка для {module_file} повторно создана")
                else:
                    logger.info(f"Файл {module_file} уже существует и не пустой (размер: {file_size} байт)")
            except Exception as e:
                logger.error(f"Ошибка при проверке существующего файла {module_file}: {e}")
    
    logger.info("Завершено создание заглушек для модулей бота")

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК ДЛЯ RAILWAY")
    print("=" * 50)
    
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Файлы в текущей директории: {[f for f in os.listdir('.') if f.endswith('.py')]}")
    
    # Создаем необходимые директории
    os.makedirs("logs", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)
    logger.info("Созданы директории logs и tmp")
    
    create_placeholder_files()
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК")
    print("=" * 50) 