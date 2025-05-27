#!/usr/bin/env python
"""
Скрипт для запуска бота в режиме long polling
Используйте этот скрипт как запасной вариант, если webhook не работает
"""

import os
import sys
import logging
import asyncio
import threading
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

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

# Установка переменной окружения WEBHOOK_MODE в значение false
os.environ["WEBHOOK_MODE"] = "false"

# Запускаем health check сервер в отдельном потоке
def start_health_check():
    try:
        from health_check import run_health_server_in_thread
        health_thread = run_health_server_in_thread()
        logger.info("Health check сервер запущен в отдельном потоке")
        return health_thread
    except Exception as e:
        logger.error(f"Ошибка при запуске health check сервера: {e}")
        return None

async def setup_bot():
    """
    Настраивает и возвращает экземпляр бота
    """
    # Получаем токен бота
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ Переменная BOT_TOKEN не найдена. Укажите BOT_TOKEN в .env или переменных окружения")
        return None, None
    
    try:
        # Инициализируем бота и диспетчер
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        
        # Регистрируем базовые обработчики
        dp.message.register(cmd_start, Command("start"))
        dp.message.register(cmd_help, Command("help"))
        dp.message.register(cmd_about, Command("about"))
        dp.message.register(cmd_meditate, Command("meditate"))
        
        # Загружаем основные обработчики из main.py
        try:
            from main import setup_dispatcher
            dp = setup_dispatcher(bot)
            logger.info("✅ Обработчики из main.py успешно загружены")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить обработчики из main.py: {e}")
            logger.info("⚠️ Будут использованы только базовые обработчики")
        
        return bot, dp
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации бота: {e}")
        return None, None

# Обработчик команды /start
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start
    """
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(f"👋 Привет, {message.from_user.full_name}!\n\nЯ Она - твой бот-помощник.\n\nЯ могу помочь тебе разобраться в себе и своих эмоциях.\n\nНапиши /help чтобы узнать, что я умею.")

# Обработчик команды /help
async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help
    """
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    await message.answer("📋 Доступные команды:\n\n/start - Начать диалог\n/help - Показать эту справку\n/about - О боте\n/meditate - Получить медитацию")

# Обработчик команды /about
async def cmd_about(message: Message) -> None:
    """
    Обработчик команды /about
    """
    logger.info(f"Получена команда /about от пользователя {message.from_user.id}")
    await message.answer("ℹ️ Я - Она, бот-помощник, созданный чтобы помогать тебе в трудные моменты. Я использую современные технологии искусственного интеллекта для анализа твоих сообщений и предоставления поддержки.")

# Обработчик команды /meditate
async def cmd_meditate(message: Message) -> None:
    """
    Обработчик команды /meditate
    """
    logger.info(f"Получена команда /meditate от пользователя {message.from_user.id}")
    await message.answer("🧘‍♀️ Медитация поможет тебе успокоиться и сосредоточиться. Глубоко вдохни и медленно выдохни. Повторяй этот процесс, концентрируясь на своем дыхании.")

async def main() -> None:
    """
    Основная функция для запуска бота
    """
    logger.info("=== Запуск бота в режиме long polling ===")
    
    # Запуск health check сервера
    health_thread = start_health_check()
    
    # Настраиваем бота и диспетчер
    bot, dp = await setup_bot()
    if not bot or not dp:
        logger.error("❌ Не удалось настроить бота. Завершение работы.")
        return
    
    try:
        # Отключаем webhook, если он был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook успешно отключен")
        
        # Запускаем планировщик задач (если есть)
        try:
            from main import start_scheduler
            asyncio.create_task(start_scheduler())
            logger.info("✅ Планировщик задач запущен")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось запустить планировщик задач: {e}")
        
        # Запускаем бота в режиме long polling
        logger.info("🤖 Бот запущен в режиме long polling")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}") 