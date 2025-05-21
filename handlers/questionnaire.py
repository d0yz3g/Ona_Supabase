import logging
from typing import Dict, List, Union, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Database
from states import QuestionnaireStates
from questions import (
    get_demo_questions, 
    get_strength_questions, 
    get_strength_options_labels, 
    get_question_by_id
)
from services.astrology import make_natal_chart
from services.ai_client import generate_profile

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Инициализация роутера
questionnaire_router = Router(name="questionnaire")

# Обработчик команды для начала опроса
@questionnaire_router.message(Command("questionnaire"))
@questionnaire_router.message(Command("begin"))
@questionnaire_router.message(F.text.lower() == "начать опрос")
async def start_questionnaire(message: Message, state: FSMContext):
    """Обработчик начала опроса."""
    user = db.get_user_by_tg_id(message.from_user.id)
    if not user:
        user_id = db.add_user(
            message.from_user.id,
            f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        )
    else:
        user_id = user["id"]
    
    # Проверка наличия профиля
    profile = db.get_profile(user_id)
    if profile:
        await message.answer(
            "У вас уже есть созданный профиль. "
            "Хотите пройти опрос заново? (Это перезапишет ваш текущий профиль)"
        )
        # Предложить кнопки Да/Нет
        builder = InlineKeyboardBuilder()
        builder.button(text="Да", callback_data="restart_questionnaire")
        builder.button(text="Нет", callback_data="cancel_questionnaire")
        await message.answer("Выберите действие:", reply_markup=builder.as_markup())
        return
    
    # Сохраняем ID пользователя в FSM-контексте
    await state.update_data(user_id=user_id)
    
    # Начинаем опрос
    await state.set_state(QuestionnaireStates.started)
    await message.answer(
        "Отлично! Сейчас я задам несколько вопросов, чтобы лучше узнать тебя. "
        "Сначала ответь на несколько базовых вопросов."
    )
    
    # Переход к первому демо-вопросу
    await ask_next_demo_question(message, state)
    
    logger.info(f"Пользователь {message.from_user.id} начал опрос")

# Обработчик для кнопок Да/Нет при перезапуске опроса
@questionnaire_router.callback_query(F.data == "restart_questionnaire")
async def restart_questionnaire(callback: CallbackQuery, state: FSMContext):
    """Обработчик перезапуска опроса."""
    user = db.get_user_by_tg_id(callback.from_user.id)
    await state.update_data(user_id=user["id"])
    
    # Начинаем опрос заново
    await state.set_state(QuestionnaireStates.started)
    await callback.message.answer(
        "Хорошо! Начинаем опрос заново. "
        "Сначала ответь на несколько базовых вопросов."
    )
    
    # Переход к первому демо-вопросу
    await ask_next_demo_question(callback.message, state)
    await callback.answer()
    
    logger.info(f"Пользователь {callback.from_user.id} перезапустил опрос")

@questionnaire_router.callback_query(F.data == "cancel_questionnaire")
async def cancel_restart(callback: CallbackQuery):
    """Обработчик отмены перезапуска опроса."""
    await callback.message.answer("Хорошо, опрос не будет перезапущен.")
    await callback.answer()

# Отправка следующего демо-вопроса
async def ask_next_demo_question(message: Message, state: FSMContext):
    """Функция для отправки следующего демо-вопроса."""
    # Получаем текущее состояние
    user_data = await state.get_data()
    current_demo_question_index = user_data.get("current_demo_question_index", 0)
    demo_questions = get_demo_questions()
    
    # Проверяем, есть ли еще вопросы
    if current_demo_question_index < len(demo_questions):
        # Получаем текущий вопрос
        question = demo_questions[current_demo_question_index]
        
        # Отправляем вопрос
        await message.answer(question["text"])
        
        # Обновляем состояние
        await state.update_data(
            current_demo_question_index=current_demo_question_index + 1,
            current_question_id=question["id"]
        )
        await state.set_state(QuestionnaireStates.demo_questions)
    else:
        # Переходим к вопросам о сильных сторонах
        await message.answer(
            "Спасибо за ответы на базовые вопросы! "
            "Теперь я задам вопросы для определения твоих сильных сторон. "
            "Оцени каждое утверждение по шкале от 1 до 5, где:\n"
            "1 - Совсем не про меня\n"
            "2 - Скорее не про меня\n"
            "3 - Нейтрально\n"
            "4 - Скорее про меня\n"
            "5 - Точно про меня"
        )
        await ask_next_strength_question(message, state)

# Отправка следующего вопроса о сильных сторонах
async def ask_next_strength_question(message: Message, state: FSMContext):
    """Функция для отправки следующего вопроса о сильных сторонах."""
    # Получаем текущее состояние
    user_data = await state.get_data()
    current_strength_question_index = user_data.get("current_strength_question_index", 0)
    strength_questions = get_strength_questions()
    
    # Проверяем, есть ли еще вопросы
    if current_strength_question_index < len(strength_questions):
        # Получаем текущий вопрос
        question = strength_questions[current_strength_question_index]
        
        # Создаем клавиатуру с вариантами ответов
        builder = InlineKeyboardBuilder()
        options_labels = get_strength_options_labels()
        
        for option in question["options"]:
            callback_data = f"strength_{question['id']}_{option}"
            label = f"{option} - {options_labels[option]}"
            builder.button(text=label, callback_data=callback_data)
        
        # Располагаем кнопки в один столбец
        builder.adjust(1)
        
        # Отправляем вопрос с клавиатурой
        await message.answer(
            f"{current_strength_question_index + 1}/{len(strength_questions)}: {question['text']}",
            reply_markup=builder.as_markup()
        )
        
        # Обновляем состояние
        await state.update_data(
            current_strength_question_index=current_strength_question_index + 1,
            current_question_id=question["id"]
        )
        await state.set_state(QuestionnaireStates.strength_questions)
    else:
        # Завершаем опрос и переходим к обработке результатов
        await state.set_state(QuestionnaireStates.processing)
        await process_questionnaire_results(message, state)

# Обработчик ответов на демо-вопросы
@questionnaire_router.message(QuestionnaireStates.demo_questions)
async def process_demo_answer(message: Message, state: FSMContext):
    """Обработчик ответов на демо-вопросы."""
    # Получаем данные из состояния
    user_data = await state.get_data()
    user_id = user_data["user_id"]
    question_id = user_data["current_question_id"]
    
    # Сохраняем ответ
    db.add_answer(user_id, question_id, message.text)
    logger.info(f"Сохранен ответ на демо-вопрос {question_id}: {message.text}")
    
    # Переходим к следующему вопросу
    await ask_next_demo_question(message, state)

# Обработчик ответов на вопросы о сильных сторонах
@questionnaire_router.callback_query(F.data.startswith("strength_"))
async def process_strength_answer(callback: CallbackQuery, state: FSMContext):
    """Обработчик ответов на вопросы о сильных сторонах."""
    # Разбираем callback_data
    _, question_id, answer = callback.data.split("_")
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    user_id = user_data["user_id"]
    
    # Сохраняем ответ
    db.add_answer(user_id, question_id, answer)
    logger.info(f"Сохранен ответ на вопрос о сильных сторонах {question_id}: {answer}")
    
    # Обновляем сообщение с вопросом, чтобы показать выбранный ответ
    options_labels = get_strength_options_labels()
    question = get_question_by_id(question_id)
    await callback.message.edit_text(
        f"{user_data.get('current_strength_question_index', 0)}/{len(get_strength_questions())}: {question['text']}\n\n"
        f"Ваш ответ: {answer} - {options_labels[answer]}"
    )
    
    # Отвечаем на callback_query, чтобы убрать "часики" на кнопке
    await callback.answer()
    
    # Переходим к следующему вопросу
    await ask_next_strength_question(callback.message, state)

async def build_profile(user_id: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Строит профиль пользователя на основе ответов на вопросы.
    
    Args:
        user_id: ID пользователя в базе данных.
        answers: Список ответов на вопросы в формате [{"q_code": "q1", "value": "ответ"}, ...].
        
    Returns:
        Dict[str, Any]: Сгенерированный профиль пользователя.
    """
    # Инициализируем базовую структуру профиля
    profile = {
        "summary_json": {
            "name": "Неизвестно",
            "birthdate": None,
            "birthplace": None,
            "age": None,
            "gender": None,
            "scores": {
                "analytical": 0,
                "creative": 0,
                "leadership": 0,
                "social": 0,
                "organized": 0,
                "resilient": 0
            },
            "strengths": [],
            "ai_analysis": {}
        },
        "natal_json": {}
    }
    
    # Обрабатываем ответы на демо-вопросы
    demo_answers = {}
    for answer in answers:
        if answer["q_code"].startswith("demo_"):
            demo_answers[answer["q_code"]] = answer["value"]
    
    # Обновляем профиль на основе демо-ответов
    if "demo_name" in demo_answers:
        profile["summary_json"]["name"] = demo_answers["demo_name"]
    
    if "demo_birthdate" in demo_answers:
        profile["summary_json"]["birthdate"] = demo_answers["demo_birthdate"]
    
    if "demo_birthplace" in demo_answers:
        profile["summary_json"]["birthplace"] = demo_answers["demo_birthplace"]
    
    if "demo_age" in demo_answers:
        try:
            profile["summary_json"]["age"] = int(demo_answers["demo_age"])
        except (ValueError, TypeError):
            profile["summary_json"]["age"] = None
    
    if "demo_gender" in demo_answers:
        profile["summary_json"]["gender"] = demo_answers["demo_gender"]
    
    # Обрабатываем ответы на вопросы о сильных сторонах
    strength_scores = {
        "analytical": 0,
        "creative": 0,
        "leadership": 0,
        "social": 0,
        "organized": 0,
        "resilient": 0
    }
    
    strength_counts = {k: 0 for k in strength_scores}
    
    for answer in answers:
        if answer["q_code"].startswith("strength_"):
            # Получаем категорию вопроса
            question = get_question_by_id(answer["q_code"])
            if question and "category" in question:
                category = question["category"]
                if category in strength_scores:
                    try:
                        score = int(answer["value"])
                        strength_scores[category] += score
                        strength_counts[category] += 1
                    except (ValueError, TypeError):
                        pass
    
    # Вычисляем средние баллы по категориям
    for category in strength_scores:
        if strength_counts[category] > 0:
            strength_scores[category] = round(strength_scores[category] / strength_counts[category], 1)
    
    profile["summary_json"]["scores"] = strength_scores
    
    # Определяем топ-3 сильных сторон
    top_strengths = sorted(
        strength_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    # Словарь для перевода категорий на русский
    category_names = {
        "analytical": "Аналитический склад ума",
        "creative": "Творческое мышление",
        "leadership": "Лидерские качества",
        "social": "Коммуникабельность",
        "organized": "Организованность",
        "resilient": "Психологическая устойчивость"
    }
    
    # Добавляем переведенные названия топ-3 сильных сторон
    profile["summary_json"]["strengths"] = [category_names.get(category, category) for category, _ in top_strengths]
    
    # Если есть дата и место рождения, создаем натальную карту
    if profile["summary_json"]["birthdate"] and profile["summary_json"]["birthplace"]:
        try:
            natal_data = make_natal_chart(
                profile["summary_json"]["birthdate"],
                profile["summary_json"]["birthplace"],
                profile["summary_json"]["name"]
            )
            profile["natal_json"] = natal_data
        except Exception as e:
            logger.error(f"Ошибка при создании натальной карты: {e}")
            profile["natal_json"] = {"error": str(e)}
    
    # Вызываем OpenAI для анализа профиля
    try:
        ai_analysis = await generate_profile(profile["summary_json"])
        profile["summary_json"]["ai_analysis"] = ai_analysis
    except Exception as e:
        logger.error(f"Ошибка при генерации AI-анализа: {e}")
        profile["summary_json"]["ai_analysis"] = {
            "summary": "Не удалось сгенерировать психологический анализ из-за технической ошибки.",
            "strengths": [],
            "growth_areas": []
        }
    
    return profile

async def process_questionnaire_results(message: Message, state: FSMContext):
    """
    Обрабатывает результаты опроса и создает профиль пользователя.
    
    Args:
        message: Объект сообщения для ответа пользователю.
        state: Контекст FSM для получения данных о текущем состоянии опроса.
    """
    # Получаем ID пользователя из состояния
    user_data = await state.get_data()
    user_id = user_data["user_id"]
    
    # Отправляем сообщение о начале обработки
    await message.answer("Спасибо за ответы! Анализирую результаты...")
    
    # Получаем все ответы пользователя
    answers = db.get_answers(user_id)
    
    if not answers:
        await message.answer("К сожалению, не найдены ваши ответы на вопросы. Пожалуйста, начните опрос заново.")
        await state.clear()
        return
    
    # Генерируем профиль
    profile = await build_profile(user_id, answers)
    
    # Сохраняем профиль в базу данных
    db.add_or_update_profile(user_id, profile)
    
    # Формируем сообщение с результатами
    summary = profile["summary_json"]
    name = summary.get("name", "Неизвестно")
    strengths = summary.get("strengths", [])
    scores = summary.get("scores", {})
    
    # Базовое сообщение с профилем
    profile_message = f"Профиль пользователя {name} создан!\n\n"
    
    if strengths:
        profile_message += "Ваши сильные стороны:\n"
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
    natal = profile.get("natal_json", {})
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
    
    # Завершаем опрос
    await message.answer(
        "Опрос завершен! Теперь вы можете использовать команду /profile, "
        "чтобы просмотреть свой профиль в любой момент. "
        "Также попробуйте команду /reflect для получения советов на основе вашего профиля."
    )
    
    # Очищаем состояние
    await state.clear()
    
    logger.info(f"Профиль пользователя {user_id} создан и сохранен в базу данных")

# Обработчик команды /cancel для прерывания опроса
@questionnaire_router.message(Command("cancel"))
async def cancel_questionnaire(message: Message, state: FSMContext):
    """Обработчик команды для отмены опроса."""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нет активного опроса для отмены.")
        return
    
    # Очищаем состояние
    await state.clear()
    
    await message.answer("Опрос отменен. Вы можете начать заново в любой момент с помощью команды /questionnaire.")
    logger.info(f"Пользователь {message.from_user.id} отменил опрос") 