import asyncio
import logging
import os
import sys
import tempfile  # Для создания временного файла блокировки
import socket  # Для получения имени хоста
import importlib.util  # Для проверки наличия модулей
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.types import BufferedInputFile

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

# Функция для проверки наличия модуля
def is_module_available(module_name):
    """
    Проверяет доступность модуля без его импорта
    
    Args:
        module_name: Имя проверяемого модуля
    
    Returns:
        bool: True, если модуль доступен, иначе False
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError):
        return False

# Проверка совместимости pydantic с aiogram
def check_pydantic_compatibility():
    """
    Проверяет совместимость установленной версии pydantic с aiogram
    
    Returns:
        bool: True, если версии совместимы, иначе False
    """
    try:
        # Попытка импорта необходимых функций из pydantic
        from pydantic import BaseModel
        # Проверка наличия model_validator или root_validator
        try:
            from pydantic import model_validator
            railway_print("Используется pydantic с model_validator", "INFO")
            return True
        except ImportError:
            try:
                from pydantic import validator
                railway_print("Используется pydantic со старым validator", "INFO")
                return True
            except ImportError:
                railway_print("pydantic не имеет необходимых валидаторов", "ERROR")
                return False
    except ImportError as e:
        railway_print(f"Ошибка при проверке pydantic: {e}", "ERROR")
        return False

# Проверка наличия railway_helper и его инициализация
try:
    from railway_helper import ensure_modules_available, print_railway_info
    # Проверяем и обеспечиваем наличие необходимых модулей
    print_railway_info("Инициализация Railway Helper", "INFO")
    
    # Проверяем наличие supabase модуля
    if not is_module_available('supabase'):
        print_railway_info("Модуль 'supabase' не найден, будет использована SQLite-заглушка", "WARNING")
    
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
    from reminder_handler import reminder_router, load_reminders_from_db
    from meditation_handler import meditation_router
    from communication_handler import communication_router
    
    # Инициализация соединения с Supabase
    try:
        from supabase_db import db
        railway_print("Импорт модуля supabase_db успешен", "INFO")
        if db.is_connected:
            railway_print("Соединение с Supabase успешно установлено", "INFO")
        else:
            railway_print("Не удалось установить соединение с Supabase", "WARNING")
    except ImportError:
        railway_print("Модуль supabase не найден, используем SQLite-заглушку", "WARNING")
        try:
            from supabase_fallback import db
            railway_print("Подключена SQLite-заглушка вместо Supabase", "INFO")
        except Exception as fallback_error:
            railway_print(f"Ошибка при подключении SQLite-заглушки: {fallback_error}", "ERROR")
        
except ImportError as e:
    logger.error(f"Ошибка при импорте модулей: {e}")
    railway_print(f"Ошибка при импорте модулей: {e}", "ERROR")
    sys.exit(1)

# Проверяем совместимость зависимостей
railway_print("Проверка совместимости зависимостей...", "INFO")
if not check_pydantic_compatibility():
    railway_print("Обнаружена несовместимая версия pydantic!", "WARNING")
    railway_print("Применение патча из patch_pydantic.py...", "INFO")
    
    # Пытаемся импортировать и применить патч из отдельного модуля
    try:
        import patch_pydantic
        if patch_pydantic.apply_pydantic_patch():
            railway_print("Патч для pydantic успешно применен", "INFO")
        else:
            railway_print("Не удалось применить патч для pydantic", "ERROR")
            railway_print("Бот может работать некорректно!", "WARNING")
    except ImportError:
        railway_print("Модуль patch_pydantic не найден, применяем встроенный патч", "WARNING")
        
        # Пытаемся переопределить model_validator в pydantic (встроенный патч)
        import sys
        import types
        
        # Проверяем, есть ли pydantic в импортированных модулях
        if 'pydantic' in sys.modules:
            try:
                pydantic_module = sys.modules['pydantic']
                if not hasattr(pydantic_module, 'model_validator'):
                    railway_print("Добавление model_validator в pydantic...", "INFO")
                    
                    # Создаем функцию-заглушку
                    def dummy_model_validator(cls_method=None, *args, **kwargs):
                        def decorator(func):
                            return func
                        if cls_method is None:
                            return decorator
                        return decorator(cls_method)
                    
                    # Добавляем model_validator в модуль pydantic
                    setattr(pydantic_module, 'model_validator', dummy_model_validator)
                    railway_print("Успешно добавлен model_validator в pydantic", "INFO")
                
                # Проверяем наличие ConfigDict
                if not hasattr(pydantic_module, 'ConfigDict'):
                    railway_print("Добавление ConfigDict в pydantic...", "INFO")
                    
                    # Создаем класс-заглушку для ConfigDict
                    class DummyConfigDict(dict):
                        def __init__(self, *args, **kwargs):
                            super().__init__(*args, **kwargs)
                    
                    # Добавляем ConfigDict в модуль pydantic
                    setattr(pydantic_module, 'ConfigDict', DummyConfigDict)
                    railway_print("Успешно добавлен ConfigDict в pydantic", "INFO")
            except Exception as patch_error:
                railway_print(f"Не удалось применить патч к pydantic: {patch_error}", "ERROR")
                railway_print("Бот может работать некорректно!", "WARNING")
        else:
            railway_print("Модуль pydantic не найден в импортированных модулях", "ERROR")
            railway_print("Бот может работать некорректно!", "WARNING")

# Создаем экземпляр бота и диспетчер
try:
    bot = Bot(
        token=BOT_TOKEN,
        parse_mode="HTML",  # Устанавливаем HTML-разметку по умолчанию
        disable_web_page_preview=True,  # Отключаем предпросмотр веб-страниц
        protect_content=False  # Разрешаем пересылку сообщений
    )
    dp = Dispatcher(storage=MemoryStorage())
except Exception as e:
    railway_print(f"Ошибка при создании бота: {e}", "ERROR")
    sys.exit(1)

# Регистрируем роутеры в правильном порядке
# Сначала регистрируем роутер опроса, чтобы он имел приоритет при обработке сообщений в состоянии опроса
dp.include_router(survey_router)
# Затем регистрируем роутер голосовых сообщений
dp.include_router(voice_router)
# Далее регистрируем остальные роутеры
dp.include_router(meditation_router)
dp.include_router(reminder_router)
# Регистрируем роутер обычных сообщений последним
dp.include_router(conversation_router)
dp.include_router(communication_router)

# Обработчик команды /start
@dp.message(Command("start"))
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
@dp.message(Command("help"))
@dp.message(F.text == "💬 Помощь")
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
@dp.message(Command("api_key"))
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
@dp.message(Command("restart"))
@dp.message(F.text == "🔄 Рестарт")
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

# Функция для инициализации планировщика
async def start_scheduler():
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("Планировщик заданий запущен")

async def main():
    """
    Основная функция запуска бота
    """
    railway_print("Запуск основной функции бота...", "INFO")
    
    # Создаем экземпляр бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Включаем логирование событий middleware для отладки
    logging.getLogger("aiogram.middleware").setLevel(logging.DEBUG)
    
    # Регистрируем роутеры
    dp.include_router(survey_router)
    dp.include_router(reminder_router)
    dp.include_router(meditation_router)
    dp.include_router(voice_router)
    dp.include_router(conversation_router)
    dp.include_router(communication_router)
    
    # Инициализируем и запускаем планировщик задач
    try:
        railway_print("Загрузка напоминаний из Supabase...", "INFO")
        if db.is_connected:
            await load_reminders_from_db(bot)
            railway_print("Напоминания успешно загружены из Supabase", "INFO")
        else:
            railway_print("Напоминания не загружены: нет подключения к Supabase", "WARNING")
        
        # Запускаем планировщик для напоминаний
        railway_print("Запуск планировщика задач...", "INFO")
        await start_scheduler()
    except Exception as e:
        railway_print(f"Ошибка при инициализации планировщика: {e}", "ERROR")
        logger.error(f"Ошибка при инициализации планировщика: {e}")
    
    # Удаляем все ожидающие обновления (webhook или polling)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем бота
    railway_print("Запуск поллинга обновлений...", "INFO")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    # Запускаем бота
    asyncio.run(main()) 