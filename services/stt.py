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
        file_path: Путь к файлу с голосовым сообщением.
        
    Returns:
        Optional[str]: Распознанный текст или None в случае ошибки.
    """
    # Проверяем наличие клиента OpenAI
    if not client:
        logger.warning("OpenAI API недоступен. Невозможно транскрибировать голосовое сообщение.")
        return None
    
    try:
        # Открываем файл для чтения в бинарном режиме
        with open(file_path, "rb") as audio_file:
            # Отправляем запрос на транскрибацию
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"  # Указываем русский язык для лучшего распознавания
            )
        
        # Удаляем временный файл
        try:
            os.unlink(file_path)
            logger.debug(f"Временный файл удален: {file_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
        
        # Возвращаем распознанный текст
        logger.info("Голосовое сообщение успешно транскрибировано")
        return transcript.text
    except Exception as e:
        logger.error(f"Ошибка при транскрибации голосового сообщения: {e}")
        
        # Удаляем временный файл в случае ошибки
        try:
            os.unlink(file_path)
        except:
            pass
        
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