import logging
import re
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services.recs import generate_recommendation, detect_focus, AVAILABLE_FOCUSES

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация роутера
recs_router = Router(name="recommendations")

# Паттерн для извлечения фокуса из команды
FOCUS_PATTERN = r"/reflect(?:_([a-zA-Z-]+))?"

@recs_router.message(Command("reflect"))
async def reflect_command(message: Message):
    """Обработчик команды /reflect с опциональным фокусом (/reflect или /reflect_anxiety)."""
    # Извлекаем фокус из команды
    match = re.match(FOCUS_PATTERN, message.text)
    focus = match.group(1) if match and match.group(1) else "default"
    
    # Извлекаем текст запроса после команды
    command_parts = message.text.split(maxsplit=1)
    text = command_parts[1] if len(command_parts) > 1 else "Дай мне совет"
    
    # Генерируем рекомендацию
    recommendation = await generate_recommendation(
        text=text,
        user_id=message.from_user.id,
        focus=focus
    )
    
    # Отправляем ответ
    await message.answer(recommendation)
    logger.info(f"Отправлена рекомендация пользователю {message.from_user.id} по команде /reflect")

@recs_router.message(F.text)
async def process_text_message(message: Message):
    """Обработчик текстовых сообщений пользователя."""
    # Проверяем, не является ли это командой
    if message.text.startswith('/'):
        return
    
    # Определяем фокус из текста сообщения
    detected_focus = detect_focus(message.text) or "default"
    
    # Генерируем рекомендацию
    recommendation = await generate_recommendation(
        text=message.text,
        user_id=message.from_user.id,
        focus=detected_focus
    )
    
    # Отправляем ответ
    await message.answer(recommendation)
    logger.info(f"Отправлена рекомендация пользователю {message.from_user.id} на основе текстового сообщения")

@recs_router.message(Command("help_reflect"))
async def help_reflect(message: Message):
    """Справка по использованию команды /reflect и доступным фокусам."""
    help_text = [
        "🧠 Команда /reflect позволяет получить психологический совет.",
        "",
        "Варианты использования:",
        "- /reflect - совет по общей теме",
        "- /reflect_focus - совет по конкретному фокусу (например, /reflect_anxiety)",
        "- /reflect Ваш запрос - совет на основе Вашего запроса",
        "",
        "📚 Доступные фокусы:"
    ]
    
    for focus, description in AVAILABLE_FOCUSES.items():
        if focus != "default":
            help_text.append(f"- {focus}: {description}")
    
    await message.answer("\n".join(help_text))
    logger.info(f"Отправлена справка по команде /reflect пользователю {message.from_user.id}")

@recs_router.message(F.voice)
async def process_voice_message(message: Message):
    """Обработчик голосовых сообщений (заглушка)."""
    # Заглушка для обработки голосовых сообщений
    # В будущем здесь можно добавить распознавание голоса через STT-сервис
    await message.answer(
        "Я пока не умею распознавать голосовые сообщения. "
        "Пожалуйста, отправьте ваш запрос текстом или используйте команду /reflect."
    )
    logger.info(f"Пользователь {message.from_user.id} отправил голосовое сообщение (не обработано)") 