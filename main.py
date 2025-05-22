import asyncio
import logging
import os
import signal
import sys
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
        
        # Обработка только SIGINT (Ctrl+C), игнорируем SIGTERM чтобы бот продолжал работать
        def signal_handler(sig, frame):
            if sig == signal.SIGINT:
                logger.info("Получен сигнал SIGINT (Ctrl+C), останавливаем бота...")
                asyncio.create_task(dp.stop_polling())
        
        # Регистрируем обработчик только для SIGINT
        signal.signal(signal.SIGINT, signal_handler)
        
        # Запуск поллинга с параметрами для непрерывной работы
        await dp.start_polling(
            bot, 
            allowed_updates=allowed_updates,
            polling_timeout=60,  # Увеличиваем таймаут
            handle_signals=False,  # Отключаем встроенную обработку сигналов
            close_bot_session=True
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        # Добавляем повторный запуск бота при критической ошибке
        logger.info("Попытка перезапуска бота через 5 секунд...")
        await asyncio.sleep(5)
        await main()  # Рекурсивный перезапуск

if __name__ == "__main__":
    # Обрабатываем исключения на верхнем уровне для предотвращения остановки бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print("Перезапуск бота...")
        os.execv(sys.executable, [sys.executable] + sys.argv) 