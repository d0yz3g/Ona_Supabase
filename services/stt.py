import os
import logging
import tempfile
from typing import Optional

import httpx
from openai import AsyncOpenAI
from aiogram.types import Voice

# Настройка логирования
logger = logging.getLogger(__name__)

# Проверка наличия API-ключа OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY не найден в переменных окружения. Функция распознавания голоса будет недоступна.")

# Инициализация клиента OpenAI с API-ключом из переменных окружения (если доступен)
http_client = httpx.AsyncClient()
client = None
if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
    except Exception as e:
        logger.error(f"Ошибка при инициализации OpenAI API: {e}")

async def download_voice_message(bot, voice: Voice) -> Optional[str]:
    """
    Скачивает голосовое сообщение.
    
    Args:
        bot: Экземпляр бота для получения файла.
        voice: Голосовое сообщение.
        
    Returns:
        Optional[str]: Путь к временному файлу с голосовым сообщением или None в случае ошибки.
    """
    try:
        # Получение информации о файле
        file_info = await bot.get_file(voice.file_id)
        file_path = file_info.file_path
        
        # Создание временного файла
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        file_name = temp_file.name
        temp_file.close()
        
        # Скачивание файла
        await bot.download_file(file_path, file_name)
        
        logger.info(f"Голосовое сообщение скачано: {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"Ошибка при скачивании голосового сообщения: {e}")
        return None

async def transcribe_voice(file_path: str) -> Optional[str]:
    """
    Транскрибирует голосовое сообщение в текст с помощью OpenAI Whisper API.
    
    Args:
        file_path: Путь к аудиофайлу
        
    Returns:
        str или None: Распознанный текст или None в случае ошибки
    """
    if not client:
        logger.error("OpenAI API недоступен для транскрибирования голосового сообщения")
        return None
    
    try:
        # Открываем файл и отправляем его в OpenAI API
        with open(file_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru",  # Ставим русский язык
                response_format="text"
            )
        
        # В OpenAI API v1.x response - это объект, а не строка напрямую
        # Нужно получить текст из объекта ответа
        if hasattr(response, 'text'):
            # Для более новых версий API, где ответ - объект с полем text
            return response.text
        elif isinstance(response, str):
            # Для версий API, где ответ возвращается как строка
            return response
        else:
            # Для других версий API, попробуем вернуть строковое представление
            logger.warning(f"Необычный формат ответа от OpenAI API: {type(response)}")
            return str(response)
    
    except Exception as e:
        logger.error(f"Ошибка при транскрибировании голосового сообщения: {e}")
        return None

async def process_voice_message(bot, voice: Voice) -> Optional[str]:
    """
    Обрабатывает голосовое сообщение: скачивает и транскрибирует.
    
    Args:
        bot: Экземпляр бота для получения файла.
        voice: Голосовое сообщение.
        
    Returns:
        Optional[str]: Распознанный текст или None в случае ошибки.
    """
    # Скачиваем голосовое сообщение
    file_path = await download_voice_message(bot, voice)
    if not file_path:
        return None
    
    # Транскрибируем голосовое сообщение
    text = await transcribe_voice(file_path)
    return text 