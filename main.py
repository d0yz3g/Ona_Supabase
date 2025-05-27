import asyncio
import logging
import os
import sys
import tempfile  # Для создания временного файла блокировки
import socket  # Для получения имени хоста
import signal  # Для обработки сигналов завершения
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.types import BufferedInputFile

# Загружаем переменные окружения из .env
load_dotenv()

# Проверка режима работы (webhook или polling)
WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "false").lower() in ("true", "1", "yes")
# Переменная для определения запуска на Railway
RAILWAY_ENV = os.getenv("RAILWAY", "false").lower() in ("true", "1", "yes") or os.getenv("RAILWAY_STATIC_URL") is not None

# Проверка наличия переменной окружения DATABASE_URL для PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# Импортируем fcntl только для Unix-подобных систем
if sys.platform != 'win32':
    try:
        import fcntl
    except ImportError:
        fcntl = None
else:
    fcntl = None

# Блокировка для предотвращения запуска нескольких экземпляров
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'ona_bot.lock')
lock_socket = None
lock_file_handle = None

# Настройка логирования
try:
    from railway_logging import setup_railway_logging, railway_print
    # Настраиваем логирование для Railway
    logger = setup_railway_logging("ona_bot", logging.INFO)
    railway_print("Логирование для Railway настроено успешно", "INFO")
except ImportError:
    # Стандартная настройка логирования, если модуль railway_logging не найден
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log")
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Определяем функцию railway_print, если модуль railway_logging не найден
    def railway_print(message, level="INFO"):
        prefix = "ИНФО"
        if level.upper() == "ERROR":
            prefix = "ОШИБКА"
        elif level.upper() == "WARNING":
            prefix = "ПРЕДУПРЕЖДЕНИЕ"
        elif level.upper() == "DEBUG":
            prefix = "ОТЛАДКА"
        print(f"{prefix}: {message}")
        sys.stdout.flush()

def acquire_lock():
    """
    Пытается получить блокировку, предотвращающую запуск нескольких экземпляров.
    
    Returns:
        bool: True, если блокировка получена успешно, False в противном случае
    """
    global lock_socket, lock_file_handle
    
    # В режиме webhook на Railway блокировка не нужна
    if WEBHOOK_MODE and RAILWAY_ENV:
        railway_print("Режим webhook на Railway: блокировка не используется")
        return True
    
    try:
        # Создаем именованный сокет для Windows
        if sys.platform == 'win32':
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Пытаемся занять порт 50000 (или любой другой специфичный для вашего приложения)
            try:
                lock_socket.bind(('localhost', 50000))
                railway_print("Блокировка получена (Windows)")
                return True
            except socket.error:
                railway_print("Блокировка уже занята другим процессом (Windows)")
                return False
        # Для Unix-подобных систем используем файловую блокировку
        elif fcntl:
            lock_file_handle = open(LOCK_FILE, 'w')
            try:
                fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                railway_print("Блокировка получена (Unix с fcntl)")
                # Записываем PID для отладки
                lock_file_handle.write(str(os.getpid()))
                lock_file_handle.flush()
                return True
            except IOError:
                railway_print("Блокировка уже занята другим процессом (Unix)")
                return False
        # Если fcntl недоступен, используем альтернативный метод
        else:
            # Простая проверка на существование PID файла
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, 'r') as f:
                    pid = f.read().strip()
                    # Проверяем, существует ли процесс с таким PID
                    try:
                        pid = int(pid)
                        # Пытаемся отправить сигнал 0 процессу - это проверка на существование
                        os.kill(pid, 0)
                        railway_print(f"Блокировка уже занята процессом {pid}")
                        return False
                    except (ValueError, OSError):
                        # PID невалидный или процесс не существует
                        pass
            
            # Записываем текущий PID в файл
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            railway_print("Блокировка получена (PID файл)")
            return True
    except Exception as e:
        railway_print(f"Ошибка при получении блокировки: {e}")
        return False

def release_lock():
    """
    Освобождает блокировку, полученную с помощью acquire_lock().
    """
    global lock_socket, lock_file_handle
    
    # В режиме webhook на Railway блокировка не используется
    if WEBHOOK_MODE and RAILWAY_ENV:
        return
    
    try:
        # Освобождаем сокет для Windows
        if lock_socket:
            try:
                lock_socket.close()
                railway_print("Блокировка освобождена (Windows)")
            except Exception as e:
                railway_print(f"Ошибка при освобождении сокета: {e}")
        
        # Освобождаем файловую блокировку для Unix
        if lock_file_handle:
            try:
                if fcntl:
                    fcntl.lockf(lock_file_handle, fcntl.LOCK_UN)
                lock_file_handle.close()
                railway_print("Блокировка освобождена (Unix)")
            except Exception as e:
                railway_print(f"Ошибка при освобождении файловой блокировки: {e}")
        
        # Удаляем PID файл, если использовался такой метод
        if os.path.exists(LOCK_FILE) and (sys.platform == 'win32' or not fcntl):
            try:
                os.remove(LOCK_FILE)
                railway_print("PID файл удален")
            except Exception as e:
                railway_print(f"Ошибка при удалении PID файла: {e}")
    except Exception as e:
        railway_print(f"Ошибка при освобождении блокировки: {e}")

# Обработчики сигналов для корректного завершения работы
def signal_handler(sig, frame):
    """Обработчик сигналов завершения"""
    railway_print(f"Получен сигнал {sig}, завершаем работу...")
    release_lock()
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Информация о запуске
railway_print("=== ONA TELEGRAM BOT STARTING ===", "INFO")
railway_print(f"Python version: {sys.version}", "INFO")
railway_print(f"Current working directory: {os.getcwd()}", "INFO")
railway_print(f"Files in directory: {[f for f in os.listdir('.') if f.endswith('.py')]}", "INFO")
railway_print(f"Режим работы: {'webhook' if WEBHOOK_MODE else 'polling'}", "INFO")
railway_print(f"Среда Railway: {'да' if RAILWAY_ENV else 'нет'}", "INFO")

if DATABASE_URL:
    railway_print(f"Обнаружена переменная DATABASE_URL: PostgreSQL будет использоваться как база данных", "INFO")
else:
    railway_print("Переменная DATABASE_URL не найдена: будет использоваться локальная SQLite база данных", "INFO")

# Загружаем API токен из .env файла
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в .env файле")
    railway_print("BOT_TOKEN не найден в .env файле", "ERROR")
    sys.exit(1)
else:
    railway_print("BOT_TOKEN найден успешно", "INFO")

# Проверка наличия psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("Библиотека psutil успешно импортирована")
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("Библиотека psutil не установлена, некоторые функции будут недоступны")

# Проверка webhook-режима
if WEBHOOK_MODE:
    webhook_url = os.getenv("WEBHOOK_URL")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if webhook_url:
        railway_print(f"Webhook URL: {webhook_url}", "INFO")
    elif railway_public_domain:
        webhook_url = f"https://{railway_public_domain}/webhook/{BOT_TOKEN}"
        railway_print(f"Сформирован Webhook URL из Railway домена: {webhook_url}", "INFO")
    else:
        railway_print("ВНИМАНИЕ: WEBHOOK_URL не указан, но выбран режим webhook", "WARNING")
        railway_print("Переключение на режим polling, так как URL webhook не настроен", "INFO")
        # Переключаемся на режим polling, так как webhook URL не настроен
        WEBHOOK_MODE = False

# Определяем функцию для получения клавиатуры
def get_main_keyboard():
    # ... существующий код ...
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Профиль"), KeyboardButton(text="🧘 Медитация")],
            [KeyboardButton(text="💬 Помощь"), KeyboardButton(text="🔄 Рестарт")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Функция для настройки бота
def setup_bot():
    """
    Создает и настраивает экземпляр бота
    
    Returns:
        Bot: Настроенный экземпляр бота
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        logger.info("Бот инициализирован")
        return bot
    except Exception as e:
        logger.error(f"Ошибка при инициализации бота: {e}")
        railway_print(f"Ошибка при инициализации бота: {e}", "ERROR")
        sys.exit(1)

# Функция для настройки диспетчера
def setup_dispatcher(bot=None):
    """
    Создает и настраивает диспетчер сообщений
    
    Args:
        bot (Bot, optional): Экземпляр бота. Если не указан, будет создан новый.
        
    Returns:
        Dispatcher: Настроенный диспетчер сообщений
    """
    if bot is None:
        bot = setup_bot()
    
    # Создаем хранилище состояний (в памяти)
    storage = MemoryStorage()
    
    # Создаем диспетчер
    dp = Dispatcher(storage=storage)
    
    # Регистрируем базовые обработчики команд
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_help, F.text == "💬 Помощь")
    dp.message.register(cmd_api_key, Command("api_key"))
    dp.message.register(cmd_restart, Command("restart"))
    dp.message.register(cmd_restart, F.text == "🔄 Рестарт")
    
    # Импортируем и регистрируем обработчики
    try:
        # Импортируем обработчики опросов
        from survey_handler import register_survey_handlers
        register_survey_handlers(dp)
        logger.info("Обработчики опросов зарегистрированы")
    except ImportError as e:
        logger.error(f"Ошибка импорта survey_handler: {e}")
    
    try:
        # Импортируем обработчики медитаций
        from meditation_handler import register_meditation_handlers
        register_meditation_handlers(dp)
        logger.info("Обработчики медитаций зарегистрированы")
    except ImportError as e:
        logger.error(f"Ошибка импорта meditation_handler: {e}")
    
    try:
        # Импортируем обработчики диалога
        from conversation_handler import register_conversation_handlers
        register_conversation_handlers(dp)
        logger.info("Обработчики диалога зарегистрированы")
    except ImportError as e:
        logger.error(f"Ошибка импорта conversation_handler: {e}")
    
    try:
        # Импортируем обработчики голосовых сообщений
        from voice_handler import register_voice_handlers
        register_voice_handlers(dp)
        logger.info("Обработчики голосовых сообщений зарегистрированы")
    except ImportError as e:
        logger.error(f"Ошибка импорта voice_handler: {e}")
    
    try:
        # Импортируем обработчики коммуникации
        from communication_handler import register_communication_handlers
        register_communication_handlers(dp)
        logger.info("Обработчики коммуникации зарегистрированы")
    except ImportError as e:
        logger.error(f"Ошибка импорта communication_handler: {e}")
    
    return dp

async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {message.from_user.id} ({message.from_user.username})")
    railway_print(f"Получена команда /start от пользователя {message.from_user.username or message.from_user.id}", "INFO")
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я ONA - твой бот-помощник.\n"
        f"Используй команду /help, чтобы узнать, что я умею.",
        reply_markup=get_main_keyboard()
    )

async def cmd_help(message: Message):
    """Обработчик команды /help"""
    logger.info(f"Получена команда /help от пользователя {message.from_user.id} ({message.from_user.username})")
    railway_print(f"Получена команда /help от пользователя {message.from_user.username or message.from_user.id}", "INFO")
    
    help_text = (
        "Вот что я умею:\n\n"
        "📋 /profile - Показать твой профиль\n"
        "🧘 /meditate - Сгенерировать медитацию\n"
        "💬 /help - Показать это сообщение\n"
        "🔑 /api_key - Обновить API ключи\n"
        "🔄 /restart - Перезапустить бота\n\n"
        "Ты также можешь общаться со мной в свободной форме."
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

async def cmd_api_key(message: Message):
    """Обработчик команды /api_key"""
    logger.info(f"Получена команда /api_key от пользователя {message.from_user.id} ({message.from_user.username})")
    railway_print(f"Получена команда /api_key от пользователя {message.from_user.username or message.from_user.id}", "INFO")
    
    await message.answer(
        "Чтобы обновить API ключи, отредактируйте файл .env и перезапустите бота."
    )

async def cmd_restart(message: Message):
    """Обработчик команды /restart"""
    logger.info(f"Получена команда /restart от пользователя {message.from_user.id} ({message.from_user.username})")
    railway_print(f"Получена команда /restart от пользователя {message.from_user.username or message.from_user.id}", "INFO")
    
    await message.answer("Перезапуск бота...")
    # Перезапуск будет выполнен внешним скриптом или службой
    release_lock()
    sys.exit(0)

async def start_scheduler():
    """Запускает планировщик задач для напоминаний"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from reminder_handler import send_reminder
        
        scheduler = AsyncIOScheduler()
        
        # Настраиваем время отправки напоминаний
        reminder_hour = int(os.getenv("REMINDER_HOUR", 20))
        reminder_minute = int(os.getenv("REMINDER_MINUTE", 0))
        
        # Добавляем задачу напоминания
        scheduler.add_job(
            send_reminder,
            "cron",
            hour=reminder_hour,
            minute=reminder_minute
        )
        
        # Запускаем планировщик
        scheduler.start()
        logger.info(f"Планировщик напоминаний запущен (время: {reminder_hour}:{reminder_minute:02d})")
    except ImportError as e:
        logger.error(f"Ошибка импорта модулей для планировщика: {e}")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")

async def start_health_check_server():
    """Запускает сервер для проверки состояния бота"""
    try:
        # Импортируем и запускаем health check сервер
        from health_check import run_health_server_in_thread
        health_thread = run_health_server_in_thread()
        logger.info("Health check сервер запущен")
        return health_thread
    except ImportError as e:
        logger.error(f"Ошибка импорта health_check: {e}")
    except Exception as e:
        logger.error(f"Ошибка при запуске health check сервера: {e}")
    return None

async def main():
    """
    Основная функция для запуска бота
    """
    # Проверяем режим работы
    if WEBHOOK_MODE:
        webhook_url = os.getenv("WEBHOOK_URL")
        railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        
        # Проверяем наличие URL для webhook
        if not webhook_url and not railway_public_domain:
            railway_print("WEBHOOK_MODE=true, но URL webhook не настроен. Переключение на режим polling", "WARNING")
            # Выполняем код для режима polling
        else:
            railway_print("Бот настроен для работы в режиме webhook", "INFO")
            railway_print("Для запуска webhook-сервера используйте: python webhook_server.py", "INFO")
            
            # Если файл запущен напрямую, выводим инструкцию
            if __name__ == "__main__":
                railway_print("Webhook режим активирован. Запуск через polling не будет выполнен", "WARNING")
                railway_print("Для запуска в режиме webhook выполните: python webhook_server.py", "INFO")
                
                # Проверяем наличие файла webhook_server.py
                if os.path.exists("webhook_server.py"):
                    railway_print("Найден файл webhook_server.py", "INFO")
                else:
                    railway_print("ОШИБКА: Файл webhook_server.py не найден", "ERROR")
                    railway_print("Создайте файл webhook_server.py или измените режим на polling (WEBHOOK_MODE=false)", "ERROR")
            
            # Возвращаем, чтобы не запускать polling в режиме webhook
            return
    
    # Пытаемся получить блокировку, чтобы предотвратить запуск нескольких экземпляров
    if not acquire_lock():
        logger.error("Не удалось получить блокировку. Возможно, другой экземпляр бота уже запущен.")
        railway_print("ОШИБКА: Не удалось получить блокировку. Возможно, другой экземпляр бота уже запущен.", "ERROR")
        return
    
    try:
        # Настраиваем бота
        bot = setup_bot()
        
        # Настраиваем диспетчер
        dp = setup_dispatcher(bot)
        
        # Добавляем общий обработчик текстовых сообщений для логирования
        @dp.message(F.text)
        async def handle_text_message(message: Message):
            logger.info(f"Получено текстовое сообщение от пользователя {message.from_user.id} ({message.from_user.username}): {message.text[:50]}...")
            railway_print(f"Получено сообщение от пользователя {message.from_user.username or message.from_user.id}: {message.text[:50]}...", "INFO")
        
        # Запускаем планировщик напоминаний
        asyncio.create_task(start_scheduler())
        
        # Запускаем health check сервер
        health_task = asyncio.create_task(start_health_check_server())
        
        # Создаем веб-сервер для поддержки мониторинга
        try:
            from aiohttp import web
            app = web.Application()
            
            async def health_check(request):
                return web.Response(text="Бот работает в режиме polling", status=200)
            
            app.router.add_get("/", health_check)
            app.router.add_get("/health", health_check)
            
            port = int(os.environ.get("PORT", 8080))
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()
            logger.info(f"Веб-сервер запущен на порту {port}")
        except Exception as e:
            logger.error(f"Ошибка при запуске веб-сервера: {e}")
        
        try:
            # Удаляем webhook (если был установлен)
            await bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем бота в режиме long polling
            logger.info("Запуск бота в режиме polling...")
            railway_print("Бот запущен в режиме polling, ожидание сообщений...", "INFO")
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            railway_print(f"Ошибка при запуске бота: {e}", "ERROR")
    finally:
        # Освобождаем блокировку при завершении
        release_lock()

if __name__ == "__main__":
    try:
        # Запускаем бота
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Обрабатываем нормальное завершение
        logger.info("Бот остановлен")
    except Exception as e:
        # Обрабатываем непредвиденные ошибки
        logger.error(f"Критическая ошибка: {e}")
        railway_print(f"ОШИБКА: {e}", "ERROR")
    finally:
        # Освобождаем блокировку
        release_lock() 