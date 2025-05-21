import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.recs import generate_recommendation, detect_focus

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация роутера с низким приоритетом для обработки всех остальных сообщений
router = Router(name="general")

# Фильтр для личных сообщений и не команд
@router.message(F.chat.type == "private", ~F.text.startswith('/'), F.text)
async def process_text_message(message: Message, state: FSMContext):
    """Обработчик текстовых сообщений пользователя (не команд)."""
    # Проверяем текущее состояние FSM, чтобы не дублировать обработку сообщений во время опроса
    current_state = await state.get_state()
    if current_state is not None:
        # Если пользователь находится в каком-то состоянии (например, проходит опрос),
        # то не обрабатываем сообщение здесь
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

@router.message(F.chat.type == "private", F.voice)
async def process_voice_message(message: Message):
    """Обработчик голосовых сообщений."""
    # Заглушка для обработки голосовых сообщений
    # В будущем здесь можно добавить распознавание голоса через STT-сервис
    await message.answer(
        "Я пока не умею распознавать голосовые сообщения. "
        "Пожалуйста, отправьте ваш запрос текстом или используйте команду /reflect."
    )
    logger.info(f"Пользователь {message.from_user.id} отправил голосовое сообщение (не обработано)") 