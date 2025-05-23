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
                
                with open(module_file, "w") as f:
                    f.write(f"# Placeholder for {module_file}\n")
                    f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                    f.write(module_content.strip())
                
                logger.info(f"Заглушка для {module_file} успешно создана")
            except Exception as e:
                logger.error(f"Ошибка при создании заглушки для {module_file}: {e}")
        else:
            logger.info(f"Файл {module_file} уже существует, создание заглушки не требуется")
    
    logger.info("Завершено создание заглушек для модулей бота")

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК ДЛЯ RAILWAY")
    print("=" * 50)
    
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Файлы в текущей директории: {[f for f in os.listdir('.') if f.endswith('.py')]}")
    
    create_placeholder_files()
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК")
    print("=" * 50) 