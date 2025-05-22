import logging
from typing import Dict, List, Union, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Database
from states import QuestionnaireStates
from questions import (    get_demo_questions,     get_strength_questions,     get_strength_options_labels,    get_question_by_id)
from services.astrology import make_natal_chart
from services.ai_client import generate_profile

# Инициализация логгера
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Инициализация роутера
router = Router(name="questionnaire")

# Обработчик команды для начала опроса
@router.message(Command("questionnaire"))
@router.message(Command("begin"))
@router.message(F.text.lower() == "начать опрос")
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
        # Сохраняем ID пользователя в FSM-контексте для последующего использования
        await state.update_data(user_id=user_id)
        
        # Предложить кнопки Да/Нет
        builder = InlineKeyboardBuilder()
        builder.button(text="Да", callback_data="restart_questionnaire")
        builder.button(text="Нет", callback_data="cancel_questionnaire")
        await message.answer("Выберите действие:", reply_markup=builder.as_markup())
        return
    
    # Сохраняем ID пользователя в FSM-контексте
    await state.update_data(user_id=user_id)
    
    # Очищаем предыдущие ответы на случай, если опрос не был завершен в прошлый раз
    db.delete_answers_by_user_id(user_id)
    
    # Сбрасываем индексы вопросов
    await state.update_data(current_demo_question_index=0, current_strength_question_index=0)
    
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
@router.callback_query(F.data == "restart_questionnaire")
async def restart_questionnaire(callback: CallbackQuery, state: FSMContext):
    """Обработчик перезапуска опроса."""
    user = db.get_user_by_tg_id(callback.from_user.id)
    user_id = user["id"]
    await state.update_data(user_id=user_id)
    
    # Очищаем предыдущие ответы пользователя
    db.delete_answers_by_user_id(user_id)
    
    # Сбрасываем индексы вопросов
    await state.update_data(current_demo_question_index=0, current_strength_question_index=0)
    
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

@router.callback_query(F.data == "cancel_questionnaire")
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
            # Извлекаем только номер вопроса из его ID (например, "1" из "strength_1")
            question_number = question["id"].split("_")[1]
            callback_data = f"strength_{question_number}_{option}"
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
@router.message(QuestionnaireStates.demo_questions)
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
@router.callback_query(F.data.startswith("strength_"))
async def process_strength_answer(callback: CallbackQuery, state: FSMContext):
    """Обработчик ответов на вопросы о сильных сторонах."""
    # Разбираем callback_data
    parts = callback.data.split("_")
    if len(parts) < 3:
        logger.error(f"Неверный формат callback_data: {callback.data}")
        await callback.answer("Ошибка обработки ответа. Попробуйте еще раз.")
        return
    
    # Формируем правильный идентификатор вопроса: strength_номер
    question_id = f"strength_{parts[1]}"
    answer = parts[2]
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    if "user_id" not in user_data:
        logger.error(f"Нет user_id в состоянии для пользователя {callback.from_user.id}")
        # Получаем пользователя из БД по Telegram ID
        user = db.get_user_by_tg_id(callback.from_user.id)
        if not user:
            # Создаем пользователя если его нет
            user_id = db.add_user(
                callback.from_user.id,
                f"{callback.from_user.first_name} {callback.from_user.last_name if callback.from_user.last_name else ''}"
            )
            logger.info(f"Создан новый пользователь {callback.from_user.id} (db_id: {user_id})")
        else:
            user_id = user["id"]
        # Обновляем состояние
        await state.update_data(user_id=user_id)
    else:
        user_id = user_data["user_id"]
    
    # Сохраняем ответ
    db.add_answer(user_id, question_id, answer)
    logger.info(f"Сохранен ответ на вопрос о сильных сторонах {question_id}: {answer}")
    
    # Отвечаем на callback
    await callback.answer("Ответ принят")
    
    # Переходим к следующему вопросу
    await ask_next_strength_question(callback.message, state)

# Обработка результатов опроса
async def process_questionnaire_results(message: Message, state: FSMContext):
    """Функция обработки результатов опроса."""
    # Получаем данные из состояния
    user_data = await state.get_data()
    user_id = user_data["user_id"]
    
    # Получаем все ответы пользователя
    answers = db.get_answers_by_user_id(user_id)
    
    # Сообщаем пользователю о начале обработки
    await message.answer("Анализирую твои ответы... Это может занять несколько секунд.")
    
    # Вызываем функцию построения профиля
    profile_data = await build_profile(user_id, answers)
    
    summary_data = profile_data["summary_data"]
    natal_data = profile_data["natal_data"]
    category_names = profile_data["category_names"]
    
    # Сохраняем профиль
    profile_id = db.add_profile(user_id, summary_data, natal_data)
    
    # Отправляем результаты пользователю
    result_message = f"Спасибо за прохождение опроса!\n\n"
    result_message += f"Твои топ-3 сильные стороны:\n"
    
    for i, strength in enumerate(summary_data["strengths"], 1):
        result_message += f"{i}. {strength}\n"
    
    result_message += "\nТвои оценки по категориям:\n"
    
    for category, score in summary_data["scores"].items():
        result_message += f"- {category_names.get(category, category)}: {score}/5\n"
    
    # Отправляем базовую информацию
    await message.answer(result_message)
    
    # Проверяем наличие AI-анализа
    if summary_data.get("ai_analysis"):
        ai_analysis = summary_data["ai_analysis"]
        
        # Отправляем психологический профиль
        ai_message = "🧠 Психологический анализ твоего профиля:\n\n"
        
        if ai_analysis.get("summary"):
            ai_message += f"{ai_analysis['summary']}\n\n"
        
        if ai_analysis.get("strengths") and len(ai_analysis["strengths"]) > 0:
            ai_message += "Твои ключевые сильные стороны:\n"
            for i, strength in enumerate(ai_analysis["strengths"], 1):
                ai_message += f"{i}. {strength}\n"
            ai_message += "\n"
        
        if ai_analysis.get("growth_areas") and len(ai_analysis["growth_areas"]) > 0:
            ai_message += "Направления для развития:\n"
            for i, area in enumerate(ai_analysis["growth_areas"], 1):
                ai_message += f"{i}. {area}\n"
            ai_message += "\n"
        
        await message.answer(ai_message)
    
    # Отправляем информацию о натальной карте
    if natal_data and not natal_data.get("error"):
        astro_message = "🌟 Данные натальной карты:\n\n"
        astro_message += f"Дата рождения: {summary_data.get('birthdate')}\n"
        astro_message += f"Место рождения: {summary_data.get('birthplace')}\n\n"
        
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
        
        for planet, position in natal_data.items():
            if planet.endswith("_long") and planet.split("_")[0] in planet_names:
                planet_name = planet_names[planet.split("_")[0]]
                astro_message += f"{planet_name}: {position:.2f}°\n"
        
        await message.answer(astro_message)
    
    # Заключительное сообщение
    await message.answer("Теперь у тебя есть профиль, который ты можешь просмотреть командой /profile.")
    
    # Завершаем опрос
    await state.set_state(QuestionnaireStates.completed)
    
    logger.info(f"Опрос завершен для пользователя {user_id}, создан профиль {profile_id}")

# Построение профиля пользователя на основе ответов
async def build_profile(user_id: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Функция построения профиля пользователя на основе ответов.
    
    Args:
        user_id: ID пользователя.
        answers: Список ответов пользователя.
        
    Returns:
        Dict: Данные профиля.
    """
    # Получаем демо-информацию
    name = None
    age = None
    birthdate = None
    birthplace = None
    timezone = None
    
    for answer in answers:
        if answer["question_id"] == "name":
            name = answer["answer_text"]
        elif answer["question_id"] == "age":
            age = answer["answer_text"]
        elif answer["question_id"] == "birthdate":
            birthdate = answer["answer_text"]
        elif answer["question_id"] == "birthplace":
            birthplace = answer["answer_text"]
        elif answer["question_id"] == "timezone":
            timezone = answer["answer_text"]
    
    # Анализ ответов на вопросы о сильных сторонах
    # Считаем средний балл по каждой категории сильных сторон
    strength_scores = {}
    strength_categories = {
        "analytical": [],
        "creative": [],
        "leadership": [],
        "social": [],
        "organized": [],
        "resilient": []
    }
    
    # Заполняем категории на основе вопросов
    strength_questions = get_strength_questions()
    for question in strength_questions:
        question_id = question["id"]
        category = question.get("category")
        if category and category in strength_categories:
            strength_categories[category].append(question_id)
    
    # Инициализация счетчиков для каждой категории
    for category in strength_categories:
        strength_scores[category] = {"total": 0, "count": 0}
    
    # Подсчет баллов
    for answer in answers:
        for category, questions in strength_categories.items():
            if answer["question_id"] in questions and answer["answer_text"].isdigit():
                strength_scores[category]["total"] += int(answer["answer_text"])
                strength_scores[category]["count"] += 1
    
    # Расчет средних значений
    final_scores = {}
    for category, data in strength_scores.items():
        if data["count"] > 0:
            # Вычисляем среднее значение баллов
            avg_score = data["total"] / data["count"]
            # Округляем до одного знака после запятой
            final_scores[category] = round(avg_score, 1)
        else:
            final_scores[category] = 0
    
    # Определение топ-3 сильных сторон
    top_strengths = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_strengths_names = []
    
    # Преобразование кодов категорий в удобочитаемые названия
    category_names = {
        "analytical": "Аналитик",
        "creative": "Творческий мыслитель",
        "leadership": "Лидер",
        "social": "Коммуникатор",
        "organized": "Организатор",
        "resilient": "Стойкий"
    }
    
    for category, score in top_strengths:
        top_strengths_names.append(category_names.get(category, category))
    
    # Создаем данные профиля
    summary_data = {
        "name": name,
        "age": age,
        "birthdate": birthdate,
        "birthplace": birthplace,
        "timezone": timezone,
        "strengths": top_strengths_names,
        "scores": final_scores
    }
    
    # Рассчитываем натальную карту
    natal_data = None
    try:
        # Преобразуем формат даты из DD.MM.YYYY в YYYY-MM-DD
        if birthdate:
            date_parts = birthdate.split('.')
            if len(date_parts) == 3:
                date_str = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]} 12:00"  # Используем полдень как время по умолчанию
                # Вызываем функцию расчета натальной карты
                natal_data = make_natal_chart(date_str, birthplace or "Москва")
                
                # Обновляем профиль пользователя с данными натальной карты
                db.update_profile_natal(user_id, natal_data)
                logger.info(f"Создана натальная карта для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при расчете натальной карты: {e}")
        natal_data = {"error": str(e)}
    
    # Генерируем психологический профиль с помощью OpenAI
    try:
        # Подготавливаем данные для анализа
        profile_for_ai = {
            "personal_info": {
                "name": name,
                "age": age
            },
            "strengths": top_strengths_names,
            "scores": final_scores,
            "answers": {answer["question_id"]: answer["answer_text"] for answer in answers}
        }
        
        # Вызываем API OpenAI для анализа
        ai_analysis = await generate_profile(profile_for_ai)
        
        # Добавляем результаты анализа в данные профиля
        summary_data["ai_analysis"] = ai_analysis
        
        # Обновляем профиль в базе данных
        db.update_profile_summary(user_id, summary_data)
        logger.info(f"Создан психологический профиль для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при генерации психологического профиля: {e}")
        summary_data["ai_analysis"] = {
            "summary": "Не удалось сгенерировать психологический профиль из-за технической ошибки.",
            "strengths": [],
            "growth_areas": []
        }
    
    # Возвращаем данные профиля
    return {
        "summary_data": summary_data,
        "natal_data": natal_data,
        "category_names": category_names
    }

# Обработчик прерывания опроса
@router.message(Command("cancel"))
async def cancel_questionnaire(message: Message, state: FSMContext):
    """Обработчик прерывания опроса."""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нет активного опроса для отмены.")
        return
    
    # Сбрасываем состояние
    await state.clear()
    await message.answer("Опрос прерван. Вы можете начать его заново в любое время командой /questionnaire.")
    
    logger.info(f"Пользователь {message.from_user.id} прервал опрос") 