import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

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
        "railway_logging"
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
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем роутеры
dp.include_router(survey_router)
dp.include_router(voice_router)
dp.include_router(meditation_router)
dp.include_router(reminder_router)
dp.include_router(conversation_router)

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
        "• /cancel или ❌ Отменить - Отменить текущее действие\n\n"
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
    Главная функция запуска бота
    """
    # Инициализируем бот
    logger.info("Бот ОНА запускается...")
    railway_print("Запуск основного цикла бота...", "INFO")
    
    try:
        # Удаляем все обновления, которые были пропущены (если бот был отключен)
        await bot.delete_webhook(drop_pending_updates=True)
        railway_print("Старые обновления удалены", "INFO")
        
        # Удаляем webhook (если он был установлен)
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            await bot.delete_webhook()
            logger.info("Webhook удален, старые обновления очищены")
        
        # Проверяем соединение с Telegram API
        bot_info = await bot.get_me()
        logger.info(f"Соединение с Telegram API установлено успешно. Имя бота: @{bot_info.username}")
        railway_print(f"Бот @{bot_info.username} успешно подключен к Telegram API", "INFO")
        
        # Запускаем планировщик заданий
        await start_scheduler()
        
        # Сообщение о готовности бота
        railway_print("=== ONA BOT ЗАПУЩЕН И ГОТОВ К РАБОТЕ ===", "INFO")
        
        # Запускаем бота с длинным поллингом
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        railway_print(f"Ошибка запуска: {str(e)}", "ERROR")
    finally:
        # Останавливаем планировщик заданий при выходе
        if scheduler and scheduler.running:
            scheduler.shutdown()
            logger.info("Планировщик заданий остановлен")
        
        await bot.session.close()
        logger.info("Бот остановлен")
        railway_print("Бот завершил работу", "INFO")

if __name__ == "__main__":
    # Запускаем бота
    asyncio.run(main()) 