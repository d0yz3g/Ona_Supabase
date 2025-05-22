import asyncio
import logging
import os
import signal
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорт основного модуля бота (все обработчики и логика перенесены в button_bot.py)
from button_bot import (
    main_router, 
    profile_router, 
    reflect_router, 
    meditate_router, 
    reminder_router, 
    survey_router,
    scheduler,
    reminder_users,
    send_reminder
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

async def main():
    try:
        # Инициализация хранилища и бота
        storage = MemoryStorage()
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=storage)
        
        # Регистрация роутеров
        dp.include_router(main_router)
        dp.include_router(profile_router)
        dp.include_router(reflect_router)
        dp.include_router(meditate_router)
        dp.include_router(reminder_router)
        dp.include_router(survey_router)
        
        # Запуск планировщика заданий, если есть активные напоминания
        if not scheduler.running and reminder_users:
            scheduler.start()
        
        # Запуск бота
        logger.info("Бот запущен, ожидание сообщений...")
        
        # Устанавливаем allowed_updates для оптимизации работы
        allowed_updates = ["message", "callback_query"]
        
        # Проверяем соединение с Telegram API
        try:
            await bot.get_me()
            logger.info("Соединение с Telegram API установлено успешно")
        except Exception as e:
            logger.error(f"Ошибка при подключении к Telegram API: {e}")
            return
        
        # Игнорируем старые обновления для предотвращения конфликтов
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Добавляем обработку сигналов для корректного завершения
        def signal_handler(sig, frame):
            logger.info("Получен сигнал завершения, останавливаем бота...")
            asyncio.create_task(dp.stop_polling())
        
        # Регистрируем обработчик сигналов
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)
        
        # Запуск поллинга
        await dp.start_polling(
            bot, 
            allowed_updates=allowed_updates,
            polling_timeout=30,
            handle_signals=True,
            close_bot_session=True
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        # В случае ошибки, пытаемся закрыть сессию
        try:
            await bot.session.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 