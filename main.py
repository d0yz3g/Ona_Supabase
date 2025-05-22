import asyncio
import logging
import os
import signal
import sys
import time
import socket
import psutil
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

# Настройка логирования с приоритетом на вывод в консоль для Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Вывод в stdout для Railway
        logging.FileHandler("bot.log")      # Файл для локальной отладки
    ]
)
logger = logging.getLogger("ona_bot")

# Явный вывод информации для Railway
print("=== ONA TELEGRAM BOT STARTING ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    print("КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден")
    exit(1)
else:
    print("BOT_TOKEN найден успешно")

# Файл блокировки для предотвращения запуска нескольких экземпляров
LOCK_PORT = 44223  # Уникальный порт для блокировки

def is_bot_already_running():
    """
    Проверяет, запущен ли уже экземпляр бота, используя TCP сокет.
    Возвращает True, если бот уже запущен, иначе False.
    """
    try:
        # Пытаемся создать серверный сокет на указанном порту
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', LOCK_PORT))
        sock.listen(1)
        # Если успешно - значит бот не запущен
        return False
    except socket.error:
        # Если ошибка - порт занят, значит бот уже запущен
        logger.warning(f"Порт {LOCK_PORT} уже занят, возможно бот уже запущен")
        print(f"ПРЕДУПРЕЖДЕНИЕ: Возможно, бот уже запущен (порт {LOCK_PORT} занят)")
        return True

def kill_other_bot_instances():
    """
    Попытка завершить другие экземпляры бота
    """
    current_pid = os.getpid()
    logger.info(f"Текущий PID: {current_pid}")
    print(f"Текущий PID процесса: {current_pid}")
    
    # Ищем другие Python процессы, запущенные с main.py
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Проверяем, что это Python процесс, запускающий main.py, но не текущий процесс
            if proc.info['pid'] != current_pid and proc.info['name'] == 'python':
                cmdline = proc.info['cmdline']
                if cmdline and any('main.py' in cmd for cmd in cmdline):
                    logger.warning(f"Найден другой экземпляр бота: PID {proc.info['pid']}")
                    print(f"ВНИМАНИЕ: Найден другой экземпляр бота с PID {proc.info['pid']}")
                    
                    # Завершаем процесс
                    try:
                        proc.terminate()
                        logger.info(f"Процесс с PID {proc.info['pid']} успешно завершен")
                        print(f"Процесс с PID {proc.info['pid']} завершен")
                    except Exception as e:
                        logger.error(f"Не удалось завершить процесс: {e}")
                        print(f"Ошибка при завершении процесса: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

async def main():
    try:
        # Проверяем, запущен ли уже бот
        if is_bot_already_running():
            # Пытаемся завершить другие экземпляры
            kill_other_bot_instances()
            logger.warning("Возможен конфликт с другим экземпляром бота. Проверьте процессы.")
            print("ПРЕДУПРЕЖДЕНИЕ: Возможен конфликт с другим запущенным ботом.")
            # Делаем паузу, чтобы другие процессы успели завершиться
            await asyncio.sleep(5)
        
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
            print("Планировщик напоминаний запущен")
        
        # Запуск бота
        logger.info("Бот запущен, ожидание сообщений...")
        print("=== ONA BOT ЗАПУЩЕН И ГОТОВ К РАБОТЕ ===")
        
        # Устанавливаем allowed_updates для оптимизации работы
        allowed_updates = ["message", "callback_query"]
        
        # Сначала сбрасываем webhook и удаляем старые обновления
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удален, старые обновления очищены")
        print("Старые обновления удалены")
        
        # Проверяем соединение с Telegram API
        try:
            bot_info = await bot.get_me()
            logger.info(f"Соединение с Telegram API установлено успешно. Имя бота: @{bot_info.username}")
            print(f"Бот @{bot_info.username} успешно подключен к Telegram API")
        except Exception as e:
            logger.error(f"Ошибка при подключении к Telegram API: {e}")
            print(f"ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
            # Пробуем еще раз через 5 секунд
            await asyncio.sleep(5)
            bot_info = await bot.get_me()
            logger.info(f"Соединение с Telegram API установлено со второй попытки. Имя бота: @{bot_info.username}")
            print(f"Повторное подключение успешно: @{bot_info.username}")
        
        # Обработка сигналов
        # Игнорируем SIGTERM чтобы бот продолжал работать при мягкой остановке контейнера
        def signal_handler(sig, frame):
            if sig == signal.SIGINT:
                logger.info("Получен сигнал SIGINT (Ctrl+C), останавливаем бота...")
                print("Получен сигнал остановки SIGINT, завершение работы...")
                asyncio.create_task(bot.session.close())
                asyncio.create_task(dp.stop_polling())
            elif sig == signal.SIGTERM:
                logger.info("Получен сигнал SIGTERM, игнорируем для предотвращения остановки")
                print("Получен сигнал SIGTERM, продолжаем работу...")
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
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
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        # Добавляем повторный запуск бота при критической ошибке
        logger.info("Попытка перезапуска бота через 5 секунд...")
        print("Перезапуск через 5 секунд...")
        await asyncio.sleep(5)
        try:
            await main()  # Рекурсивный перезапуск
        except Exception as restart_error:
            logger.error(f"Не удалось перезапустить бота: {restart_error}")
            print(f"ОШИБКА ПЕРЕЗАПУСКА: {restart_error}")
            raise

if __name__ == "__main__":
    # Обрабатываем исключения на верхнем уровне для предотвращения остановки бота
    try:
        print("Запуск основного цикла бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print("Перезапуск бота...")
        time.sleep(3)
        os.execv(sys.executable, [sys.executable] + sys.argv) 