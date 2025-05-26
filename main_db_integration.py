import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем нашу базу данных
from db import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в .env файле")
    exit(1)

# Создаем экземпляр бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создаем роутер для обработки сообщений
router = Router()
dp.include_router(router)

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Создает или получает пользователя в БД
    """
    user_id = await db.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(f"Привет, {message.from_user.full_name}! Твой ID в базе данных: {user_id}")

# Обработчик команды /profile
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """
    Обработчик команды /profile
    Получает и отображает профиль пользователя
    """
    # Получаем ID пользователя в БД
    user_id = await db.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Получаем профиль
    profile = await db.get_profile(user_id)
    
    if profile:
        # Формируем сообщение с профилем
        personality_type = profile.get("personality_type", "Не определен")
        strengths = ", ".join(profile.get("strengths", ["Не определены"]))
        
        profile_text = f"🧠 Ваш психологический тип: {personality_type}\n\n"
        profile_text += f"💪 Ключевые качества: {strengths}\n\n"
        
        if "profile_text" in profile:
            profile_text += profile["profile_text"]
        
        await message.answer(profile_text)
    else:
        await message.answer("У вас еще нет профиля. Пройдите опрос для создания психологического профиля.")

# Обработчик команды /answers
@router.message(Command("answers"))
async def cmd_answers(message: Message):
    """
    Обработчик команды /answers
    Получает и отображает ответы пользователя
    """
    # Получаем ID пользователя в БД
    user_id = await db.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Получаем ответы
    answers = await db.get_answers(user_id)
    
    if answers:
        # Формируем сообщение с ответами
        answers_text = "📝 Ваши ответы на вопросы:\n\n"
        
        for q_code, value in answers.items():
            answers_text += f"Вопрос {q_code}: {value}\n"
        
        await message.answer(answers_text)
    else:
        await message.answer("Вы еще не отвечали на вопросы.")

# Обработчик текстовых сообщений для примера сохранения ответов
@router.message(F.text)
async def handle_text(message: Message):
    """
    Обработчик текстовых сообщений
    Для примера сохраняем сообщение как ответ на вопрос
    """
    # Получаем ID пользователя в БД
    user_id = await db.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Сохраняем сообщение как ответ на вопрос "последнее_сообщение"
    await db.save_answer(user_id, "последнее_сообщение", message.text)
    
    await message.answer("Ваше сообщение сохранено в базе данных.")

# Главная функция
async def main():
    """
    Главная функция запуска бота
    """
    logger.info("Бот запускается...")
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    finally:
        # Закрываем соединение с ботом при завершении
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 