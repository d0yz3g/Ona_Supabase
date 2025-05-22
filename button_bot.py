import asyncio
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Union, List, Tuple, Any, Optional
import json
import uuid
from pathlib import Path
import aiohttp
import tempfile
import signal
import random

# Импорт библиотеки для планирования задач
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Импорт aiogram
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация планировщика задач
scheduler = AsyncIOScheduler()

# Словарь для хранения пользователей с включенными напоминаниями
reminder_users = {}

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Получение токена ElevenLabs
ELEVEN_TOKEN = os.getenv("ELEVEN_API_KEY")
# Если токен не найден, логируем предупреждение, но продолжаем работу
if not ELEVEN_TOKEN:
    logger.warning("ELEVEN_API_KEY не найден в переменных окружения. Медитации будут работать в демо-режиме.")

# Получение токена OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Если токен не найден, логируем предупреждение, но продолжаем работу
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY не найден в переменных окружения. Функции распознавания голоса и генерации ответов будут работать в ограниченном режиме.")

# Настройки для API ElevenLabs
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVEN_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ID стандартного голоса

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, LOG_LEVEL))

# Создаем директорию tmp, если она не существует
tmp_dir = Path("tmp")
tmp_dir.mkdir(exist_ok=True)

# Функция для генерации аудио (заменяем удаленную функцию из services/tts.py)
async def generate_audio(text: str, user_id: int, meditation_type: str) -> str:
    """
    Генерирует аудио с помощью ElevenLabs API или gTTS в демо-режиме.
    
    Args:
        text: Текст для преобразования в аудио
        user_id: ID пользователя Telegram
        meditation_type: Тип медитации (relax, focus, sleep)
        
    Returns:
        str: Путь к созданному аудио-файлу
    """
    # Создаем директорию tmp, если она не существует
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_name = f"{meditation_type}_{user_id}_{uuid.uuid4()}.mp3"
    file_path = tmp_dir / file_name
    
    try:
        # Проверяем наличие токена ElevenLabs
        if not ELEVEN_TOKEN:
            logger.warning(f"ELEVEN_TOKEN не найден. Создаем демо-файл для пользователя {user_id}")
            
            # Создаем MP3 файл с помощью Google Text-to-Speech
            try:
                # Импортируем библиотеку gTTS
                from gtts import gTTS
                
                # Создаем объект gTTS и сохраняем аудио
                tts = gTTS(text=text, lang='ru', slow=False)
                tts.save(str(file_path))
                
                # Проверяем, что файл был успешно создан
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logger.info(f"Создан демо MP3 файл с помощью gTTS: {file_path}")
                    return str(file_path)
                else:
                    logger.error(f"Файл gTTS создан, но имеет нулевой размер: {file_path}")
                    return None
            except Exception as e:
                logger.error(f"Ошибка при создании демо MP3 файла с gTTS: {e}")
                return None
        
        # Если есть токен ElevenLabs, используем API ElevenLabs
        # Настройки для запроса к API
        headers = {
            "xi-api-key": ELEVEN_TOKEN,
            "Content-Type": "application/json",
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            }
        }
        
        # Отправляем запрос к API
        logger.info(f"Отправка запроса к ElevenLabs API для пользователя {user_id}")
        
        # Выполняем асинхронный запрос к API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ELEVEN_API_URL}/{ELEVEN_VOICE_ID}",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    # Сохраняем аудио-файл
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    logger.info(f"Аудио успешно сгенерировано и сохранено: {file_path}")
                    return str(file_path)
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка при генерации аудио: {response.status}, {error_text}")
                    # В случае ошибки возвращаем None
                    return None
    except Exception as e:
        logger.error(f"Ошибка при генерации аудио: {e}")
        return None

# Функция для отправки напоминания
async def send_reminder(bot: Bot, user_id: int):
    """
    Отправляет напоминание пользователю.
    
    Args:
        bot: Бот, который отправляет сообщение
        user_id: ID пользователя в Telegram
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text="🧘 <b>Напоминание о практике</b>\n\n"
                 "Привет! Не забудьте уделить время себе сегодня. "
                 "Медитация или другая психологическая практика поможет вам "
                 "чувствовать себя лучше и поддерживать ментальное здоровье.",
            parse_mode="HTML"
        )
        logger.info(f"Отправлено напоминание пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")

# Импорт модулей для обработки сообщений и голосовых сообщений
from services.stt import process_voice_message
from services.recs import generate_response as generate_ai_response

# Импортируем состояния
from button_states import SurveyStates, MeditationStates, ReminderStates

# Импортируем вопросы
try:
    from questions import get_demo_questions, get_strength_questions, get_strength_options_labels
    
    # Используем вопросы из файла questions.py
    DEMO_QUESTIONS_FULL = get_demo_questions()
    DEMO_QUESTIONS = [q["text"] for q in DEMO_QUESTIONS_FULL]
    STRENGTH_QUESTIONS = get_strength_questions()
    STRENGTH_OPTIONS_LABELS = get_strength_options_labels()
    
    # Категории сильных сторон
    STRENGTH_CATEGORIES = {
        "analytical": "Аналитик",
        "creative": "Творческий мыслитель",
        "leadership": "Лидер",
        "social": "Коммуникатор",
        "organized": "Организатор",
        "resilient": "Стойкий"
    }
    
    # Группируем вопросы по категориям для подсчета баллов
    CATEGORY_QUESTIONS = {
        "analytical": [],
        "creative": [],
        "leadership": [],
        "social": [],
        "organized": [],
        "resilient": []
    }
    
    # Заполняем группы вопросов
    for question in STRENGTH_QUESTIONS:
        if "category" in question:
            category = question["category"]
            if category in CATEGORY_QUESTIONS:
                CATEGORY_QUESTIONS[category].append(question["id"])
    
    logger.info("Вопросы успешно импортированы из questions.py")
except ImportError:
    logger.warning("Не удалось импортировать вопросы из questions.py, используем демо-вопросы")
    # Демо-вопросы для опроса, если не удалось импортировать
    DEMO_QUESTIONS = [
        "Как вас зовут?",
        "Сколько вам лет?",
        "Какой у вас уровень образования?",
        "Где вы живете?",
        "Чем вы занимаетесь?"
    ]
    STRENGTH_CATEGORIES = {}
    CATEGORY_QUESTIONS = {}

# Создаем роутеры
main_router = Router(name="main")
profile_router = Router(name="profile")
reflect_router = Router(name="reflect")
meditate_router = Router(name="meditate")
reminder_router = Router(name="reminder")
survey_router = Router(name="survey")

# Константы для callback_data
class CallbackActions:
    # Основные действия
    START = "start"
    HELP = "help"
    PROFILE = "profile"
    QUESTIONNAIRE = "questionnaire"
    RESET = "reset"
    REFLECT = "reflect"
    HELP_REFLECT = "help_reflect"
    MEDITATE = "meditate"
    HELP_MEDITATE = "help_meditate"
    REMINDER_ON = "reminder_on"
    REMINDER_OFF = "reminder_off"
    REMINDER_STATUS = "reminder_status"
    HELP_REMINDER = "help_reminder"
    CANCEL = "cancel"
    
    # Категории меню
    MAIN_MENU = "main_menu"
    REFLECT_MENU = "reflect_menu"
    MEDITATE_MENU = "meditate_menu"
    REMINDER_MENU = "reminder_menu"
    PROFILE_MENU = "profile_menu"

# Функция для создания главного меню
def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    # Основные функции
    builder.button(text="👤 Профиль")
    builder.button(text="📝 Опрос")
    
    # Категории
    builder.button(text="💭 Советы")
    builder.button(text="🧘 Медитации")
    builder.button(text="⏰ Напоминания")
    
    # Дополнительные опции
    builder.button(text="🔄 Рестарт")
    builder.button(text="🆘 Помощь")
    
    # Формируем сетку кнопок: 2-2-2-1
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
        input_field_placeholder="Выберите действие..."
    )

# Функция для создания меню советов
def get_reflect_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="💭 Получить совет", 
        callback_data=CallbackActions.REFLECT
    )
    builder.button(
        text="❓ Помощь по советам", 
        callback_data=CallbackActions.HELP_REFLECT
    )
    builder.button(
        text="◀️ Назад в меню", 
        callback_data=CallbackActions.MAIN_MENU
    )
    
    # Формируем сетку кнопок: по одной кнопке в строке
    builder.adjust(1, 1, 1)
    
    return builder.as_markup()

# Функция для создания меню медитаций
def get_meditate_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Разные типы медитаций
    builder.button(
        text="🧘 Медитация для расслабления", 
        callback_data="meditate_relax"
    )
    builder.button(
        text="🧠 Медитация для фокусировки", 
        callback_data="meditate_focus"
    )
    builder.button(
        text="😴 Медитация для сна", 
        callback_data="meditate_sleep"
    )
    builder.button(
        text="📖 Справка по медитациям", 
        callback_data=CallbackActions.HELP_MEDITATE
    )
    builder.button(
        text="◀️ Назад в меню", 
        callback_data=CallbackActions.MAIN_MENU
    )
    
    # Формируем сетку кнопок: по одной кнопке в строке для лучшей читаемости
    builder.adjust(1, 1, 1, 1, 1)
    
    return builder.as_markup()

# Функция для создания меню напоминаний
def get_reminder_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Верхний ряд с двумя кнопками (включить/отключить)
    builder.button(
        text="⏰ Включить напоминания", 
        callback_data=CallbackActions.REMINDER_ON
    )
    builder.button(
        text="🔕 Отключить напоминания", 
        callback_data=CallbackActions.REMINDER_OFF
    )
    
    # Отдельные кнопки
    builder.button(
        text="📅 Статус напоминаний", 
        callback_data=CallbackActions.REMINDER_STATUS
    )
    builder.button(
        text="ℹ️ Справка по напоминаниям", 
        callback_data=CallbackActions.HELP_REMINDER
    )
    builder.button(
        text="◀️ Назад в меню", 
        callback_data=CallbackActions.MAIN_MENU
    )
    
    # Формируем сетку кнопок: две в первом ряду, по одной в остальных
    builder.adjust(2, 1, 1, 1)
    
    return builder.as_markup()

# Функция для создания меню профиля
def get_profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="👤 Показать профиль", 
        callback_data=CallbackActions.PROFILE
    )
    builder.button(
        text="📝 Начать опрос", 
        callback_data=CallbackActions.QUESTIONNAIRE
    )
    builder.button(
        text="🗑 Сбросить профиль", 
        callback_data=CallbackActions.RESET
    )
    builder.button(
        text="◀️ Назад в меню", 
        callback_data=CallbackActions.MAIN_MENU
    )
    
    # Формируем сетку кнопок: по одной кнопке в строке
    builder.adjust(1, 1, 1, 1)
    
    return builder.as_markup()

# Тексты медитаций для разных типов
MEDITATION_TEXTS = {
    "relax": "Сядьте удобно, расслабьте плечи и закройте глаза. Сделайте глубокий вдох через нос, "
             "наполняя легкие воздухом. Задержите дыхание на три секунды. Теперь медленно выдохните "
             "через рот, ощущая, как напряжение покидает ваше тело. Сконцентрируйтесь на своем дыхании, "
             "позволяя каждому вдоху и выдоху становиться все глубже и спокойнее. Почувствуйте, как с "
             "каждым выдохом вы все больше расслабляетесь. Представьте, что вы находитесь на "
             "спокойном пляже, слушая шум волн и ощущая тепло солнца. Продолжайте глубоко дышать в "
             "этом умиротворенном состоянии.",
    
    "focus": "Примите удобное положение и сделайте несколько глубоких вдохов. Сосредоточьте внимание "
             "на своем дыхании. Почувствуйте, как воздух входит и выходит через ваши ноздри. Обратите "
             "внимание на то, как поднимается и опускается ваша грудь. Если в ваш ум приходят мысли, "
             "просто отметьте их и мягко верните внимание к дыханию. Сейчас мы будем считать вдохи и "
             "выдохи. Вдох – один, выдох – один. Вдох – два, выдох – два. Продолжайте до десяти, затем "
             "начните сначала. Это помогает сосредоточить ум и улучшить концентрацию внимания.",
    
    "sleep": "Лягте удобно, расслабьте все мышцы и закройте глаза. Сделайте глубокий вдох, затем "
             "медленно выдохните. Представьте, что с каждым выдохом вы погружаетесь глубже в состояние "
             "покоя. Начните с расслабления мышц лица – лоб, глаза, щеки, челюсть. Затем переходите к "
             "шее и плечам, рукам, груди, животу, ногам. Почувствуйте, как тяжелеют ваши конечности. "
             "Представьте, что вы лежите на мягком облаке, которое нежно качает вас, унося все дальше в "
             "страну снов. Ваше дыхание становится все медленнее и глубже. Позвольте себе плавно "
             "погрузиться в спокойный, восстанавливающий сон."
}

# Обработчики команд

@main_router.message(CommandStart())
@main_router.message(F.text == "🔄 Рестарт")
async def command_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот-психолог Она.\n\n"
        "Я помогу вам узнать свои сильные стороны и дам персональные рекомендации. "
        "Воспользуйтесь кнопками ниже для взаимодействия со мной:",
        reply_markup=get_main_keyboard()
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

@main_router.message(Command("help"))
@main_router.message(F.text == "🆘 Помощь")
async def command_help(message: Message):
    help_text = (
        "🆘 <b>Доступные функции:</b>\n\n"
        "👤 <b>Профиль</b> - просмотр профиля или начало опроса\n"
        "📝 <b>Опрос</b> - прохождение опроса для создания профиля\n"
        "💭 <b>Советы</b> - получение психологических рекомендаций\n"
        "🧘 <b>Медитации</b> - получение голосовых медитаций\n"
        "⏰ <b>Напоминания</b> - управление напоминаниями\n"
        "🔄 <b>Рестарт</b> - перезапуск бота\n"
        "❌ <b>Отмена</b> - отмена текущего опроса\n\n"
        "Используйте кнопки для взаимодействия с ботом."
    )
    await message.answer(help_text, parse_mode="HTML")
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")

# Обработчики для кнопок основного меню
@main_router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    await message.answer(
        "👤 <b>Меню профиля</b>\n\n"
        "Здесь вы можете управлять своим профилем:",
        reply_markup=get_profile_keyboard(),
        parse_mode="HTML"
    )

@main_router.message(F.text == "📝 Опрос")
async def questionnaire_start(message: Message, state: FSMContext):
    # Перенаправляем на start_survey
    await start_survey(message, state)

@main_router.message(F.text == "💭 Советы")
async def reflect_menu(message: Message):
    await message.answer(
        "💭 <b>Меню советов</b>\n\n"
        "Здесь вы можете получить персональные психологические рекомендации:",
        reply_markup=get_reflect_keyboard(),
        parse_mode="HTML"
    )

@main_router.message(F.text == "🧘 Медитации")
async def meditate_menu(message: Message):
    await message.answer(
        "🧘 <b>АУДИО-МЕДИТАЦИИ ДЛЯ РЕЛАКСАЦИИ</b>\n\n"
        "Выберите тип медитации, который соответствует вашим текущим потребностям:\n\n"
        "• <b>Медитация для расслабления</b> - снимает стресс и напряжение\n"
        "• <b>Медитация для фокусировки</b> - улучшает концентрацию и ясность ума\n"
        "• <b>Медитация для сна</b> - помогает заснуть и улучшает качество сна\n\n"
        "Все медитации доставляются в виде голосовых сообщений. Рекомендуется использовать наушники для лучшего эффекта.",
        reply_markup=get_meditate_keyboard(),
        parse_mode="HTML"
    )

@main_router.message(F.text == "⏰ Напоминания")
async def reminder_menu(message: Message):
    await message.answer(
        "⏰ <b>Меню напоминаний</b>\n\n"
        "Здесь вы можете управлять напоминаниями о практиках:",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )

# Обработчики инлайн-кнопок
@main_router.callback_query(F.data == CallbackActions.MAIN_MENU)
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.answer(
        "Главное меню. Используйте кнопки клавиатуры для навигации:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")

# Обработчики для инлайн-кнопок профиля
@profile_router.callback_query(F.data == CallbackActions.PROFILE)
async def show_profile(callback: CallbackQuery, state: FSMContext):
    # Получаем данные пользователя из состояния
    user_data = await state.get_data()
    
    # Проверяем, есть ли ответы у пользователя
    if not user_data or "answers" not in user_data:
        await callback.message.edit_text(
            "👤 <b>Ваш профиль:</b>\n\n"
            "Профиль еще не создан. Пройдите опрос, чтобы создать психологический профиль.",
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer("Профиль не найден")
        return
    
    # Получаем ответы пользователя
    answers = user_data.get("answers", {})
    
    if not answers:
        await callback.message.edit_text(
            "👤 <b>Ваш профиль:</b>\n\n"
            "Профиль еще не создан. Пройдите опрос, чтобы создать психологический профиль.",
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer("Профиль не найден")
        return
    
    # Формируем основную информацию профиля
    profile_text = "👤 <b>Ваш психологический профиль:</b>\n\n"
    
    # Добавляем базовую информацию из демо-вопросов
    profile_text += "📋 <b>Основная информация:</b>\n"
    
    # Отладочная информация для проверки структуры ответов
    logger.info(f"Структура ответов: {answers}")
    
    # Получаем ответы на демо-вопросы
    demo_answers = {}
    for key, value in answers.items():
        if key.startswith("demo_"):
            question_index = int(key.split("_")[1]) - 1
            if question_index < len(DEMO_QUESTIONS):
                demo_answers[question_index] = value
    
    # Добавляем информацию о наличии/отсутствии ответов
    if not demo_answers:
        profile_text += "❌ Базовая информация не заполнена\n\n"
    else:
        # Создаем словарь для красивых наименований полей
        field_icons = {
            "Как тебя зовут?": "👤 <b>Имя:</b> ",
            "Сколько тебе лет?": "🎂 <b>Возраст:</b> ",
            "Какая у тебя дата рождения?": "📅 <b>Дата рождения:</b> ",
            "Какая у тебя дата рождения? (формат: ДД.ММ.ГГГГ)": "📅 <b>Дата рождения:</b> ",
            "Где ты родился/родилась?": "🌍 <b>Место рождения:</b> ",
            "Где ты родился/родилась? (город, страна)": "🌍 <b>Место рождения:</b> ",
            "В каком часовом поясе ты находишься?": "🕒 <b>Часовой пояс:</b> ",
            "В каком часовом поясе ты находишься? (например, UTC+3 для Москвы)": "🕒 <b>Часовой пояс:</b> "
        }
        
        # Сортируем и добавляем ответы на демо-вопросы в красивом формате
        for i in sorted(demo_answers.keys()):
            if i < len(DEMO_QUESTIONS):
                question = DEMO_QUESTIONS[i]
                answer = demo_answers[i]
                
                # Проверяем, есть ли вопрос в словаре иконок
                if question in field_icons:
                    profile_text += f"{field_icons[question]}{answer}\n"
                else:
                    # Для необработанных вопросов используем стандартный формат
                    profile_text += f"• <b>{question}</b> {answer}\n"
        
        profile_text += "\n"
    
    # Проверяем, есть ли ответы на вопросы о сильных сторонах
    strength_answers = {}
    for key, value in answers.items():
        if key.startswith("strength_") and value.isdigit():
            strength_answers[key] = value
    
    # Если есть ответы на вопросы о сильных сторонах, добавляем информацию о сильных сторонах
    if strength_answers:
        profile_text += "🧠 <b>ПСИХОЛОГИЧЕСКИЙ ПРОФИЛЬ</b>\n"
        profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        profile_text += "✅ Опрос на определение сильных сторон завершен\n"
        profile_text += "📊 Проанализировано ответов: <b>34</b>\n\n"
        
        # Получаем топ-3 сильные стороны
        scores = {}
        for category in CATEGORY_QUESTIONS:
            scores[category] = {"total": 0, "count": 0}
        
        for question_id, answer_value in strength_answers.items():
            for category, questions in CATEGORY_QUESTIONS.items():
                if question_id in questions:
                    scores[category]["total"] += int(answer_value)
                    scores[category]["count"] += 1
        
        final_scores = {}
        for category, data in scores.items():
            if data["count"] > 0:
                final_scores[category] = round(data["total"] / data["count"], 2)
            else:
                final_scores[category] = 0
        
        top_strengths = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if top_strengths:
            profile_text += "💪 <b>ВАШИ КЛЮЧЕВЫЕ СИЛЬНЫЕ СТОРОНЫ:</b>\n"
            for i, (category, score) in enumerate(top_strengths, 1):
                category_name = STRENGTH_CATEGORIES.get(category, category)
                # Добавляем звездочки для визуального отображения оценки
                stars = "★" * round(score) + "☆" * (5 - round(score))
                profile_text += f"{i}. <b>{category_name}</b> ({score}/5) {stars}\n"
            profile_text += "\n"
            profile_text += "📋 Для просмотра полных результатов теста нажмите кнопку <b>«Результаты теста»</b> ниже\n\n"
        
        # Создаем клавиатуру с дополнительной кнопкой для просмотра результатов теста
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Результаты теста", callback_data="show_test_results")
        builder.button(text="📝 Пройти опрос заново", callback_data=CallbackActions.QUESTIONNAIRE)
        builder.button(text="🗑 Сбросить профиль", callback_data=CallbackActions.RESET)
        builder.button(text="◀️ Назад в меню", callback_data=CallbackActions.MAIN_MENU)
        
        # Формируем сетку кнопок: по одной кнопке в строке
        builder.adjust(1, 1, 1, 1)
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        profile_text += "🧠 <b>ПСИХОЛОГИЧЕСКИЙ ПРОФИЛЬ</b>\n"
        profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        profile_text += "❌ <b>Опрос на определение сильных сторон не пройден</b>\n\n"
        profile_text += "📝 Чтобы узнать свои сильные стороны, пройдите психологический тест\n"
        profile_text += "🔍 Тест поможет выявить ваши природные таланты и склонности\n"
        profile_text += "⏱ Время прохождения: около 5-7 минут\n\n"
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил просмотр профиля")

@profile_router.callback_query(F.data == CallbackActions.QUESTIONNAIRE)
async def start_questionnaire_callback(callback: CallbackQuery, state: FSMContext):
    # Получаем данные пользователя из состояния
    user_data = await state.get_data()
    has_profile = user_data.get("answers", {}) and any(key.startswith("demo_") for key in user_data.get("answers", {}))
    
    # Если у пользователя уже есть профиль, спрашиваем подтверждение
    if has_profile:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Да, начать заново", callback_data="confirm_survey")
        builder.button(text="❌ Нет, отмена", callback_data=CallbackActions.PROFILE_MENU)
        builder.adjust(2)  # Размещаем обе кнопки в одном ряду
        
        await callback.message.edit_text(
            "⚠️ <b>Внимание:</b>\n\n"
            "У вас уже есть заполненный профиль. Если вы пройдете опрос заново, "
            "ваши текущие данные будут перезаписаны.\n\n"
            "Вы уверены, что хотите начать опрос заново?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Если профиля нет, начинаем опрос сразу
    # Отвечаем на callback
    await callback.answer("Запускаем опрос...")
    
    # Удаляем инлайн клавиатуру
    await callback.message.delete()
    
    # Отправляем новое сообщение
    await callback.message.answer(
        "📋 <b>Начинаем опрос!</b>\n\n"
        "Я задам несколько вопросов, чтобы лучше узнать тебя. "
        "Сначала ответь на несколько базовых вопросов, а затем мы перейдем к "
        "специальному тесту для определения твоих сильных сторон.",
        parse_mode="HTML"
    )
    
    # Показываем первый вопрос
    await callback.message.answer(
        f"Вопрос 1: {DEMO_QUESTIONS[0]}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
            resize_keyboard=True,
            one_time_keyboard=False,
            is_persistent=True,
            input_field_placeholder="Введите ваш ответ..."
        )
    )
    
    # Инициализируем опрос
    await state.set_state(SurveyStates.answering_questions)
    await state.update_data(
        question_index=0,
        answers={},
        is_strength_questions=False
    )
    
    logger.info(f"Пользователь {callback.from_user.id} запустил опрос через кнопку в профиле")

@profile_router.callback_query(F.data == CallbackActions.RESET)
async def reset_profile(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сбросить", callback_data="confirm_reset")
    builder.button(text="❌ Нет, отмена", callback_data=CallbackActions.PROFILE_MENU)
    builder.adjust(2)  # Размещаем обе кнопки в одном ряду
    
    await callback.message.edit_text(
        "🗑 <b>Сброс профиля:</b>\n\n"
        "Вы уверены, что хотите сбросить ваш профиль? Все данные будут удалены.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил сброс профиля")

@profile_router.callback_query(F.data == "confirm_reset")
async def confirm_reset_profile(callback: CallbackQuery, state: FSMContext):
    # Сбрасываем состояние пользователя
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Ваш профиль успешно сброшен. Вы можете пройти опрос заново.",
        reply_markup=get_profile_keyboard()
    )
    await callback.answer("Профиль сброшен!")
    logger.info(f"Пользователь {callback.from_user.id} подтвердил сброс профиля")

@profile_router.callback_query(F.data == CallbackActions.PROFILE_MENU)
async def back_to_profile_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 <b>Меню профиля</b>\n\n"
        "Здесь вы можете управлять своим профилем:",
        reply_markup=get_profile_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики для инлайн-кнопок советов
@reflect_router.callback_query(F.data == CallbackActions.REFLECT)
async def get_reflect(callback: CallbackQuery):
    # Отправляем сообщение о том, что генерируем совет
    await callback.answer("Генерирую персональный совет...")
    
    try:
        # Генерируем персональный совет с помощью OpenAI
        advice = await generate_ai_response(
            text="Дай мне психологический совет на сегодня",
            user_id=callback.from_user.id
        )
        
        await callback.message.edit_text(
            f"💭 <b>Ваш совет:</b>\n\n{advice}",
            reply_markup=get_reflect_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"Пользователь {callback.from_user.id} получил психологический совет")
    except Exception as e:
        logger.error(f"Ошибка при генерации совета: {e}")
        # В случае ошибки отправляем заготовленный ответ
        await callback.message.edit_text(
            "💭 <b>Ваш совет:</b>\n\n"
            "Помните, что забота о себе - это не эгоизм, а необходимость. "
            "Выделите сегодня 15 минут на то, что приносит вам радость.",
            reply_markup=get_reflect_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"Пользователь {callback.from_user.id} получил стандартный психологический совет из-за ошибки")

@reflect_router.callback_query(F.data == CallbackActions.HELP_REFLECT)
async def help_reflect(callback: CallbackQuery):
    await callback.message.edit_text(
        "❓ <b>Справка по советам:</b>\n\n"
        "Психологические советы - это рекомендации, которые помогут вам справиться "
        "с повседневными трудностями и улучшить ваше психологическое состояние.\n\n"
        "Рекомендации формируются на основе вашего профиля и контекста беседы.",
        reply_markup=get_reflect_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил справку по советам")

# Обработчики для инлайн-кнопок медитаций
@meditate_router.callback_query(F.data == "meditate_relax")
async def get_relax_meditation(callback: CallbackQuery):
    await callback.answer("Подготавливаю медитацию для расслабления...")
    
    # Отправляем текст медитации
    await callback.message.edit_text(
        "🧘 <b>Медитация для расслабления:</b>\n\n"
        "Сейчас вы получите голосовую медитацию. Найдите удобное место, "
        "где вас не будут беспокоить в течение 5-10 минут.",
        reply_markup=get_meditate_keyboard(),
        parse_mode="HTML"
    )
    
    try:
        # Отправляем сообщение о том, что медитация готовится
        preparing_message = await callback.message.answer(
            "⏳ Генерирую аудио медитацию...\n"
            "Это может занять несколько секунд."
        )
        
        # Генерируем аудио с помощью ElevenLabs API
        audio_path = await generate_audio(
            text=MEDITATION_TEXTS["relax"],
            user_id=callback.from_user.id,
            meditation_type="relax"
        )
        
        # Удаляем сообщение о подготовке
        await preparing_message.delete()
        
        if audio_path:
            # Проверяем, что файл существует
            if os.path.exists(audio_path):
                try:
                    # Отправляем голосовое сообщение
                    await callback.message.answer_voice(
                        FSInputFile(audio_path),
                        caption="🧘 Медитация для расслабления. Найдите спокойное место и следуйте инструкциям."
                    )
                    logger.info(f"Голосовое сообщение успешно отправлено пользователю {callback.from_user.id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке голосового сообщения: {e}")
                    # Если не удалось отправить голосовое, отправляем текст медитации
                    await callback.message.answer(
                        f"<b>Не удалось отправить аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['relax']}",
                        parse_mode="HTML"
                    )
            else:
                logger.error(f"Файл {audio_path} не существует")
                await callback.message.answer(
                    f"<b>Не удалось создать аудио-файл. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['relax']}",
                    parse_mode="HTML"
                )
            
            # Удаляем временный файл
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Временный файл {audio_path} удален")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
        else:
            # Если не удалось сгенерировать аудио, отправляем текст медитации
            await callback.message.answer(
                f"<b>Не удалось сгенерировать аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['relax']}",
                parse_mode="HTML"
            )
        
        logger.info(f"Пользователь {callback.from_user.id} получил медитацию для расслабления")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке медитации: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при подготовке медитации. Пожалуйста, попробуйте позже."
        )

@meditate_router.callback_query(F.data == "meditate_focus")
async def get_focus_meditation(callback: CallbackQuery):
    await callback.answer("Подготавливаю медитацию для фокусировки...")
    
    # Отправляем текст медитации
    await callback.message.edit_text(
        "🧠 <b>Медитация для фокусировки:</b>\n\n"
        "Сейчас вы получите голосовую медитацию. Найдите удобное место, "
        "где вас не будут беспокоить в течение 5-10 минут.",
        reply_markup=get_meditate_keyboard(),
        parse_mode="HTML"
    )
    
    try:
        # Отправляем сообщение о том, что медитация готовится
        preparing_message = await callback.message.answer(
            "⏳ Генерирую аудио медитацию...\n"
            "Это может занять несколько секунд."
        )
        
        # Генерируем аудио с помощью ElevenLabs API
        audio_path = await generate_audio(
            text=MEDITATION_TEXTS["focus"],
            user_id=callback.from_user.id,
            meditation_type="focus"
        )
        
        # Удаляем сообщение о подготовке
        await preparing_message.delete()
        
        if audio_path:
            # Проверяем, что файл существует
            if os.path.exists(audio_path):
                try:
                    # Отправляем голосовое сообщение
                    await callback.message.answer_voice(
                        FSInputFile(audio_path),
                        caption="🧠 Медитация для фокусировки. Сядьте в удобной позе и следуйте инструкциям."
                    )
                    logger.info(f"Голосовое сообщение успешно отправлено пользователю {callback.from_user.id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке голосового сообщения: {e}")
                    # Если не удалось отправить голосовое, отправляем текст медитации
                    await callback.message.answer(
                        f"<b>Не удалось отправить аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['focus']}",
                        parse_mode="HTML"
                    )
            else:
                logger.error(f"Файл {audio_path} не существует")
                await callback.message.answer(
                    f"<b>Не удалось создать аудио-файл. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['focus']}",
                    parse_mode="HTML"
                )
            
            # Удаляем временный файл
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Временный файл {audio_path} удален")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
        else:
            # Если не удалось сгенерировать аудио, отправляем текст медитации
            await callback.message.answer(
                f"<b>Не удалось сгенерировать аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['focus']}",
                parse_mode="HTML"
            )
        
        logger.info(f"Пользователь {callback.from_user.id} получил медитацию для фокусировки")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке медитации: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при подготовке медитации. Пожалуйста, попробуйте позже."
        )

@meditate_router.callback_query(F.data == "meditate_sleep")
async def get_sleep_meditation(callback: CallbackQuery):
    await callback.answer("Подготавливаю медитацию для сна...")
    
    # Отправляем текст медитации
    await callback.message.edit_text(
        "😴 <b>Медитация для сна:</b>\n\n"
        "Сейчас вы получите голосовую медитацию. Рекомендуется слушать "
        "ее лежа в кровати перед сном.",
        reply_markup=get_meditate_keyboard(),
        parse_mode="HTML"
    )
    
    try:
        # Отправляем сообщение о том, что медитация готовится
        preparing_message = await callback.message.answer(
            "⏳ Генерирую аудио медитацию...\n"
            "Это может занять несколько секунд."
        )
        
        # Генерируем аудио с помощью ElevenLabs API
        audio_path = await generate_audio(
            text=MEDITATION_TEXTS["sleep"],
            user_id=callback.from_user.id,
            meditation_type="sleep"
        )
        
        # Удаляем сообщение о подготовке
        await preparing_message.delete()
        
        if audio_path:
            # Проверяем, что файл существует
            if os.path.exists(audio_path):
                try:
                    # Отправляем голосовое сообщение
                    await callback.message.answer_voice(
                        FSInputFile(audio_path),
                        caption="😴 Медитация для сна. Лягте удобно и следуйте инструкциям."
                    )
                    logger.info(f"Голосовое сообщение успешно отправлено пользователю {callback.from_user.id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке голосового сообщения: {e}")
                    # Если не удалось отправить голосовое, отправляем текст медитации
                    await callback.message.answer(
                        f"<b>Не удалось отправить аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['sleep']}",
                        parse_mode="HTML"
                    )
            else:
                logger.error(f"Файл {audio_path} не существует")
                await callback.message.answer(
                    f"<b>Не удалось создать аудио-файл. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['sleep']}",
                    parse_mode="HTML"
                )
            
            # Удаляем временный файл
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Временный файл {audio_path} удален")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
        else:
            # Если не удалось сгенерировать аудио, отправляем текст медитации
            await callback.message.answer(
                f"<b>Не удалось сгенерировать аудио. Вот текст медитации:</b>\n\n{MEDITATION_TEXTS['sleep']}",
                parse_mode="HTML"
            )
        
        logger.info(f"Пользователь {callback.from_user.id} получил медитацию для сна")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке медитации: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при подготовке медитации. Пожалуйста, попробуйте позже."
        )

@meditate_router.callback_query(F.data == CallbackActions.HELP_MEDITATE)
async def help_meditate(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>СПРАВКА ПО МЕДИТАЦИЯМ</b>\n\n"
        "Голосовые медитации помогают расслабиться, снять стресс и улучшить концентрацию. "
        "Они представляют собой аудиозаписи с инструкциями для выполнения "
        "релаксационных упражнений.\n\n"
        "<b>Доступные типы медитаций:</b>\n\n"
        "🧘 <b>Медитация для расслабления</b>\n"
        "Помогает снять стресс, напряжение и тревогу. Эта медитация идеально подходит для периодов повышенного стресса или "
        "в конце напряженного дня. Она направлена на глубокое расслабление тела и успокоение ума через "
        "осознанное дыхание и визуализацию.\n\n"
        "🧠 <b>Медитация для фокусировки</b>\n"
        "Улучшает концентрацию внимания и ясность ума. Рекомендуется выполнять перед важными задачами, "
        "требующими концентрации, или в периоды, когда вам сложно сосредоточиться. Помогает устранить "
        "ментальный шум и направить внимание на конкретную задачу.\n\n"
        "😴 <b>Медитация для сна</b>\n"
        "Помогает быстрее заснуть и улучшить качество сна. Эта медитация использует техники прогрессивной "
        "релаксации и успокаивающие визуализации для подготовки тела и ума к глубокому, восстанавливающему сну. "
        "Рекомендуется выполнять лежа в постели непосредственно перед сном.\n\n"
        "<b>Рекомендации по практике:</b>\n"
        "• Найдите тихое место, где вас не будут беспокоить\n"
        "• Примите удобное положение (сидя или лежа)\n"
        "• Используйте наушники для лучшего восприятия\n"
        "• Следуйте инструкциям в аудио, не торопясь\n"
        "• Регулярная практика дает наилучшие результаты",
        reply_markup=get_meditate_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил справку по медитациям")

# Обработчики для инлайн-кнопок напоминаний
@reminder_router.callback_query(F.data == CallbackActions.REMINDER_ON)
async def reminder_on(callback: CallbackQuery):
    global reminder_users
    user_id = callback.from_user.id
    
    # Получаем время по умолчанию из переменных окружения
    default_time = os.getenv("DEFAULT_REMINDER_TIME", "20:00")
    hour, minute = map(int, default_time.split(":"))
    
    # Добавляем пользователя в словарь с напоминаниями
    reminder_users[user_id] = default_time
    
    # Создаем уникальный ID для задачи
    job_id = f"reminder_{user_id}"
    
    # Удаляем существующую задачу, если она есть
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Добавляем новую задачу в планировщик
    scheduler.add_job(
        send_reminder,
        CronTrigger(hour=hour, minute=minute),
        id=job_id,
        args=[callback.bot, user_id],
        replace_existing=True
    )
    
    # Если планировщик не запущен, запускаем его
    if not scheduler.running:
        scheduler.start()
    
    await callback.message.edit_text(
        f"⏰ <b>Напоминания включены</b>\n\n"
        f"Вы будете получать ежедневные напоминания о практиках в {default_time}.",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Напоминания включены!")
    logger.info(f"Пользователь {user_id} включил напоминания на {default_time}")

@reminder_router.callback_query(F.data == CallbackActions.REMINDER_OFF)
async def reminder_off(callback: CallbackQuery):
    global reminder_users
    user_id = callback.from_user.id
    
    # Удаляем пользователя из словаря напоминаний
    if user_id in reminder_users:
        del reminder_users[user_id]
    
    # Удаляем задачу из планировщика
    job_id = f"reminder_{user_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Задача напоминания {job_id} удалена из планировщика")
    
    await callback.message.edit_text(
        "🔕 <b>Напоминания отключены</b>\n\n"
        "Вы не будете получать напоминания о практиках.",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Напоминания отключены!")
    logger.info(f"Пользователь {user_id} отключил напоминания")

@reminder_router.callback_query(F.data == CallbackActions.REMINDER_STATUS)
async def reminder_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    job_id = f"reminder_{user_id}"
    job = scheduler.get_job(job_id)
    
    if job and user_id in reminder_users:
        reminder_time = reminder_users[user_id]
        status_text = (
            "📅 <b>Статус напоминаний:</b>\n\n"
            f"Напоминания о практиках: Включены\n"
            f"Расписание: Ежедневно в {reminder_time}"
        )
    else:
        status_text = (
            "📅 <b>Статус напоминаний:</b>\n\n"
            "Напоминания о практиках: Отключены\n"
            "Расписание: -"
        )
    
    await callback.message.edit_text(
        status_text,
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"Пользователь {user_id} запросил статус напоминаний")

@reminder_router.callback_query(F.data == CallbackActions.HELP_REMINDER)
async def help_reminder(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>Справка по напоминаниям:</b>\n\n"
        "Напоминания помогают вам регулярно выполнять психологические практики. "
        "Вы можете включить или отключить напоминания в любой момент.\n\n"
        "По умолчанию напоминания приходят ежедневно в 20:00.",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил справку по напоминаниям")

# Обработчик для кнопки Отмена
@main_router.message(Command("cancel"))
@main_router.message(F.text == "❌ Отменить опрос")
async def cancel_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ Текущий опрос отменен.",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {message.from_user.id} отменил опрос")
    else:
        await message.answer(
            "У вас нет активного опроса для отмены.",
            reply_markup=get_main_keyboard()
        )

# Обработчик неизвестных сообщений
@main_router.message()
async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Если пользователь находится в состоянии опроса
    if current_state == SurveyStates.answering_questions:
        # Перенаправляем обработку сообщения в соответствующий обработчик
        await process_survey_answer(message, state)
    # Если пользователь в состоянии ожидания начала опроса
    elif current_state == SurveyStates.waiting_start:
        # Установим состояние answering_questions и сохраним индекс текущего вопроса
        await state.set_state(SurveyStates.answering_questions)
        await state.update_data(question_index=0, answers={})
        
        # Задаем первый вопрос
        await message.answer(f"Вопрос 1: {DEMO_QUESTIONS[0]}")
        logger.info(f"Пользователь {message.from_user.id} начал отвечать на опрос")
    # Если пользователь завершил опрос
    elif current_state == SurveyStates.completed:
        await message.answer(
            "Вы успешно завершили опрос. Используйте кнопки меню для других функций.",
            reply_markup=get_main_keyboard()
        )
    # Если нет активного состояния или это другое состояние
    else:
        # Проверяем тип сообщения
        if message.text:
            # Если это текстовое сообщение, перенаправляем его в process_text_message
            await process_text_message(message, state)
        elif message.voice:
            # Если это голосовое сообщение, перенаправляем его в process_voice_message_handler
            await process_voice_message_handler(message, state)
        else:
            # Если это другой тип сообщения, отправляем стандартный ответ
            await message.answer(
                "Я не понимаю эту команду. Пожалуйста, используйте кнопки меню для взаимодействия.",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"Пользователь {message.from_user.id} отправил неподдерживаемый тип сообщения")

# Обработчики для опроса
@survey_router.message(SurveyStates.answering_questions)
async def process_survey_answer(message: Message, state: FSMContext):
    # Если пользователь хочет отменить опрос
    if message.text == "❌ Отменить опрос":
        await cancel_command(message, state)
        return
    
    # Получаем текущий индекс вопроса и ответы
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    answers = data.get("answers", {})
    
    # Определяем, в какой части опроса мы находимся
    is_strength_questions = data.get("is_strength_questions", False)
    
    # Сохраняем ответ пользователя
    if is_strength_questions:
        question_id = f"strength_{question_index + 1}"
    else:
        question_id = f"demo_{question_index + 1}"
    
    answers[question_id] = message.text
    
    # Переходим к следующему вопросу
    question_index += 1
    
    # Проверяем, есть ли еще вопросы в текущей части опроса
    if not is_strength_questions and question_index < len(DEMO_QUESTIONS):
        # Продолжаем демо-вопросы
        await state.update_data(question_index=question_index, answers=answers)
        await message.answer(f"Вопрос {question_index + 1}: {DEMO_QUESTIONS[question_index]}")
    elif not is_strength_questions and question_index >= len(DEMO_QUESTIONS):
        # Переходим к вопросам о сильных сторонах
        await state.update_data(
            question_index=0, 
            answers=answers,
            is_strength_questions=True
        )
        
        # Объясняем шкалу оценки
        scale_explanation = "Теперь я задам вопросы для определения твоих сильных сторон.\n\n"
        scale_explanation += "Оцени каждое утверждение по шкале от 1 до 5, где:\n"
        scale_explanation += "1 - Совсем не про меня\n"
        scale_explanation += "2 - Скорее не про меня\n"
        scale_explanation += "3 - Нейтрально\n"
        scale_explanation += "4 - Скорее про меня\n"
        scale_explanation += "5 - Точно про меня\n\n"
        scale_explanation += "Отвечай только цифрой от 1 до 5."
        
        await message.answer(scale_explanation)
        
        # Задаем первый вопрос о сильных сторонах
        if STRENGTH_QUESTIONS:
            await message.answer(
                f"Вопрос 1/{len(STRENGTH_QUESTIONS)}: {STRENGTH_QUESTIONS[0]['text']}"
            )
        else:
            # Если вопросы о сильных сторонах не найдены, завершаем опрос
            await complete_survey(message, state, answers)
    elif is_strength_questions and question_index < len(STRENGTH_QUESTIONS):
        # Продолжаем вопросы о сильных сторонах
        await state.update_data(question_index=question_index, answers=answers)
        await message.answer(
            f"Вопрос {question_index + 1}/{len(STRENGTH_QUESTIONS)}: {STRENGTH_QUESTIONS[question_index]['text']}"
        )
    else:
        # Завершаем опрос
        await complete_survey(message, state, answers)

# Функция для завершения опроса и анализа результатов
async def complete_survey(message: Message, state: FSMContext, answers: Dict[str, str]):
    """Функция для завершения опроса и анализа результатов."""
    await state.set_state(SurveyStates.completed)
    
    # Сообщаем пользователю о начале обработки
    await message.answer("Анализирую твои ответы... Это может занять несколько секунд.")
    
    # Расчет баллов по категориям
    if CATEGORY_QUESTIONS:
        scores = {}
        
        # Инициализация счетчиков для каждой категории
        for category in CATEGORY_QUESTIONS:
            scores[category] = {"total": 0, "count": 0}
        
        # Подсчет баллов
        for question_id, answer in answers.items():
            if question_id.startswith("strength_") and answer.isdigit():
                q_id = question_id
                for category, questions in CATEGORY_QUESTIONS.items():
                    if q_id in questions:
                        scores[category]["total"] += int(answer)
                        scores[category]["count"] += 1
        
        # Расчет средних значений
        final_scores = {}
        for category, data in scores.items():
            if data["count"] > 0:
                final_scores[category] = round(data["total"] / data["count"], 2)
            else:
                final_scores[category] = 0
        
        # Определение топ-3 сильных сторон
        top_strengths = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_strengths_names = []
        
        for category, score in top_strengths:
            top_strengths_names.append(STRENGTH_CATEGORIES.get(category, category))
        
        # Отправляем результаты пользователю
        result_message = "✅ <b>Опрос завершен!</b>\n\n"
        
        if top_strengths_names:
            result_message += "🏆 <b>Твои топ-3 сильные стороны:</b>\n"
            for i, strength in enumerate(top_strengths_names, 1):
                result_message += f"{i}. {strength}\n"
            result_message += "\n"
        
        if final_scores:
            result_message += "📊 <b>Твои оценки по категориям:</b>\n"
            for category, score in final_scores.items():
                category_name = STRENGTH_CATEGORIES.get(category, category)
                result_message += f"- {category_name}: {score}/5\n"
            result_message += "\n"
        
        # Психологический анализ профиля
        result_message += "🧠 <b>Психологический анализ твоего профиля:</b>\n\n"
        
        # Собираем психологический анализ на основе топ-сильных сторон
        personality_traits = {
            "analytical": "Ты обладаешь аналитическим складом ума. Твоя способность логически мыслить и анализировать информацию помогает тебе находить оптимальные решения сложных задач.",
            "creative": "Ты творческая личность с богатым воображением. Твоя способность мыслить нестандартно и генерировать новые идеи делает тебя ценным участником любой команды.",
            "leadership": "У тебя ярко выражены лидерские качества. Ты умеешь вдохновлять других и брать на себя ответственность, что делает тебя естественным лидером в группе.",
            "social": "Ты обладаешь высоким эмоциональным интеллектом и коммуникативными навыками. Твоя способность понимать других и строить гармоничные отношения ценится в любом коллективе.",
            "organized": "Ты организованный и ответственный человек. Твоя способность планировать и структурировать работу помогает тебе эффективно достигать поставленных целей.",
            "resilient": "Ты обладаешь высокой стрессоустойчивостью и адаптивностью. Твоя способность сохранять спокойствие и эффективность в сложных ситуациях - это ценное качество."
        }
        
        # Добавляем анализ для топ-3 категорий
        for category, _ in top_strengths:
            if category in personality_traits:
                result_message += f"{personality_traits[category]}\n\n"
        
        # Ключевые сильные стороны
        result_message += "💪 <b>Твои ключевые сильные стороны:</b>\n"
        strength_traits = {
            "analytical": ["Критическое мышление", "Системный подход к решению задач", "Способность видеть логические связи"],
            "creative": ["Генерация новых идей", "Нестандартное мышление", "Творческий подход к задачам"],
            "leadership": ["Умение вдохновлять других", "Стратегическое мышление", "Решительность"],
            "social": ["Эмпатия", "Коммуникабельность", "Умение работать в команде"],
            "organized": ["Организованность", "Внимание к деталям", "Пунктуальность"],
            "resilient": ["Стрессоустойчивость", "Адаптивность", "Настойчивость"]
        }
        
        # Добавляем 3 ключевые сильные стороны для каждой из топ-3 категорий
        strength_count = 1
        for category, _ in top_strengths:
            if category in strength_traits:
                for trait in strength_traits[category]:
                    result_message += f"{strength_count}. {trait}\n"
                    strength_count += 1
        
        result_message += "\n"
        
        # Направления для развития
        result_message += "🌱 <b>Направления для развития:</b>\n"
        
        # Определяем слабые стороны (с самыми низкими баллами)
        bottom_strengths = sorted(final_scores.items(), key=lambda x: x[1])[:2]
        
        growth_areas = {
            "analytical": ["Развивай критическое мышление через решение логических задач", "Практикуй анализ информации из разных источников"],
            "creative": ["Экспериментируй с новыми хобби", "Уделяй время творческим занятиям"],
            "leadership": ["Практикуй публичные выступления", "Бери на себя ответственность за групповые проекты"],
            "social": ["Развивай эмпатию через общение с разными людьми", "Практикуй активное слушание"],
            "organized": ["Используй планировщики и системы организации", "Практикуй тайм-менеджмент"],
            "resilient": ["Развивай устойчивость к стрессу через регулярные практики", "Работай над адаптивностью к изменениям"]
        }
        
        # Добавляем рекомендации для развития слабых сторон
        growth_count = 1
        for category, _ in bottom_strengths:
            if category in growth_areas:
                for area in growth_areas[category]:
                    result_message += f"{growth_count}. {area}\n"
                    growth_count += 1
        
        await message.answer(result_message, parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        # Если не удалось импортировать категории, просто показываем ответы
        result_text = "✅ <b>Опрос завершен!</b>\n\n<b>Ваши ответы:</b>\n\n"
        for i, answer in enumerate(answers.values()):
            if i < len(DEMO_QUESTIONS):
                result_text += f"<b>Вопрос {i + 1}:</b> {DEMO_QUESTIONS[i]}\n"
                result_text += f"<b>Ответ:</b> {answer}\n\n"
        
        await message.answer(
            result_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    
    logger.info(f"Пользователь {message.from_user.id} завершил опрос")

# Обработчик для команды начала опроса
@survey_router.message(Command("questionnaire"))
@survey_router.message(F.text == "📝 Опрос")
async def start_survey(message: Message, state: FSMContext):
    # Проверяем, есть ли у пользователя уже заполненный профиль
    user_data = await state.get_data()
    has_profile = user_data.get("answers", {}) and any(key.startswith("demo_") for key in user_data.get("answers", {}))
    
    if has_profile:
        # Создаем клавиатуру с кнопками подтверждения
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Да, начать заново", callback_data="confirm_survey_button")
        builder.button(text="❌ Нет, отмена", callback_data=CallbackActions.MAIN_MENU)
        builder.adjust(2)  # Размещаем обе кнопки в одном ряду
        
        await message.answer(
            "⚠️ <b>Внимание:</b>\n\n"
            "У вас уже есть заполненный профиль. Если вы пройдете опрос заново, "
            "ваши текущие данные будут перезаписаны.\n\n"
            "Вы уверены, что хотите начать опрос заново?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return
    
    # Если профиля нет, начинаем опрос
    # Инициализируем опрос
    await state.set_state(SurveyStates.answering_questions)
    await state.update_data(
        question_index=0,
        answers={},
        is_strength_questions=False
    )
    
    # Приветственное сообщение
    await message.answer(
        "📋 <b>Начинаем опрос!</b>\n\n"
        "Я задам несколько вопросов, чтобы лучше узнать тебя. "
        "Сначала ответь на несколько базовых вопросов, а затем мы перейдем к "
        "специальному тесту для определения твоих сильных сторон.",
        parse_mode="HTML"
    )
    
    # Показываем первый вопрос
    await message.answer(
        f"Вопрос 1: {DEMO_QUESTIONS[0]}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
            resize_keyboard=True,
            one_time_keyboard=False,
            is_persistent=True,
            input_field_placeholder="Введите ваш ответ..."
        )
    )
    logger.info(f"Пользователь {message.from_user.id} начал опрос")

@profile_router.callback_query(F.data == "show_test_results")
async def show_test_results(callback: CallbackQuery, state: FSMContext):
    # Получаем данные пользователя из состояния
    user_data = await state.get_data()
    
    # Проверяем наличие ответов
    if not user_data or "answers" not in user_data:
        await callback.answer("Результаты теста не найдены")
        return
    
    answers = user_data.get("answers", {})
    
    # Собираем ответы на вопросы о сильных сторонах
    strength_answers = {}
    for key, value in answers.items():
        if key.startswith("strength_") and value.isdigit():
            question_id = key
            strength_answers[question_id] = int(value)
    
    # Если нет ответов на вопросы о сильных сторонах
    if not strength_answers:
        await callback.answer("Результаты теста не найдены")
        return
    
    logger.info(f"Найдено {len(strength_answers)} ответов на вопросы о сильных сторонах")
    
    # Рассчитываем баллы по категориям
    scores = {}
    
    # Инициализация счетчиков для каждой категории
    for category in CATEGORY_QUESTIONS:
        scores[category] = {"total": 0, "count": 0}
    
    # Подсчет баллов
    for question_id, answer_value in strength_answers.items():
        for category, questions in CATEGORY_QUESTIONS.items():
            if question_id in questions:
                scores[category]["total"] += answer_value
                scores[category]["count"] += 1
                logger.info(f"Добавлен балл {answer_value} в категорию {category} для вопроса {question_id}")
    
    # Расчет средних значений
    final_scores = {}
    for category, data in scores.items():
        if data["count"] > 0:
            final_scores[category] = round(data["total"] / data["count"], 2)
        else:
            final_scores[category] = 0
    
    logger.info(f"Финальные оценки по категориям: {final_scores}")
    
    # Определение топ-3 сильных сторон
    top_strengths = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_strengths_names = []
    
    for category, score in top_strengths:
        category_name = STRENGTH_CATEGORIES.get(category, category)
        top_strengths_names.append(f"{category_name} ({score}/5)")
    
    # Формируем результаты теста с более красивым форматированием
    result_message = "📊 <b>РЕЗУЛЬТАТЫ ПСИХОЛОГИЧЕСКОГО ТЕСТА</b>\n"
    result_message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Добавляем базовую информацию
    demo_answers = {}
    for key, value in answers.items():
        if key.startswith("demo_"):
            question_index = int(key.split("_")[1]) - 1
            if question_index < len(DEMO_QUESTIONS):
                demo_answers[question_index] = value
    
    if demo_answers:
        result_message += "👤 <b>ЛИЧНАЯ ИНФОРМАЦИЯ</b>\n"
        
        # Словарь с красивыми обозначениями полей
        field_icons = {
            "Как тебя зовут?": "👤 <b>Имя:</b> ",
            "Сколько тебе лет?": "🎂 <b>Возраст:</b> ",
            "Какая у тебя дата рождения?": "📅 <b>Дата рождения:</b> ",
            "Какая у тебя дата рождения? (формат: ДД.ММ.ГГГГ)": "📅 <b>Дата рождения:</b> ",
            "Где ты родился/родилась?": "🌍 <b>Место рождения:</b> ",
            "Где ты родился/родилась? (город, страна)": "🌍 <b>Место рождения:</b> ",
            "В каком часовом поясе ты находишься?": "🕒 <b>Часовой пояс:</b> "
        }
        
        # Сортируем и добавляем ответы на демо-вопросы в красивом формате
        for i in sorted(demo_answers.keys()):
            if i < len(DEMO_QUESTIONS):
                question = DEMO_QUESTIONS[i]
                answer = demo_answers[i]
                
                # Используем иконки и форматирование для каждого поля
                if question in field_icons:
                    result_message += f"{field_icons[question]}{answer}\n"
                else:
                    # Для необработанных вопросов используем стандартный формат
                    result_message += f"• <b>{question}</b> {answer}\n"
        
        result_message += "\n"
    
    # Добавляем топ-3 сильные стороны
    if top_strengths_names:
        result_message += "🏆 <b>ТОП-3 СИЛЬНЫЕ СТОРОНЫ</b>\n"
        for i, strength in enumerate(top_strengths, 1):
            category, score = strength
            category_name = STRENGTH_CATEGORIES.get(category, category)
            # Добавляем звездочки для визуального отображения оценки
            stars = "★" * round(score) + "☆" * (5 - round(score))
            result_message += f"{i}. <b>{category_name}</b> ({score}/5) {stars}\n"
        result_message += "\n"
    
    # Добавляем оценки по всем категориям
    if final_scores:
        result_message += "📈 <b>ОЦЕНКИ ПО КАТЕГОРИЯМ</b>\n"
        
        # Сортируем категории по убыванию оценок
        sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        for category, score in sorted_scores:
            category_name = STRENGTH_CATEGORIES.get(category, category)
            # Добавляем визуальное представление оценки
            stars = "★" * round(score) + "☆" * (5 - round(score))
            result_message += f"• <b>{category_name}:</b> {score}/5 {stars}\n"
        
        result_message += "\n"
    
    # Психологический анализ профиля
    result_message += "🧠 <b>ПСИХОЛОГИЧЕСКИЙ АНАЛИЗ ПРОФИЛЯ</b>\n\n"
    
    # Собираем психологический анализ на основе топ-сильных сторон
    personality_traits = {
        "analytical": "Вы обладаете аналитическим складом ума. Ваша способность логически мыслить и анализировать информацию помогает вам находить оптимальные решения сложных задач.",
        "creative": "Вы творческая личность с богатым воображением. Ваша способность мыслить нестандартно и генерировать новые идеи делает вас ценным участником любой команды.",
        "leadership": "У вас ярко выражены лидерские качества. Вы умеете вдохновлять других и брать на себя ответственность, что делает вас естественным лидером в группе.",
        "social": "Вы обладаете высоким эмоциональным интеллектом и коммуникативными навыками. Ваша способность понимать других и строить гармоничные отношения ценится в любом коллективе.",
        "organized": "Вы организованный и ответственный человек. Ваша способность планировать и структурировать работу помогает вам эффективно достигать поставленных целей.",
        "resilient": "Вы обладаете высокой стрессоустойчивостью и адаптивностью. Ваша способность сохранять спокойствие и эффективность в сложных ситуациях - это ценное качество."
    }
    
    # Добавляем анализ для топ-3 категорий
    for category, _ in top_strengths:
        if category in personality_traits:
            result_message += f"{personality_traits[category]}\n\n"
    
    # Ключевые сильные стороны
    result_message += "💪 <b>КЛЮЧЕВЫЕ СИЛЬНЫЕ СТОРОНЫ</b>\n"
    strength_traits = {
        "analytical": ["Критическое мышление", "Системный подход к решению задач", "Способность видеть логические связи"],
        "creative": ["Генерация новых идей", "Нестандартное мышление", "Творческий подход к задачам"],
        "leadership": ["Умение вдохновлять других", "Стратегическое мышление", "Решительность"],
        "social": ["Эмпатия", "Коммуникабельность", "Умение работать в команде"],
        "organized": ["Организованность", "Внимание к деталям", "Пунктуальность"],
        "resilient": ["Стрессоустойчивость", "Адаптивность", "Настойчивость"]
    }
    
    # Добавляем 3 ключевые сильные стороны для каждой из топ-3 категорий
    strength_count = 1
    for category, _ in top_strengths:
        if category in strength_traits and strength_count <= 9:  # Ограничиваем до 9 ключевых качеств
            for trait in strength_traits[category]:
                result_message += f"• {trait}\n"
                strength_count += 1
    
    result_message += "\n"
    
    # Направления для развития
    result_message += "🌱 <b>НАПРАВЛЕНИЯ ДЛЯ РАЗВИТИЯ</b>\n"
    
    # Определяем слабые стороны (с самыми низкими баллами)
    bottom_strengths = sorted(final_scores.items(), key=lambda x: x[1])[:2]
    
    growth_areas = {
        "analytical": ["Развивайте критическое мышление через решение логических задач", "Практикуйте анализ информации из разных источников"],
        "creative": ["Экспериментируйте с новыми хобби", "Уделяйте время творческим занятиям"],
        "leadership": ["Практикуйте публичные выступления", "Берите на себя ответственность за групповые проекты"],
        "social": ["Развивайте эмпатию через общение с разными людьми", "Практикуйте активное слушание"],
        "organized": ["Используйте планировщики и системы организации", "Практикуйте тайм-менеджмент"],
        "resilient": ["Развивайте устойчивость к стрессу через регулярные практики", "Работайте над адаптивностью к изменениям"]
    }
    
    # Добавляем рекомендации для развития слабых сторон
    growth_count = 1
    for category, _ in bottom_strengths:
        if category in growth_areas and growth_count <= 4:  # Ограничиваем до 4 направлений развития
            for area in growth_areas[category]:
                result_message += f"• {area}\n"
                growth_count += 1
    
    # Создаем клавиатуру для возврата в профиль
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Вернуться к профилю", callback_data=CallbackActions.PROFILE)
    builder.button(text="◀️ Назад в меню", callback_data=CallbackActions.MAIN_MENU)
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        result_message,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} просмотрел результаты теста")

# Обработчик для текстовых сообщений
@main_router.message(F.text, ~F.text.startswith('/'))
async def process_text_message(message: Message, state: FSMContext):
    """Обработчик текстовых сообщений пользователя (не команд)."""
    # Проверяем текущее состояние FSM, чтобы не дублировать обработку сообщений во время опроса
    current_state = await state.get_state()
    if current_state is not None and current_state != SurveyStates.completed:
        # Если пользователь находится в каком-то состоянии (например, проходит опрос),
        # то не обрабатываем сообщение здесь
        logger.debug(f"Пропуск обработки текстового сообщения: пользователь {message.from_user.id} находится в состоянии {current_state}")
        return
    
    # Отправляем индикатор набора текста, чтобы пользователь видел, что бот "печатает"
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Импортируем функцию для генерации ответа из services/recs.py
        from services.recs import generate_response as generate_ai_response
        
        # Генерируем контекстуальный ответ
        response = await generate_ai_response(
            text=message.text,
            user_id=message.from_user.id
        )
        
        # Отправляем ответ
        await message.answer(response)
        logger.info(f"Отправлен ответ пользователю {message.from_user.id} на основе текстового сообщения")
    except Exception as e:
        # В случае ошибки отправляем заготовленный ответ
        logger.error(f"Ошибка при генерации ответа: {e}")
        await message.answer(
            "Извините, не удалось обработать ваше сообщение. Пожалуйста, попробуйте позже или воспользуйтесь командами бота."
        )
    logger.info(f"Пользователь {message.from_user.id} отправил сообщение: {message.text}")

# Обработчик для голосовых сообщений
@main_router.message(F.voice)
async def process_voice_message_handler(message: Message, state: FSMContext):
    """Обработчик голосовых сообщений."""
    # Проверяем текущее состояние FSM, чтобы не дублировать обработку сообщений во время опроса
    current_state = await state.get_state()
    if current_state is not None and current_state != SurveyStates.completed:
        # Если пользователь находится в каком-то состоянии (например, проходит опрос),
        # то не обрабатываем сообщение здесь
        logger.debug(f"Пропуск обработки голосового сообщения: пользователь {message.from_user.id} находится в состоянии {current_state}")
        return
    
    # Отправляем сообщение о начале обработки
    processing_message = await message.answer("Обрабатываю ваше голосовое сообщение...")
    
    try:
        # Импортируем функции для обработки голосовых сообщений
        from services.stt import process_voice_message
        from services.recs import generate_response as generate_ai_response
        
        # Отправляем индикатор набора текста
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Транскрибируем голосовое сообщение
        transcribed_text = await process_voice_message(message.bot, message.voice)
        
        if transcribed_text:
            # Если текст успешно распознан, то отправляем его пользователю
            await processing_message.edit_text(f"Я распознал: «{transcribed_text}»")
            
            # Генерируем контекстуальный ответ с учетом типа сообщения
            response = await generate_ai_response(
                text=transcribed_text,
                user_id=message.from_user.id
            )
            
            # Отправляем ответ
            await message.answer(response)
            logger.info(f"Отправлен ответ пользователю {message.from_user.id} на основе голосового сообщения")
        else:
            # Если текст не распознан, то отправляем сообщение об ошибке
            await processing_message.edit_text(
                "Извините, не удалось распознать ваше голосовое сообщение. "
                "Пожалуйста, попробуйте еще раз или отправьте текстовое сообщение."
            )
            logger.warning(f"Не удалось распознать голосовое сообщение пользователя {message.from_user.id}")
    except Exception as e:
        # В случае ошибки отправляем сообщение об ошибке
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await processing_message.edit_text(
            "Извините, произошла ошибка при обработке вашего голосового сообщения. "
            "Пожалуйста, попробуйте еще раз или отправьте текстовое сообщение."
        )

# Инициализация и запуск бота
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
        dp.include_router(survey_router)  # Добавляем роутер для опроса
        
        # Запуск планировщика заданий, если есть активные напоминания
        if not scheduler.running and reminder_users:
            scheduler.start()
        
        # Запуск бота
        logger.info("Запуск бота...")
        
        # Устанавливаем allowed_updates, чтобы избежать конфликтов и улучшить производительность
        allowed_updates = ["message", "callback_query"]
        
        # Сначала проверяем, нет ли уже запущенных экземпляров
        try:
            # Отправляем простой запрос, чтобы проверить соединение
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
        
        # Настраиваем таймаут и повторные попытки
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