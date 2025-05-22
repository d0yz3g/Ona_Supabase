import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.recs import generate_response
from services.stt import process_voice_message
from states import QuestionnaireStates

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
    if current_state is not None and current_state != QuestionnaireStates.completed.state:
        # Если пользователь находится в каком-то состоянии (например, проходит опрос),
        # то не обрабатываем сообщение здесь, за исключением состояния completed
        logger.debug(f"Пропуск обработки текстового сообщения: пользователь {message.from_user.id} находится в состоянии {current_state}")
        return
    
    # Генерируем контекстуальный ответ
    response = await generate_response(
        text=message.text,
        user_id=message.from_user.id
    )
    
    # Отправляем ответ
    await message.answer(response)
    logger.info(f"Отправлен ответ пользователю {message.from_user.id} на основе текстового сообщения")

@router.message(F.chat.type == "private", F.voice)
async def process_voice_message_handler(message: Message, state: FSMContext):
    """Обработчик голосовых сообщений."""
    # Проверяем текущее состояние FSM, чтобы не дублировать обработку сообщений во время опроса
    current_state = await state.get_state()
    if current_state is not None and current_state != QuestionnaireStates.completed.state:
        # Если пользователь находится в каком-то состоянии (например, проходит опрос),
        # то не обрабатываем сообщение здесь, за исключением состояния completed
        logger.debug(f"Пропуск обработки голосового сообщения: пользователь {message.from_user.id} находится в состоянии {current_state}")
        return
    
    # Отправляем сообщение о начале обработки
    processing_message = await message.answer("Обрабатываю ваше голосовое сообщение...")
    
    # Транскрибируем голосовое сообщение
    transcribed_text = await process_voice_message(message.bot, message.voice)
    
    if transcribed_text:
        # Если текст успешно распознан, то отправляем его пользователю
        await processing_message.edit_text(f"Я распознал: «{transcribed_text}»")
        
        # Генерируем контекстуальный ответ с учетом типа сообщения
        response = await generate_response(
            text=transcribed_text,
            user_id=message.from_user.id
        )
        
        # Отправляем ответ
        await message.answer(response)
        logger.info(f"Отправлен ответ пользователю {message.from_user.id} на основе голосового сообщения")
    else:
        # Если текст не распознан, то отправляем сообщение об ошибке
        await processing_message.edit_text(
            "Извините, не удалось распознать ваше голосовое сообщение. "
            "Пожалуйста, попробуйте еще раз или отправьте текстовое сообщение."
        )
        logger.warning(f"Не удалось распознать голосовое сообщение пользователя {message.from_user.id}") 