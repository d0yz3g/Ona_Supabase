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

# Флаг для корректного завершения работы
shutdown_event = asyncio.Event()

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

def acquire_lock():
    """
    Пытается получить блокировку, предотвращающую запуск нескольких экземпляров.
    
    Returns:
        bool: True, если блокировка получена успешно, False в противном случае
    """
    global lock_socket, lock_file_handle
    
    try:
        # Создаем именованный сокет для Windows
        if sys.platform == 'win32':
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Пытаемся занять порт 50000 (или любой другой специфичный для вашего приложения)
            try:
                lock_socket.bind(('localhost', 50000))
                print("Блокировка получена (Windows)")
                return True
            except socket.error:
                print("Блокировка уже занята другим процессом (Windows)")
                return False
        # Для Unix-подобных систем используем файловую блокировку
        elif fcntl:
            lock_file_handle = open(LOCK_FILE, 'w')
            try:
                fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                print("Блокировка получена (Unix с fcntl)")
                return True
            except IOError:
                print("Блокировка уже занята другим процессом (Unix)")
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
                        print(f"Блокировка уже занята процессом {pid}")
                        return False
                    except (ValueError, OSError):
                        # PID невалидный или процесс не существует
                        pass
            
            # Записываем текущий PID в файл
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            print("Блокировка получена (PID файл)")
            return True
    except Exception as e:
        print(f"Ошибка при получении блокировки: {e}")
        return False

def release_lock():
    """
    Освобождает блокировку, полученную с помощью acquire_lock().
    """
    global lock_socket, lock_file_handle
    
    try:
        # Освобождаем сокет для Windows
        if lock_socket:
            try:
                lock_socket.close()
                print("Блокировка освобождена (Windows)")
            except Exception as e:
                print(f"Ошибка при освобождении сокета: {e}")
        
        # Освобождаем файловую блокировку для Unix
        if lock_file_handle:
            try:
                if fcntl:
                    fcntl.lockf(lock_file_handle, fcntl.LOCK_UN)
                lock_file_handle.close()
                print("Блокировка освобождена (Unix)")
            except Exception as e:
                print(f"Ошибка при освобождении файловой блокировки: {e}")
        
        # Удаляем PID файл, если использовался такой метод
        if os.path.exists(LOCK_FILE) and sys.platform == 'win32' or not fcntl:
            try:
                os.remove(LOCK_FILE)
                print("PID файл удален")
            except Exception as e:
                print(f"Ошибка при удалении PID файла: {e}")
    except Exception as e:
        print(f"Ошибка при освобождении блокировки: {e}")

# Загружаем переменные окружения из .env
load_dotenv()

# Проверка наличия railway_helper и его инициализация
try:
    from railway_helper import ensure_modules_available, print_railway_info
    # Проверяем и обеспечиваем наличие необходимых модулей
    print_railway_info("Инициализация Railway Helper", "INFO")
    ensure_modules_available([
        "survey_handler",
        "meditation_handler",
        "conversation_handler",
        "reminder_handler",
        "voice_handler",
        "railway_logging",
        "communication_handler"
    ])
except ImportError:
    print("БОТ: Railway Helper не найден, продолжаем без дополнительных проверок")

# Импортируем настройку логирования для Railway
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
    print("БОТ: Используется стандартное логирование (railway_logging не найден)")
    
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

# Информация о запуске
railway_print("=== ONA TELEGRAM BOT STARTING ===", "INFO")
railway_print(f"Python version: {sys.version}", "INFO")
railway_print(f"Current working directory: {os.getcwd()}", "INFO")
railway_print(f"Files in directory: {[f for f in os.listdir('.') if f.endswith('.py')]}", "INFO")

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

# Импортируем роутеры
try:
    railway_print("Импорт основных модулей бота...", "INFO")
    from survey_handler import survey_router, get_main_keyboard
    from voice_handler import voice_router
    from conversation_handler import conversation_router
    from meditation_handler import meditation_router
    from reminder_handler import reminder_router, scheduler
    from communication_handler import communication_router
    railway_print("Все модули успешно импортированы", "INFO")
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    railway_print(f"Ошибка импорта модулей: {e}", "ERROR")
    railway_print("Попытка аварийной загрузки базовых модулей...", "WARNING")
    
    # Попытка аварийной загрузки базовых модулей
    # Создаем пустые роутеры
    from aiogram import Router
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    survey_router = Router(name="survey")
    voice_router = Router(name="voice")
    conversation_router = Router(name="conversation")
    meditation_router = Router(name="meditation")
    reminder_router = Router(name="reminder")
    communication_router = Router(name="communication")
    
    # Создаем базовую клавиатуру
    def get_main_keyboard():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="💬 Помощь")]
            ],
            resize_keyboard=True
        )
    
    # Создаем пустой планировщик
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    
    railway_print("Аварийная загрузка базовых модулей выполнена", "WARNING")

# Создаем экземпляр бота и диспетчер
bot = Bot(
    token=BOT_TOKEN,
    parse_mode="HTML",  # Устанавливаем HTML-разметку по умолчанию
    disable_web_page_preview=True,  # Отключаем предпросмотр веб-страниц
    protect_content=False  # Разрешаем пересылку сообщений
)
dp = Dispatcher(storage=MemoryStorage())

# Функция для инициализации планировщика
async def start_scheduler():
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("Планировщик заданий запущен")

# Функция для корректного завершения работы бота
async def shutdown(dp, bot):
    """
    Корректно завершает работу бота, сохраняя все данные.
    
    Args:
        dp: Dispatcher
        bot: Bot
    """
    logger.info("Получен сигнал завершения работы. Корректно завершаем работу бота...")
    railway_print("Получен сигнал завершения работы. Корректно завершаем работу бота...", "INFO")
    
    # Сохраняем профили пользователей
    try:
        from profile_storage import save_profiles_to_file
        await save_profiles_to_file()
        logger.info("Профили пользователей сохранены")
        railway_print("Профили пользователей сохранены", "INFO")
    except Exception as e:
        logger.error(f"Ошибка при сохранении профилей: {e}")
        railway_print(f"Ошибка при сохранении профилей: {e}", "ERROR")
    
    # Останавливаем планировщик заданий
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Планировщик заданий остановлен")
    
    # Закрываем сессию бота
    if hasattr(bot, "session") and bot.session:
        await bot.session.close()
        logger.info("Сессия бота закрыта")
    
    # Останавливаем бота
    railway_print("Бот корректно завершил работу", "INFO")
    
    # Освобождаем блокировку
    release_lock()

# Обработчик сигналов SIGINT и SIGTERM
def signal_handler(signal_name):
    """
    Обработчик сигналов для корректного завершения работы бота.
    
    Args:
        signal_name: Имя сигнала
    """
    logger.info(f"Получен сигнал {signal_name}")
    railway_print(f"Получен сигнал {signal_name}", "INFO")
    shutdown_event.set()

async def main():
    """
    Основная функция запуска бота.
    """
    try:
        # Получаем блокировку для предотвращения запуска нескольких экземпляров
        if not acquire_lock():
            logger.error("Бот уже запущен. Завершение работы.")
            railway_print("Бот уже запущен. Завершение работы.", "ERROR")
            return
        
        # Настраиваем обработчики сигналов для корректного завершения работы
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(signal_handler("SIGINT")))
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(signal_handler("SIGTERM")))
        
        # Создаем хранилище состояний FSM в памяти
        storage = MemoryStorage()
        
        # Создаем объекты бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=storage)
        
        # Регистрируем обработчики команд бота
        dp.include_router(survey_router)
        dp.include_router(meditation_router)
        dp.include_router(conversation_router)
        dp.include_router(reminder_router)
        dp.include_router(voice_router)
        dp.include_router(communication_router)
        
        # Определение обработчиков команд внутри функции main
        # Обработчик команды /start
        async def cmd_start(message: Message):
            """
            Обработчик команды /start
            """
            # Приветственное сообщение
            greeting_text = (
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                "Я <b>ОНА</b> - твой Осознанный Наставник и Аналитик.\n\n"
                "Я помогу тебе:\n"
                "• 🧠 Определить твои сильные стороны и таланты\n"
                "• 💡 Дать персонализированные советы\n"
                "• 🌱 Поддержать в развитии и росте\n\n"
                "Чтобы создать твой <b>психологический профиль</b>, нужно пройти опрос из 34 вопросов. "
                "Это займет около 10-15 минут.\n\n"
                "Готов начать?"
            )
            
            # Используем единую клавиатуру из survey_handler
            keyboard = get_main_keyboard()
            
            # Отправляем приветственное сообщение
            await message.answer(
                greeting_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        # Обработчик команды /help
        async def cmd_help(message: Message):
            """
            Обработчик команды /help
            """
            help_text = (
                "🔍 <b>Основные команды и возможности:</b>\n\n"
                "• /start - Начать работу с ботом\n"
                "• /survey или 📝 Опрос - Пройти опрос для создания профиля\n"
                "• /profile или 👤 Профиль - Посмотреть свой психологический профиль\n"
                "• /meditate или 🧘 Медитации - Получить аудио-медитацию\n"
                "• /reminders или ⏰ Напоминания - Настроить напоминания о практиках\n"
                "• /advice или 💡 Советы - Получить персонализированный совет на основе типа личности\n"
                "• /restart или 🔄 Рестарт - Перезапустить бота\n"
                "• /cancel или ❌ Отменить - Отменить текущее действие\n"
                "• /api_key - Инструкции по настройке API ключа OpenAI\n\n"
                "🗣 <b>Как пользоваться ботом:</b>\n\n"
                "1. Пройдите опрос из 34 вопросов\n"
                "2. Получите свой психологический профиль\n"
                "3. Узнайте ваш тип личности (Интеллектуальный, Эмоциональный, Практический или Творческий)\n"
                "4. Получайте персонализированные советы, соответствующие вашему типу личности\n"
                "5. Общайтесь со мной текстом или голосовыми сообщениями\n"
                "6. Я буду отвечать с учетом ваших психологических особенностей\n\n"
                "💡 <b>Если возникнут вопросы или проблемы:</b>\n"
                "• Напишите \"Помощь\" или используйте команду /help\n"
            )
            
            await message.answer(
                help_text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        
        # Обработчик команды /api_key
        async def cmd_api_key(message: Message):
            """
            Обработчик команды /api_key - отображает инструкции по настройке API ключа OpenAI
            """
            try:
                with open('api_key_instructions.md', 'r', encoding='utf-8') as f:
                    instructions = f.read()
                
                instructions_text = (
                    "🔑 <b>Инструкции по настройке API ключа OpenAI</b>\n\n"
                    "Если бот отвечает шаблонными сообщениями и не генерирует уникальные ответы, "
                    "необходимо настроить API ключ OpenAI.\n\n"
                    "Краткая инструкция:\n"
                    "1. Получите API ключ на сайте OpenAI Platform\n"
                    "2. Откройте файл .env в корневой директории\n"
                    "3. Установите ключ в параметр OPENAI_API_KEY\n"
                    "4. Перезапустите бота\n\n"
                    "Полные инструкции отправлены отдельным файлом."
                )
                
                # Отправляем краткую информацию
                await message.answer(
                    instructions_text,
                    parse_mode="HTML"
                )
                
                # Отправляем файл с полными инструкциями
                await message.answer_document(
                    document=BufferedInputFile(
                        instructions.encode('utf-8'),
                        filename="api_key_setup_instructions.md"
                    ),
                    caption="Подробные инструкции по настройке API ключа OpenAI"
                )
                
                logger.info(f"Отправлены инструкции по настройке API ключа пользователю {message.from_user.id}")
                
            except Exception as e:
                logger.error(f"Ошибка при отправке инструкций по API ключу: {e}")
                await message.answer(
                    "К сожалению, не удалось отправить инструкции. Пожалуйста, обратитесь к администратору бота."
                )
        
        # Обработчик команды /restart
        async def cmd_restart(message: Message):
            """
            Обработчик команды /restart
            """
            # Отправляем сообщение о перезапуске
            await message.answer(
                "🔄 <b>Бот перезапущен!</b>\n\n"
                "Начинаем заново. Если вы хотите сбросить свой профиль, "
                "воспользуйтесь кнопкой 📝 Опрос и подтвердите перезапуск.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        
        # Регистрируем основные обработчики команд
        dp.message.register(cmd_start, Command("start"))
        dp.message.register(cmd_help, Command("help"))
        dp.message.register(cmd_help, F.text == "💬 Помощь")
        dp.message.register(cmd_api_key, Command("api_key"))
        dp.message.register(cmd_restart, Command("restart"))
        dp.message.register(cmd_restart, F.text == "🔄 Рестарт")
        
        # Запускаем запланированные задачи
        asyncio.create_task(start_scheduler())
        
        # Запускаем асинхронные задачи из других модулей
        setup_tasks = []
        
        # Добавляем задачи из модуля опросов
        try:
            from survey_handler import setup_async_tasks as survey_setup_tasks
            setup_tasks.extend(survey_setup_tasks())
        except (ImportError, AttributeError) as e:
            logger.warning(f"Не удалось настроить асинхронные задачи из модуля survey_handler: {e}")
        
        # Добавляем задачи из модуля напоминаний
        try:
            from reminder_handler import setup_async_tasks as reminder_setup_tasks
            setup_tasks.extend(reminder_setup_tasks())
        except (ImportError, AttributeError) as e:
            logger.warning(f"Не удалось настроить асинхронные задачи из модуля reminder_handler: {e}")
        
        # Запускаем все подготовленные задачи
        for task in setup_tasks:
            asyncio.create_task(task)
        
        # Запускаем бота в режиме long polling
        railway_print("Начинаем поллинг обновлений Telegram", "INFO")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        railway_print(f"Ошибка при запуске бота: {e}", "ERROR")
    finally:
        # Корректно завершаем работу
        await shutdown(dp, bot)
        # Освобождаем блокировку
        release_lock()

# Запуск бота
if __name__ == "__main__":
    # Запускаем основную функцию
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
        railway_print("Бот остановлен пользователем (Ctrl+C)", "INFO")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        railway_print(f"Критическая ошибка при запуске бота: {e}", "ERROR") 