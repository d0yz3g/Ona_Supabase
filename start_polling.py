#!/usr/bin/env python
"""
Скрипт для запуска бота в режиме long polling
Используйте этот скрипт как запасной вариант, если webhook не работает
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POLLING] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("polling_bot.log")
    ]
)
logger = logging.getLogger("polling_bot")

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена. Укажите BOT_TOKEN в .env или переменных окружения")
    sys.exit(1)

# Создаем роутер
router = Router()

# Обработчик команды /start
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обработчик команды /start
    """
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(f"👋 Привет, {hbold(message.from_user.full_name)}!\n\nЯ Она - твой бот-помощник.\n\nЯ могу помочь тебе разобраться в себе и своих эмоциях.\n\nНапиши /help чтобы узнать, что я умею.")

# Обработчик команды /help
@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """
    Обработчик команды /help
    """
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    await message.answer("📋 Доступные команды:\n\n/start - Начать диалог\n/help - Показать эту справку\n/about - О боте\n/meditate - Получить медитацию")

# Обработчик команды /about
@router.message(Command("about"))
async def command_about_handler(message: Message) -> None:
    """
    Обработчик команды /about
    """
    logger.info(f"Получена команда /about от пользователя {message.from_user.id}")
    await message.answer("ℹ️ Я - Она, бот-помощник, созданный чтобы помогать тебе в трудные моменты. Я использую современные технологии искусственного интеллекта для анализа твоих сообщений и предоставления поддержки.")

# Обработчик команды /meditate
@router.message(Command("meditate"))
async def command_meditate_handler(message: Message) -> None:
    """
    Обработчик команды /meditate
    """
    logger.info(f"Получена команда /meditate от пользователя {message.from_user.id}")
    await message.answer("🧘‍♀️ Медитация поможет тебе успокоиться и сосредоточиться. Глубоко вдохни и медленно выдохни. Повторяй этот процесс, концентрируясь на своем дыхании.")

# Обработчик для всех текстовых сообщений
@router.message()
async def echo_handler(message: Message) -> None:
    """
    Обработчик для всех текстовых сообщений
    """
    logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text}")
    await message.answer(f"🤖 Ты написал: {message.text}\n\nВ будущих версиях я смогу поддерживать полноценный диалог.")

async def main() -> None:
    """
    Основная функция для запуска бота
    """
    logger.info("=== Запуск бота в режиме long polling ===")
    
    # Отключаем webhook, если он был установлен
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        import requests
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Webhook успешно отключен")
        else:
            logger.warning(f"⚠️ Не удалось отключить webhook: {response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отключении webhook: {e}")
    
    # Инициализируем бота и диспетчера
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Регистрируем роутер
    dp.include_router(router)
    
    # Пропускаем накопившиеся обновления и запускаем long polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Бот запущен в режиме long polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 