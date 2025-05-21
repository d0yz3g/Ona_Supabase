import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from db import Database
from services.scheduler import ReminderScheduler

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация роутера
router = Router(name="reminder")

# Сообщения для пользователя
REMINDER_ENABLED_MESSAGE = (
    "✅ Напоминания включены!\n\n"
    "Теперь вы будете получать ежедневные напоминания о практике в 20:00.\n"
    "Чтобы отключить напоминания, используйте команду /reminder_off."
)

REMINDER_DISABLED_MESSAGE = (
    "❌ Напоминания отключены.\n\n"
    "Вы больше не будете получать ежедневные напоминания.\n"
    "Чтобы снова включить напоминания, используйте команду /reminder_on."
)

REMINDER_ALREADY_ENABLED_MESSAGE = (
    "ℹ️ Напоминания уже включены.\n\n"
    "Вы уже получаете ежедневные напоминания о практике в 20:00.\n"
    "Чтобы отключить их, используйте команду /reminder_off."
)

REMINDER_ALREADY_DISABLED_MESSAGE = (
    "ℹ️ Напоминания уже отключены.\n\n"
    "Если вы хотите получать ежедневные напоминания о практике, "
    "используйте команду /reminder_on."
)

# Инициализация объектов
db = Database()
scheduler = None  # Будет инициализирован в main.py

def set_scheduler(reminder_scheduler: ReminderScheduler):
    """Установка экземпляра планировщика."""
    global scheduler
    scheduler = reminder_scheduler

@router.message(Command("reminder_on"))
async def enable_reminder(message: Message):
    """Обработчик команды для включения напоминаний."""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил включение напоминаний")
    
    # Получаем пользователя из БД
    user = db.get_user_by_tg_id(user_id)
    
    if not user:
        # Если пользователь не найден, добавляем его
        db_user_id = db.add_user(
            user_id, 
            f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        )
        logger.info(f"Создан новый пользователь {user_id} (db_id: {db_user_id})")
    else:
        db_user_id = user["id"]
    
    # Проверяем, включены ли уже напоминания
    reminder_status = db.get_reminder_status(db_user_id)
    
    if reminder_status and reminder_status.get("is_active", False):
        await message.answer(REMINDER_ALREADY_ENABLED_MESSAGE)
        logger.info(f"Напоминания для пользователя {user_id} уже включены")
        return
    
    # Включаем напоминания
    success = db.enable_reminder(db_user_id)
    
    if success:
        # Отправляем подтверждение и тестовое напоминание
        await message.answer(REMINDER_ENABLED_MESSAGE)
        logger.info(f"Напоминания для пользователя {user_id} включены")
        
        # Отправляем тестовое напоминание, если планировщик инициализирован
        if scheduler:
            await scheduler.send_test_reminder(user_id)
    else:
        await message.answer(
            "❌ Произошла ошибка при включении напоминаний. Пожалуйста, попробуйте позже."
        )
        logger.error(f"Ошибка при включении напоминаний для пользователя {user_id}")

@router.message(Command("reminder_off"))
async def disable_reminder(message: Message):
    """Обработчик команды для отключения напоминаний."""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил отключение напоминаний")
    
    # Получаем пользователя из БД
    user = db.get_user_by_tg_id(user_id)
    
    if not user:
        await message.answer(
            "ℹ️ У вас нет активных напоминаний.\n\n"
            "Чтобы включить напоминания, используйте команду /reminder_on."
        )
        return
    
    db_user_id = user["id"]
    
    # Проверяем статус напоминаний
    reminder_status = db.get_reminder_status(db_user_id)
    
    if not reminder_status or not reminder_status.get("is_active", False):
        await message.answer(REMINDER_ALREADY_DISABLED_MESSAGE)
        logger.info(f"Напоминания для пользователя {user_id} уже отключены")
        return
    
    # Отключаем напоминания
    success = db.disable_reminder(db_user_id)
    
    if success:
        await message.answer(REMINDER_DISABLED_MESSAGE)
        logger.info(f"Напоминания для пользователя {user_id} отключены")
    else:
        await message.answer(
            "❌ Произошла ошибка при отключении напоминаний. Пожалуйста, попробуйте позже."
        )
        logger.error(f"Ошибка при отключении напоминаний для пользователя {user_id}")

@router.message(Command("reminder_status"))
async def check_reminder_status(message: Message):
    """Проверка статуса напоминаний."""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил статус напоминаний")
    
    # Получаем пользователя из БД
    user = db.get_user_by_tg_id(user_id)
    
    if not user:
        await message.answer(
            "ℹ️ У вас нет активных напоминаний.\n\n"
            "Чтобы включить напоминания, используйте команду /reminder_on."
        )
        return
    
    db_user_id = user["id"]
    
    # Проверяем статус напоминаний
    reminder_status = db.get_reminder_status(db_user_id)
    
    if reminder_status and reminder_status.get("is_active", False):
        await message.answer(
            "✅ Напоминания включены.\n\n"
            "Вы получаете ежедневные напоминания о практике в 20:00.\n"
            "Чтобы отключить напоминания, используйте команду /reminder_off."
        )
    else:
        await message.answer(
            "❌ Напоминания отключены.\n\n"
            "Чтобы включить напоминания, используйте команду /reminder_on."
        )

@router.message(Command("help_reminder"))
async def help_reminder(message: Message):
    """Справка по командам управления напоминаниями."""
    help_text = [
        "🔔 Управление напоминаниями",
        "",
        "Доступные команды:",
        "- /reminder_on - включить ежедневные напоминания",
        "- /reminder_off - отключить напоминания",
        "- /reminder_status - проверить текущий статус напоминаний",
        "- /help_reminder - показать эту справку",
        "",
        "Напоминания приходят каждый день в 20:00 по вашему локальному времени."
    ]
    
    await message.answer("\n".join(help_text))
    logger.info(f"Отправлена справка по напоминаниям пользователю {message.from_user.id}") 