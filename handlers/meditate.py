import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from services.tts import generate_voice, delete_voice_file, MEDITATION_TEXTS

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация роутера
meditate_router = Router(name="meditation")

@meditate_router.message(Command("meditate"))
async def meditate_command(message: Message):
    """Обработчик команды /meditate с возможностью указания типа медитации."""
    # Получаем аргументы команды
    args = message.text.split()
    
    # Определяем тип медитации
    meditation_type = "default"
    if len(args) > 1 and args[1].lower() in MEDITATION_TEXTS:
        meditation_type = args[1].lower()
    
    # Получаем текст медитации
    meditation_text = MEDITATION_TEXTS[meditation_type]
    
    # Отправляем сообщение о начале генерации
    await message.answer(
        f"Подготавливаю медитацию '{meditation_type}'. Это займет несколько секунд..."
    )
    
    # Генерируем голосовой файл
    voice_file_path = await generate_voice(
        text=meditation_text,
        tg_id=message.from_user.id
    )
    
    if voice_file_path:
        try:
            # Отправляем голосовое сообщение
            await message.answer_voice(
                voice=FSInputFile(voice_file_path),
                caption="Найдите тихое место, где вас никто не побеспокоит. Расслабьтесь и следуйте инструкциям."
            )
            logger.info(f"Отправлена медитация типа '{meditation_type}' пользователю {message.from_user.id}")
            
            # Удаляем временный файл
            await delete_voice_file(voice_file_path)
        except Exception as e:
            logger.error(f"Ошибка при отправке голосового сообщения: {e}")
            await message.answer("Произошла ошибка при отправке медитации. Пожалуйста, попробуйте позже.")
            # В случае ошибки также пытаемся удалить файл
            await delete_voice_file(voice_file_path)
    else:
        await message.answer(
            "К сожалению, не удалось сгенерировать медитацию. Пожалуйста, попробуйте позже."
        )

@meditate_router.message(Command("help_meditate"))
async def help_meditate(message: Message):
    """Справка по использованию команды /meditate и доступным типам медитаций."""
    help_text = [
        "🧘‍♀️ Команда /meditate позволяет получить голосовую медитацию.",
        "",
        "Варианты использования:",
        "- /meditate - медитация по умолчанию",
        "- /meditate relax - медитация для расслабления",
        "- /meditate focus - медитация для концентрации",
        "- /meditate sleep - медитация для сна",
        "",
        "Найдите тихое место, устройтесь поудобнее и позвольте себе полностью расслабиться."
    ]
    
    await message.answer("\n".join(help_text))
    logger.info(f"Отправлена справка по медитациям пользователю {message.from_user.id}") 