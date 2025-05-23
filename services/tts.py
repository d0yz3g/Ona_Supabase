import os
import uuid
import logging
import aiohttp
import json
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

# Получение токена ElevenLabs из переменных окружения
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    logger.warning("ELEVEN_API_KEY не найден в переменных окружения. Функция генерации голоса будет работать в демо-режиме.")

# API URL ElevenLabs
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# ID голоса по умолчанию (мягкий, спокойный голос)
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella - успокаивающий женский голос

# Максимальная длина текста для передачи в API
MAX_TEXT_LENGTH = 4000

async def generate_audio(text: str, user_id: int, meditation_type: str = "default") -> tuple:
    """
    Генерирует аудио с помощью ElevenLabs API.
    
    Args:
        text: Текст для преобразования в аудио
        user_id: ID пользователя Telegram
        meditation_type: Тип медитации (relax, focus, sleep)
        
    Returns:
        tuple: (str, str) - (Путь к созданному аудио-файлу, причина ошибки) 
               Если аудио создано успешно - (путь_к_файлу, None)
               Если произошла ошибка - (None, текст_ошибки)
    """
    # Создаем директорию tmp, если она не существует
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_name = f"{meditation_type}_{user_id}_{uuid.uuid4()}.mp3"
    file_path = tmp_dir / file_name
    
    # Если API ключ недоступен, генерируем демо-ответ
    if not ELEVEN_API_KEY:
        logger.warning(f"ELEVEN_API_KEY недоступен, генерация аудио невозможна для пользователя {user_id}")
        return None, "API ключ недоступен"
    
    try:
        # Подготовка данных для запроса
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY
        }
        
        # Параметры голоса (можно настроить)
        voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
        
        # Подготавливаем текст (ограничиваем длину)
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH-3] + "..."
            logger.warning(f"Текст для генерации аудио был обрезан для пользователя {user_id}")
        
        # Данные для запроса
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": voice_settings
        }
        
        # ID голоса выбираем в зависимости от типа медитации
        voice_id = DEFAULT_VOICE_ID
        
        # Отправляем запрос к API
        logger.info(f"Отправка запроса к ElevenLabs API для пользователя {user_id}")
        
        # Выполняем асинхронный запрос к API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ELEVEN_API_URL}/{voice_id}",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    # Сохраняем аудио-файл
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    logger.info(f"Аудио успешно сгенерировано и сохранено: {file_path}")
                    return str(file_path), None
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка при генерации аудио: {response.status}, {error_text}")
                    
                    # Проверяем тип ошибки
                    try:
                        error_data = json.loads(error_text)
                        if response.status == 401 and "quota_exceeded" in str(error_data):
                            error_reason = "quota_exceeded"
                        else:
                            error_reason = f"HTTP ошибка {response.status}"
                    except:
                        error_reason = f"HTTP ошибка {response.status}"
                    
                    return None, error_reason
    except Exception as e:
        logger.error(f"Ошибка при генерации аудио: {e}")
        return None, str(e) 