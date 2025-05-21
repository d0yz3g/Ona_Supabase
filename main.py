import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.types import Message, Update, ErrorEvent
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from aiohttp import web

from db import Database
# Импортируем роутеры из handlers/__init__.py
from handlers import (
    reflect_router,
    meditate_router,
    reminder_router,
    survey_router,
    general_router
)

from services.scheduler import ReminderScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler("bot.log", mode="a", encoding="utf-8")
    ]
)

# Настройка логгера для отлова необработанных исключений
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Стандартная обработка Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Логирование необработанных исключений
    logger.error("Необработанное исключение:", 
                exc_info=(exc_type, exc_value, exc_traceback),
                stack_info=True)

# Установка обработчика необработанных исключений
sys.excepthook = handle_exception

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение токенов из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения. Бот не может быть запущен.")
    sys.exit(1)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY не найден в переменных окружения. Будет использована заглушка для генерации рекомендаций.")

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    logger.warning("ELEVEN_API_KEY не найден в переменных окружения. Функция медитации будет работать в режиме заглушки.")

# Инициализация базы данных
db = Database()

# Создание роутера для основных команд
main_router = Router(name="main")

# Обработчики команд
@main_router.message(Command("start"))
async def start(message: Message):
    """Обработчик команды /start."""
    # Добавление пользователя в базу данных
    user_id = db.add_user(
        message.from_user.id, 
        f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
    )
    logger.info(f"Пользователь {message.from_user.id} (db_id: {user_id}) запустил бота")
    
    await message.answer(
        "Привет! Я бот Она, давай познакомимся. "
        "Я помогу тебе узнать свои сильные стороны и дам персональные рекомендации."
    )

@main_router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help."""
    help_text = (
        "Вот команды, которые я понимаю:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/help - Показать это сообщение\n"
        "/profile - Показать ваш профиль (или начать опрос, если профиль отсутствует)\n"
        "/questionnaire, /begin - Начать опрос для создания профиля\n"
        "/reflect - Получить психологический совет\n"
        "/help_reflect - Справка по получению советов\n"
        "/meditate - Получить голосовую медитацию\n"
        "/help_meditate - Справка по медитациям\n"
        "/reminder_on - Включить ежедневные напоминания\n"
        "/reminder_off - Отключить напоминания\n"
        "/reminder_status - Проверить статус напоминаний\n"
        "/help_reminder - Справка по напоминаниям\n"
        "/cancel - Прервать текущий опрос"
    )
    await message.answer(help_text)
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")

@main_router.message(Command("profile"))
async def profile(message: Message):
    """Обработчик команды /profile."""
    # Проверка наличия пользователя в БД
    user = db.get_user_by_tg_id(message.from_user.id)
    
    if not user:
        user_id = db.add_user(
            message.from_user.id,
            f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        )
    else:
        user_id = user["id"]
        
    # Проверка наличия профиля
    profile_data = db.get_profile(user_id)
    
    if profile_data:
        # Отображаем информацию о профиле
        summary = profile_data.get("summary_json", {})
        natal = profile_data.get("natal_json", {})
        
        if summary:
            # Получаем информацию из профиля
            name = summary.get("name", "Неизвестно")
            strengths = summary.get("strengths", [])
            scores = summary.get("scores", {})
            
            # Формируем сообщение с профилем
            profile_message = f"Профиль пользователя {name}:\n\n"
            
            if strengths:
                profile_message += "Сильные стороны:\n"
                for i, strength in enumerate(strengths, 1):
                    profile_message += f"{i}. {strength}\n"
                profile_message += "\n"
            
            # Словарь для перевода категорий
            category_names = {
                "analytical": "Аналитик",
                "creative": "Творческий мыслитель",
                "leadership": "Лидер",
                "social": "Коммуникатор",
                "organized": "Организатор",
                "resilient": "Стойкий"
            }
            
            if scores:
                profile_message += "Оценки по категориям:\n"
                for category, score in scores.items():
                    profile_message += f"- {category_names.get(category, category)}: {score}/5\n"
            
            # Отправляем базовую информацию о профиле
            await message.answer(profile_message)
            
            # Если есть AI-анализ, отправляем его
            ai_analysis = summary.get("ai_analysis", {})
            if ai_analysis:
                ai_message = "🧠 Психологический анализ профиля:\n\n"
                
                if ai_analysis.get("summary"):
                    ai_message += f"{ai_analysis['summary']}\n\n"
                
                if ai_analysis.get("strengths") and len(ai_analysis["strengths"]) > 0:
                    ai_message += "Ключевые сильные стороны:\n"
                    for i, strength in enumerate(ai_analysis["strengths"], 1):
                        ai_message += f"{i}. {strength}\n"
                    ai_message += "\n"
                
                if ai_analysis.get("growth_areas") and len(ai_analysis["growth_areas"]) > 0:
                    ai_message += "Направления для развития:\n"
                    for i, area in enumerate(ai_analysis["growth_areas"], 1):
                        ai_message += f"{i}. {area}\n"
                
                await message.answer(ai_message)
            
            # Если есть данные натальной карты, отправляем их
            if natal and not natal.get("error"):
                astro_message = "🌟 Данные натальной карты:\n\n"
                astro_message += f"Дата рождения: {summary.get('birthdate')}\n"
                astro_message += f"Место рождения: {summary.get('birthplace')}\n\n"
                
                # Словарь для перевода планет
                planet_names = {
                    "sun": "Солнце",
                    "moon": "Луна",
                    "mercury": "Меркурий",
                    "venus": "Венера",
                    "mars": "Марс",
                    "jupiter": "Юпитер",
                    "saturn": "Сатурн"
                }
                
                for planet, position in natal.items():
                    if planet.endswith("_long") and planet.split("_")[0] in planet_names:
                        planet_name = planet_names[planet.split("_")[0]]
                        astro_message += f"{planet_name}: {position:.2f}°\n"
                
                await message.answer(astro_message)
        else:
            await message.answer(
                "Ваш профиль уже создан, но информация в нем неполная. "
                "Рекомендуется пройти опрос заново с помощью команды /questionnaire."
            )
    else:
        await message.answer(
            "Ваш профиль еще не создан. "
            "Чтобы начать создание профиля, пройдите опрос. "
            "Введите команду /questionnaire или напишите 'Начать опрос', когда будете готовы."
        )
    
    logger.info(f"Пользователь {message.from_user.id} запросил профиль")

# Создаем API роутер для health-check
api_router = web.RouteTableDef()

@api_router.get("/health")
async def health_handler(request):
    """Эндпоинт для проверки работоспособности бота."""
    return web.Response(text="OK")

@api_router.get("/")
async def root_handler(request):
    """Корневой эндпоинт со статусом работы бота."""
    uptime = datetime.now() - request.app['start_time']
    return web.json_response({
        "status": "Бот работает",
        "uptime": str(uptime),
        "version": "1.0.0"
    })

# Обработчик ошибок для диспетчера
async def errors_handler(event: ErrorEvent):
    """Обработчик ошибок при обработке обновлений Telegram."""
    # Получаем информацию об ошибке
    update = event.update if hasattr(event, 'update') else None
    exception = event.exception
    
    # Получаем информацию о пользователе и сообщении
    user_id = 'Неизвестно'
    chat_id = 'Неизвестно'
    message_id = 'Неизвестно'
    user_text = 'Неизвестно'
    
    if update and hasattr(update, 'message') and update.message:
        user_id = update.message.from_user.id if update.message.from_user else 'Неизвестно'
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        user_text = update.message.text if hasattr(update.message, 'text') and update.message.text else '<нет текста>'
    elif update and hasattr(update, 'callback_query') and update.callback_query:
        user_id = update.callback_query.from_user.id if update.callback_query.from_user else 'Неизвестно'
        chat_id = update.callback_query.message.chat.id if update.callback_query.message else 'Неизвестно'
        message_id = update.callback_query.message.message_id if update.callback_query.message else 'Неизвестно'
        user_text = update.callback_query.data if update.callback_query.data else '<нет данных>'
    
    # Подготовка данных об ошибке
    error_message = f"Ошибка при обработке сообщения от пользователя {user_id}:\n"
    error_message += f"Чат: {chat_id}, Сообщение ID: {message_id}\n"
    error_message += f"Текст сообщения: {html.quote(str(user_text))}\n"
    error_message += f"Ошибка: {html.quote(str(exception))}"
    
    # Логирование ошибки
    logger.error(error_message, exc_info=True)
    
    # Возвращать False, чтобы aiogram продолжил обработку ошибки
    return False

async def main():
    """Основная функция запуска бота."""
    # Инициализация хранилища состояний FSM
    storage = MemoryStorage()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Регистрация обработчика ошибок
    dp.errors.register(errors_handler)
    
    # Инициализация планировщика напоминаний
    scheduler = ReminderScheduler(bot=bot, db=db)
    
    # Передаем экземпляр планировщика в модуль напоминаний
    from handlers.reminder import set_scheduler
    set_scheduler(scheduler)

    # Настройка приоритетов роутеров (чем выше число, тем выше приоритет)
    main_router.message.middleware.priority = 10  # Самый высокий приоритет для основных команд
    survey_router.message.middleware.priority = 9  # Высокий приоритет для опросника
    reflect_router.message.middleware.priority = 8
    meditate_router.message.middleware.priority = 8
    reminder_router.message.middleware.priority = 8
    general_router.message.middleware.priority = 1  # Самый низкий приоритет для обработки неспециализированных сообщений

    # Регистрация роутеров
    dp.include_router(main_router)
    dp.include_router(survey_router)
    dp.include_router(reflect_router)
    dp.include_router(meditate_router)
    dp.include_router(reminder_router)
    dp.include_router(general_router)  # Регистрируем последним с низким приоритетом

    # Запускаем планировщик
    scheduler.start()
    logger.info("Планировщик напоминаний запущен")
    
    # Настройка веб-сервера для healthcheck
    app = web.Application()
    app.add_routes(api_router)
    app['start_time'] = datetime.now()
    
    # Запуск веб-сервера
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Веб-сервер запущен на порту {port}")
    
    # Запуск поллинга
    logger.info("Бот запущен, ожидание сообщений...")
    try:
        await dp.start_polling(bot)
    finally:
        # Остановка планировщика и веб-сервера при завершении работы бота
        scheduler.shutdown()
        await runner.cleanup()
        logger.info("Планировщик напоминаний и веб-сервер остановлены")

if __name__ == "__main__":
    logger.info("Инициализация бота...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
    finally:
        # Закрытие соединения с базой данных при завершении работы
        if 'db' in locals():
            db.close()
            logger.info("Соединение с базой данных закрыто") 