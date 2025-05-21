import os
import uuid
import logging
import aiofiles
import aiohttp
import asyncio
from typing import Optional

# Настройка логирования
logger = logging.getLogger(__name__)

# Параметры API
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    logger.warning("ELEVEN_API_KEY не найден в переменных окружения. Будет использоваться заглушка для голосовых сообщений.")

ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # ID женского голоса по умолчанию
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"

# Директория для временных файлов
TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)

# Путь к заготовленному аудиофайлу для заглушки
DEFAULT_AUDIO_PATH = os.path.join(TMP_DIR, "default_meditation.mp3")

async def generate_voice(text: str, tg_id: int) -> Optional[str]:
    """
    Генерация голосового сообщения с использованием ElevenLabs API.
    Если API-ключ отсутствует, возвращается путь к заготовленному аудиофайлу.
    
    Args:
        text: Текст для озвучивания.
        tg_id: ID пользователя в Telegram.
        
    Returns:
        Optional[str]: Путь к созданному аудиофайлу или None в случае ошибки.
    """
    if not ELEVEN_API_KEY:
        logger.info(f"Используется заглушка для голосового сообщения пользователя {tg_id}")
        
        # Создаем копию заготовленного аудиофайла с уникальным именем
        file_uuid = str(uuid.uuid4())
        file_path = os.path.join(TMP_DIR, f"{tg_id}_{file_uuid}.mp3")
        
        # Если существует заготовленный файл, копируем его
        if os.path.exists(DEFAULT_AUDIO_PATH):
            try:
                # Копирование файла синхронно (для простоты)
                with open(DEFAULT_AUDIO_PATH, 'rb') as src, open(file_path, 'wb') as dst:
                    dst.write(src.read())
                logger.info(f"Создана копия заготовленного аудиофайла {file_path} для пользователя {tg_id}")
                return file_path
            except Exception as e:
                logger.error(f"Ошибка при копировании заготовленного аудиофайла: {e}")
                return None
        else:
            # Если заготовленный файл не существует, создаем пустой файл
            try:
                with open(file_path, 'wb') as f:
                    # Записываем минимальный MP3-заголовок
                    f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00')
                logger.info(f"Создан пустой аудиофайл {file_path} для пользователя {tg_id}")
                return file_path
            except Exception as e:
                logger.error(f"Ошибка при создании пустого аудиофайла: {e}")
                return None
    
    # Ограничение на количество слов
    words = text.split()
    if len(words) > 250:
        text = " ".join(words[:250]) + "..."
        logger.warning(f"Текст для пользователя {tg_id} был обрезан до 250 слов")
    
    # Формирование уникального имени файла
    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(TMP_DIR, f"{tg_id}_{file_uuid}.mp3")
    
    # Подготовка запроса к API
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        # Отправка запроса и сохранение результата
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    # Сохранение MP3 файла
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(await response.read())
                    
                    logger.info(f"Создан аудиофайл {file_path} для пользователя {tg_id}")
                    return file_path
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка API ElevenLabs: {response.status} - {error_text}")
                    # В случае ошибки API также используем заглушку
                    return await _generate_fallback_audio(tg_id)
    except Exception as e:
        logger.error(f"Ошибка при генерации голосового сообщения: {e}")
        # В случае исключения также используем заглушку
        return await _generate_fallback_audio(tg_id)

async def _generate_fallback_audio(tg_id: int) -> Optional[str]:
    """
    Создает заглушку аудиофайла в случае ошибки API.
    
    Args:
        tg_id: ID пользователя в Telegram.
        
    Returns:
        Optional[str]: Путь к созданному аудиофайлу или None в случае ошибки.
    """
    # Формирование уникального имени файла
    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(TMP_DIR, f"{tg_id}_{file_uuid}.mp3")
    
    try:
        # Создаем минимальный MP3 файл
        with open(file_path, 'wb') as f:
            # Записываем минимальный MP3-заголовок
            f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00')
        logger.info(f"Создан запасной аудиофайл {file_path} для пользователя {tg_id}")
        return file_path
    except Exception as e:
        logger.error(f"Ошибка при создании запасного аудиофайла: {e}")
        return None

async def delete_voice_file(file_path: str) -> bool:
    """
    Удаление временного аудиофайла.
    
    Args:
        file_path: Путь к файлу.
        
    Returns:
        bool: True, если файл успешно удален, иначе False.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Удален временный аудиофайл {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {file_path}: {e}")
        return False

# Тексты медитаций для разных фокусов
MEDITATION_TEXTS = {
    "relax": """
    Сделайте глубокий вдох. Почувствуйте, как воздух наполняет ваши легкие. Медленно выдохните, отпуская напряжение.
    Сосредоточьтесь на своем дыхании. Вдох... выдох... Позвольте каждому вдоху принести спокойствие, а каждому выдоху - унести беспокойство.
    Расслабьте мышцы лица, шеи, плеч. Почувствуйте, как тяжесть покидает ваше тело.
    С каждым вдохом вы становитесь все более расслабленными. Ваше тело наполняется легкостью.
    Просто наблюдайте за своими мыслями, не оценивая их. Позвольте им приходить и уходить, как облака в небе.
    Вы в безопасности. Вы спокойны. Вы расслаблены.
    Насладитесь этим состоянием покоя.
    """,
    
    "focus": """
    Примите удобное положение и закройте глаза. Обратите внимание на свое дыхание.
    Сделайте глубокий вдох через нос и медленный выдох через рот.
    Сосредоточьтесь на одной точке. Это может быть ваше дыхание или ощущение в определенной части тела.
    Если ваш ум начинает блуждать, мягко верните внимание к точке фокуса.
    Представьте, что вы смотрите на свои мысли со стороны, не вовлекаясь в них.
    Почувствуйте, как ясность и концентрация наполняют ваш разум.
    Вы полностью присутствуете в настоящем моменте. Здесь и сейчас.
    """,
    
    "sleep": """
    Устройтесь поудобнее и закройте глаза. Почувствуйте, как ваше тело погружается в поверхность под вами.
    Сделайте глубокий вдох и медленный выдох. Позвольте своему телу стать тяжелым.
    Начните расслаблять каждую часть тела, начиная с пальцев ног и двигаясь вверх.
    Пальцы ног... ступни... лодыжки... голени... колени... бедра...
    Живот... грудь... плечи... руки... кисти... пальцы рук...
    Шея... лицо... голова...
    Все ваше тело теперь полностью расслаблено и готово к глубокому, восстанавливающему сну.
    Позвольте себе погрузиться в это приятное состояние между бодрствованием и сном.
    Каждый вдох приближает вас к спокойному, глубокому сну.
    """,
    
    "default": """
    Сядьте или лягте в удобном положении. Позвольте своему телу расслабиться.
    Сделайте глубокий вдох, наполняя легкие воздухом. Медленно выдохните, отпуская напряжение.
    Почувствуйте, как с каждым вдохом в вас входит спокойствие, а с каждым выдохом уходят тревоги и стресс.
    Сосредоточьтесь на своем дыхании. Просто наблюдайте за ним, не пытаясь его контролировать.
    Если в голову приходят мысли, просто отпустите их, возвращаясь к дыханию.
    Почувствуйте, как ваше тело становится тяжелее, а ум - спокойнее.
    Насладитесь этим моментом покоя и тишины.
    Вы в безопасности. Вы спокойны. Вы присутствуете здесь и сейчас.
    """
} 