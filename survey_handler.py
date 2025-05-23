import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from button_states import SurveyStates, ProfileStates
from profile_generator import generate_profile, save_profile_to_db

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для опроса
survey_router = Router()

# Функция для получения основной клавиатуры
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает основную клавиатуру приложения.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с основными функциями
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📝 Опрос")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
            [KeyboardButton(text="🔄 Рестарт")]
        ],
        resize_keyboard=True
    )

async def start_survey(message: Message, state: FSMContext):
    """
    Начинает опрос пользователя.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    
    # Проверяем, есть ли у пользователя уже заполненный профиль
    has_profile = user_data.get("profile_completed", False)
    
    if has_profile:
        # Если у пользователя уже есть профиль, спрашиваем подтверждение на перезапись
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Да, начать заново", callback_data="confirm_survey")
        builder.button(text="❌ Нет, отмена", callback_data="cancel_survey")
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
    
    # Если профиля нет, начинаем опрос сразу
    # Импортируем функцию для получения демо-вопросов
    from questions import get_demo_questions
    
    # Получаем список демо-вопросов
    demo_questions = get_demo_questions()
    
    # Показываем первый вопрос
    await message.answer(
        "📋 <b>Начинаем опрос!</b>\n\n"
        "Я задам несколько вопросов, чтобы лучше узнать тебя. "
        "Сначала ответь на несколько базовых вопросов, а затем мы перейдем к "
        "специальному тесту для определения твоих сильных сторон.",
        parse_mode="HTML"
    )
    
    # Показываем первый вопрос
    await message.answer(
        f"Вопрос 1: {demo_questions[0]['text']}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Введите ваш ответ..."
        )
    )
    
    # Инициализируем опрос
    await state.set_state(SurveyStates.answering_questions)
    await state.update_data(
        question_index=0,
        question_type="demo",
        answers={},
        is_demo_questions=True
    )
    
    logger.info(f"Пользователь {message.from_user.id} начал опрос")

# Обработчик для подтверждения перезапуска опроса
@survey_router.callback_query(F.data == "confirm_survey")
async def confirm_restart_survey(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждает перезапуск опроса.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Очищаем текущие данные профиля
    await state.update_data(
        answers={},
        profile_completed=False,
        profile_text="",
        personality_type=None
    )
    
    # Начинаем опрос заново
    await start_survey(callback.message, state)
    
    # Отвечаем на callback
    await callback.answer("Начинаем опрос заново")

# Обработчик для отмены перезапуска опроса
@survey_router.callback_query(F.data == "cancel_survey")
async def cancel_restart_survey(callback: CallbackQuery):
    """
    Отменяет перезапуск опроса.
    
    Args:
        callback: Callback query
    """
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Отправляем сообщение об отмене
    await callback.message.answer(
        "✅ Опрос отменен. Ваш текущий профиль сохранен.",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Опрос отменен")

# Обработчик ответов на вопросы опроса
@survey_router.message(SurveyStates.answering_questions)
async def process_survey_answer(message: Message, state: FSMContext):
    """
    Обрабатывает ответы на вопросы опроса.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Если пользователь хочет отменить опрос
    if message.text == "❌ Отменить опрос":
        await state.clear()
        await message.answer(
            "❌ Опрос отменен. Вы можете начать его заново в любое время.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем текущее состояние опроса
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    answers = data.get("answers", {})
    is_demo_questions = data.get("is_demo_questions", True)
    
    # Импортируем функции для получения вопросов
    from questions import get_demo_questions, get_all_vasini_questions
    
    # Получаем списки вопросов
    demo_questions = get_demo_questions()
    vasini_questions = get_all_vasini_questions()
    
    # Определяем текущий вопрос
    if is_demo_questions:
        current_question = demo_questions[question_index]
        # Сохраняем ответ на демо-вопрос
        question_id = current_question["id"]
        answers[question_id] = message.text
        
        # Переходим к следующему вопросу
        question_index += 1
        
        # Если демо-вопросы закончились, переходим к вопросам Vasini
        if question_index >= len(demo_questions):
            is_demo_questions = False
            question_index = 0
            
            # Показываем информацию о начале теста Vasini
            await message.answer(
                "🧠 <b>Основная информация собрана!</b>\n\n"
                "Теперь я задам вам 34 вопроса для определения ваших сильных сторон и талантов. "
                "Этот тест называется Vasini Strengths Constellation и помогает выявить ваши природные способности.\n\n"
                "На каждый вопрос нужно выбрать один из вариантов ответа (A, B, C или D).\n\n"
                "Готовы начать?",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="✅ Да, готов(а)")],
                        [KeyboardButton(text="❌ Отменить опрос")]
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            
            # Обновляем состояние
            await state.update_data(
                question_index=question_index,
                answers=answers,
                is_demo_questions=is_demo_questions,
                waiting_for_vasini_confirmation=True
            )
            return
    else:
        # Проверяем, ожидаем ли мы подтверждения для начала теста Vasini
        if data.get("waiting_for_vasini_confirmation", False):
            if message.text == "✅ Да, готов(а)":
                # Начинаем тест Vasini
                current_question = vasini_questions[question_index]
                
                # Создаем клавиатуру с вариантами ответов
                options = current_question["options"]
                keyboard = []
                for option, text in options.items():
                    keyboard.append([KeyboardButton(text=f"{option}: {text}")])
                keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
                
                await message.answer(
                    f"Вопрос {question_index + 1}/34: {current_question['text']}",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=keyboard,
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
                
                # Обновляем состояние
                await state.update_data(
                    waiting_for_vasini_confirmation=False
                )
                return
            elif message.text == "❌ Отменить опрос":
                await state.clear()
                await message.answer(
                    "❌ Опрос отменен. Вы можете начать его заново в любое время.",
                    reply_markup=get_main_keyboard()
                )
                return
            else:
                # Повторяем вопрос о готовности
                await message.answer(
                    "Пожалуйста, выберите один из вариантов:",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text="✅ Да, готов(а)")],
                            [KeyboardButton(text="❌ Отменить опрос")]
                        ],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
                return
        
        # Обрабатываем ответ на вопрос Vasini
        current_question = vasini_questions[question_index]
        
        # Проверяем, что ответ содержит букву варианта (A, B, C или D)
        option = None
        for opt in ["A", "B", "C", "D"]:
            if message.text.startswith(f"{opt}:"):
                option = opt
                break
        
        if not option:
            # Если ответ не соответствует формату, просим повторить
            options = current_question["options"]
            keyboard = []
            for opt, text in options.items():
                keyboard.append([KeyboardButton(text=f"{opt}: {text}")])
            keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
            
            await message.answer(
                f"Пожалуйста, выберите один из предложенных вариантов ответа (A, B, C или D).\n\n"
                f"Вопрос {question_index + 1}/34: {current_question['text']}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=keyboard,
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            return
        
        # Сохраняем ответ на вопрос Vasini
        question_id = current_question["id"]
        answers[question_id] = option
        
        # Переходим к следующему вопросу
        question_index += 1
        
        # Если все вопросы Vasini заданы, завершаем опрос
        if question_index >= len(vasini_questions):
            await complete_survey(message, state, answers)
            return
    
    # Показываем следующий вопрос
    if is_demo_questions:
        next_question = demo_questions[question_index]
        await message.answer(
            f"Вопрос {question_index + 1}/{len(demo_questions)}: {next_question['text']}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
                resize_keyboard=True,
                one_time_keyboard=False,
                input_field_placeholder="Введите ваш ответ..."
            )
        )
    else:
        next_question = vasini_questions[question_index]
        
        # Создаем клавиатуру с вариантами ответов
        options = next_question["options"]
        keyboard = []
        for option, text in options.items():
            keyboard.append([KeyboardButton(text=f"{option}: {text}")])
        keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
        
        await message.answer(
            f"Вопрос {question_index + 1}/34: {next_question['text']}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    
    # Обновляем состояние
    await state.update_data(
        question_index=question_index,
        answers=answers,
        is_demo_questions=is_demo_questions
    )

async def complete_survey(message: Message, state: FSMContext, answers: Dict[str, str]):
    """
    Завершает опрос и генерирует профиль.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
        answers: Ответы пользователя
    """
    # Сообщаем о завершении опроса
    await message.answer(
        "🎉 <b>Поздравляю! Вы завершили опрос!</b>\n\n"
        "Теперь я анализирую ваши ответы и создаю персональный психологический профиль.\n"
        "Это может занять несколько секунд...",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    
    try:
        # Импортируем функции для определения типа личности
        from questions import get_personality_type_from_answers
        
        # Определяем тип личности
        type_counts, primary_type, secondary_type = get_personality_type_from_answers(answers)
        
        # Генерируем профиль
        profile_text = await generate_profile(answers)
        
        # Сохраняем профиль в базу данных
        await save_profile_to_db(message.from_user.id, profile_text, answers)
        
        # Обновляем состояние
        await state.update_data(
            profile_completed=True,
            profile_text=profile_text,
            answers=answers,
            personality_type=primary_type
        )
        
        # Переключаем состояние на просмотр профиля
        await state.set_state(ProfileStates.viewing)
        
        # Отображаем профиль пользователю
        await message.answer(
            profile_text,
            parse_mode="HTML"
        )
        
        # Предлагаем дальнейшие действия
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Подробная статистика", callback_data="show_stats")
        builder.button(text="💡 Получить совет", callback_data="get_advice")
        builder.adjust(1)
        
        await message.answer(
            "🧠 <b>Что дальше?</b>\n\n"
            "Теперь я буду общаться с вами с учетом вашего психологического профиля.\n"
            "Вы можете задавать мне вопросы, просить совета или просто поговорить на интересующие вас темы.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        logger.info(f"Пользователь {message.from_user.id} успешно завершил опрос и получил профиль")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации профиля: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при создании профиля.</b>\n\n"
            "Пожалуйста, попробуйте пройти опрос еще раз или обратитесь в поддержку.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

# Обработчик для перезапуска опроса
@survey_router.callback_query(F.data == "restart_survey")
async def restart_survey(callback: CallbackQuery, state: FSMContext):
    """
    Перезапускает опрос, удаляя предыдущий профиль пользователя.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Спрашиваем подтверждение перед сбросом данных
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сбросить профиль", callback_data="confirm_profile_reset")
    builder.button(text="❌ Нет, отмена", callback_data="cancel_profile_reset")
    builder.adjust(1)
    
    await callback.message.answer(
        "⚠️ <b>Внимание!</b>\n\n"
        "Вы собираетесь сбросить ваш текущий профиль и пройти опрос заново. "
        "Все ваши предыдущие ответы будут удалены.\n\n"
        "Вы уверены, что хотите продолжить?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Отвечаем на callback
    await callback.answer("Подтвердите сброс профиля")

@survey_router.callback_query(F.data == "confirm_profile_reset")
async def confirm_profile_reset(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждает сброс профиля и перезапускает опрос.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Очищаем текущие данные профиля
    await state.update_data(
        answers={},
        profile_completed=False,
        profile_text="",
        personality_type=None,
        waiting_for_vasini_confirmation=False,
        question_index=0,
        is_demo_questions=True
    )
    
    # Удаляем сообщение с подтверждением
    await callback.message.delete()
    
    # Сообщаем об успешном сбросе
    await callback.message.answer(
        "✅ <b>Профиль успешно сброшен!</b>\n\n"
        "Сейчас мы начнем опрос заново.",
        parse_mode="HTML"
    )
    
    # Небольшая задержка перед началом нового опроса
    import asyncio
    await asyncio.sleep(1)
    
    # Начинаем опрос заново
    await start_survey(callback.message, state)
    
    # Отвечаем на callback
    await callback.answer("Профиль сброшен, начинаем опрос заново")
    logger.info(f"Пользователь {callback.from_user.id} сбросил профиль и начал опрос заново")

@survey_router.callback_query(F.data == "cancel_profile_reset")
async def cancel_profile_reset(callback: CallbackQuery):
    """
    Отменяет сброс профиля.
    
    Args:
        callback: Callback query
    """
    # Удаляем сообщение с подтверждением
    await callback.message.delete()
    
    # Сообщаем об отмене
    await callback.message.answer(
        "✅ Действие отменено. Ваш текущий профиль сохранен.",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Отмена сброса профиля")
    logger.info(f"Пользователь {callback.from_user.id} отменил сброс профиля")

# Обработчик для отображения подробной статистики
@survey_router.callback_query(F.data == "show_stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    """
    Отображает подробную статистику по ответам.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    answers = user_data.get("answers", {})
    
    if not answers:
        await callback.message.answer(
            "❌ <b>Ошибка:</b> Данные профиля не найдены. Пожалуйста, пройдите опрос.",
            parse_mode="HTML"
        )
        await callback.answer("Данные профиля не найдены")
        return
    
    # Импортируем функцию для анализа ответов
    from questions import get_personality_type_from_answers
    
    # Получаем статистику по типам ответов
    type_counts, primary_type, secondary_type = get_personality_type_from_answers(answers)
    
    # Формируем красивый текст статистики
    stats_text = "📊 <b>ПСИХОЛОГИЧЕСКИЙ ПРОФИЛЬ - ПОДРОБНАЯ СТАТИСТИКА</b>\n\n"
    
    # Добавляем информацию о типе личности
    stats_text += f"<b>🧠 Ваш тип личности:</b> {primary_type}"
    if secondary_type:
        stats_text += f" <i>(с элементами {secondary_type})</i>"
    stats_text += "\n\n"
    
    # Подсчитываем количество вопросов по типам
    vasini_questions_count = sum(1 for key in answers if key.startswith('vasini_'))
    demo_questions_count = sum(1 for key in answers if not key.startswith('vasini_'))
    
    # Добавляем базовую информацию о результатах
    stats_text += "<b>📋 СТАТИСТИКА ОПРОСА:</b>\n"
    stats_text += f"• Всего вопросов: {len(answers)}\n"
    stats_text += f"• Вопросов профиля: {demo_questions_count}\n"
    stats_text += f"• Вопросов психологического теста: {vasini_questions_count}\n\n"
    
    # Добавляем распределение ответов с визуальными элементами
    stats_text += "<b>📈 РАСПРЕДЕЛЕНИЕ ОТВЕТОВ:</b>\n"
    
    # Визуализация распределения ответов
    total_answers = sum(type_counts.values())
    
    # Типы личности и их эмодзи
    type_emoji = {
        "A": "🧠", # Интеллектуальный
        "B": "❤️", # Эмоциональный
        "C": "⚙️", # Практический
        "D": "✨"  # Творческий
    }
    
    type_labels = {
        "A": "Интеллектуальный",
        "B": "Эмоциональный",
        "C": "Практический",
        "D": "Творческий"
    }
    
    # Создаем визуальный график распределения
    for type_key in ["A", "B", "C", "D"]:
        count = type_counts[type_key]
        percentage = round((count / total_answers) * 100) if total_answers > 0 else 0
        
        # Создаем график в виде символов
        bar = ""
        bar_length = min(10, percentage // 10) if percentage > 0 else 0
        bar = "▮" * bar_length + "▯" * (10 - bar_length)
        
        stats_text += f"{type_emoji[type_key]} <b>{type_labels[type_key]}:</b> {count} ({percentage}%)\n"
        stats_text += f"  {bar} \n"
    
    stats_text += "\n<b>👤 ЛИЧНАЯ ИНФОРМАЦИЯ:</b>\n"
    if "name" in answers:
        stats_text += f"• Имя: {answers['name']}\n"
    if "age" in answers:
        stats_text += f"• Возраст: {answers['age']}\n"
    if "birthdate" in answers:
        stats_text += f"• Дата рождения: {answers['birthdate']}\n"
    if "birthplace" in answers:
        stats_text += f"• Место рождения: {answers['birthplace']}\n"
    if "timezone" in answers:
        stats_text += f"• Часовой пояс: {answers['timezone']}\n"
    
    # Добавляем интерпретацию (краткую) на основе доминирующего типа
    stats_text += "\n<b>💡 ИНТЕРПРЕТАЦИЯ:</b>\n"
    
    interpretations = {
        "Интеллектуальный": "Вы склонны к аналитическому мышлению, рационализму и структурированному подходу к задачам. Вам важно глубокое понимание процессов.",
        "Эмоциональный": "Вы обладаете развитой эмпатией, эмоциональным интеллектом и чуткостью к людям. Для вас важны гармоничные отношения и внутренний баланс.",
        "Практический": "Вы ориентированы на результат, организованны и эффективны. Для вас важно достижение конкретных целей и практическая применимость.",
        "Творческий": "Вы обладаете богатым воображением, креативным подходом и нестандартным мышлением. Для вас важна свобода самовыражения."
    }
    
    stats_text += interpretations.get(primary_type, "")
    
    # Отправляем статистику
    await callback.message.answer(
        stats_text,
        parse_mode="HTML"
    )
    
    # Предлагаем пользователю действия после просмотра статистики
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Пройти опрос заново", callback_data="restart_survey")
    builder.button(text="💡 Получить совет", callback_data="get_advice")
    builder.button(text="◀️ Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        "Что вы хотите сделать дальше?",
        reply_markup=builder.as_markup()
    )
    
    # Отвечаем на callback
    await callback.answer("Статистика загружена")

# Регистрация обработчиков команд
@survey_router.message(Command("survey"))
@survey_router.message(F.text == "📝 Опрос")
async def command_survey(message: Message, state: FSMContext):
    """
    Обработчик команды /survey и кнопки "Опрос".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    await start_survey(message, state)

# Обработчик команды профиля
@survey_router.message(Command("profile"))
@survey_router.message(F.text == "👤 Профиль")
async def command_profile(message: Message, state: FSMContext):
    """
    Обработчик команды /profile и кнопки "Профиль".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_completed = user_data.get("profile_completed", False)
    
    if profile_completed:
        profile_text = user_data.get("profile_text", "")
        
        # Отправляем профиль
        await message.answer(
            f"<b>Ваш психологический профиль:</b>\n\n{profile_text}",
            parse_mode="HTML"
        )
        
        # Добавляем кнопки для действий с профилем
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Пройти опрос заново", callback_data="restart_survey")
        builder.button(text="📊 Подробная статистика", callback_data="show_stats")
        builder.button(text="💡 Получить совет", callback_data="get_advice")
        builder.button(text="◀️ Вернуться в меню", callback_data="main_menu")
        builder.adjust(1)
        
        await message.answer(
            "Что вы хотите сделать с вашим профилем?",
            reply_markup=builder.as_markup()
        )
        
        # Устанавливаем состояние просмотра профиля
        await state.set_state(ProfileStates.viewing)
    else:
        # Предлагаем пройти опрос, если профиля нет
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Начать опрос", callback_data="start_survey")
        
        await message.answer(
            "У вас пока нет психологического профиля. Чтобы создать его, нужно пройти опрос.",
            reply_markup=builder.as_markup()
        )

# Добавляем обработчик отмены опроса
@survey_router.message(Command("cancel"))
@survey_router.message(F.text == "❌ Отменить")
async def cancel_survey_command(message: Message, state: FSMContext):
    """
    Отменяет текущий опрос.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    current_state = await state.get_state()
    
    if current_state == SurveyStates.answering_questions:
        await state.clear()
        await message.answer(
            "❌ Опрос отменен. Вы можете начать его заново в любое время.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❓ Сейчас нет активного опроса для отмены."
        )

# Обработчик кнопки возврата в главное меню
@survey_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Возвращает пользователя в главное меню.
    
    Args:
        callback: Callback query
    """
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Отправляем сообщение с основной клавиатурой
    await callback.message.answer(
        "Вы вернулись в главное меню. Выберите нужную опцию:",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Возврат в главное меню")
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")

# Обработчик команды советов
@survey_router.message(Command("advice"))
@survey_router.message(F.text == "💡 Советы")
async def command_advice(message: Message, state: FSMContext):
    """
    Обработчик команды /advice и кнопки "Советы".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_completed = user_data.get("profile_completed", False)
    
    if profile_completed:
        # Если профиль есть, получаем тип личности
        personality_type = user_data.get("personality_type", "Интеллектуальный")
        
        # Получаем персонализированный совет на основе типа личности
        advice = get_personalized_advice(personality_type)
        
        # Отправляем совет
        await message.answer(
            f"💡 <b>Персонализированный совет</b>\n\n{advice}",
            parse_mode="HTML"
        )
        
        # Добавляем кнопки для дополнительных действий
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Получить другой совет", callback_data="get_advice")
        builder.button(text="👤 Посмотреть профиль", callback_data="view_profile")
        builder.button(text="◀️ Главное меню", callback_data="main_menu")
        builder.adjust(1)
        
        await message.answer(
            "Что вы хотите сделать дальше?",
            reply_markup=builder.as_markup()
        )
    else:
        # Если профиля нет, предлагаем пройти опрос
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Начать опрос", callback_data="start_survey")
        
        await message.answer(
            "Чтобы получать персонализированные советы, необходимо сначала пройти психологический тест и создать ваш профиль.",
            reply_markup=builder.as_markup()
        )

# Обработчик для callback "get_advice"
@survey_router.callback_query(F.data == "get_advice")
async def get_advice_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для получения совета через callback.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    personality_type = user_data.get("personality_type", "Интеллектуальный")
    
    # Получаем персонализированный совет
    advice = get_personalized_advice(personality_type)
    
    # Отправляем совет
    await callback.message.answer(
        f"💡 <b>Персонализированный совет</b>\n\n{advice}",
        parse_mode="HTML"
    )
    
    # Добавляем кнопки для дополнительных действий
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Получить другой совет", callback_data="get_advice")
    builder.button(text="👤 Посмотреть профиль", callback_data="view_profile")
    builder.button(text="◀️ Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        "Что вы хотите сделать дальше?",
        reply_markup=builder.as_markup()
    )
    
    # Отвечаем на callback
    await callback.answer("Совет получен")

# Обработчик для callback "view_profile"
@survey_router.callback_query(F.data == "view_profile")
async def view_profile_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для просмотра профиля через callback.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_text = user_data.get("profile_text", "")
    
    if profile_text:
        # Отправляем профиль
        await callback.message.answer(
            f"<b>Ваш психологический профиль:</b>\n\n{profile_text}",
            parse_mode="HTML"
        )
        
        # Добавляем кнопки для действий с профилем
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Пройти опрос заново", callback_data="restart_survey")
        builder.button(text="📊 Подробная статистика", callback_data="show_stats")
        builder.button(text="◀️ Главное меню", callback_data="main_menu")
        builder.adjust(1)
        
        await callback.message.answer(
            "Что вы хотите сделать дальше?",
            reply_markup=builder.as_markup()
        )
        
        # Устанавливаем состояние просмотра профиля
        await state.set_state(ProfileStates.viewing)
    else:
        # Если профиль не найден
        await callback.message.answer(
            "Профиль не найден. Возможно, вам нужно пройти опрос заново.",
            reply_markup=get_main_keyboard()
        )
    
    # Отвечаем на callback
    await callback.answer("Просмотр профиля")

# Функция для генерации персонализированных советов
def get_personalized_advice(personality_type: str) -> str:
    """
    Генерирует персонализированный совет на основе типа личности.
    
    Args:
        personality_type: Тип личности пользователя
        
    Returns:
        str: Персонализированный совет
    """
    # Словарь с советами для разных типов личности
    advice_by_type = {
        "Интеллектуальный": [
            "🧠 Запланируйте 15-20 минут в день для чтения материалов по интересующей вас теме. Это поможет удовлетворить вашу потребность в интеллектуальном развитии.",
            "🧩 Попробуйте метод «пяти почему» при анализе проблемы — задавайте вопрос «почему» пять раз подряд, чтобы докопаться до первопричины.",
            "📝 Выделите 10 минут перед сном для рефлексии дня. Запишите три вещи, которые вы узнали сегодня, и как это можно применить.",
            "🔄 При решении сложных задач попробуйте технику mind mapping (ментальные карты). Она позволит вам увидеть связи между различными элементами проблемы.",
            "⏸️ Чтобы избежать информационной перегрузки, практикуйте метод «информационного поста» — один день в неделю минимизируйте потребление новостей и соцсетей.",
            "🎯 Для улучшения фокусировки используйте технику «глубокой работы» — выделяйте 90 минут на работу без отвлечений, без проверки почты и сообщений.",
            "📚 Развивайте межпредметные связи: изучайте, как ваша область знаний пересекается с другими дисциплинами. Это стимулирует нестандартное мышление.",
            "🤔 Практикуйте сократовский метод диалога: задавайте вопросы, которые помогают собеседнику самостоятельно прийти к выводам.",
            "🔍 Постарайтесь в течение недели фиксировать моменты, когда вы чувствуете наибольший интеллектуальный подъем. Это поможет определить ваш оптимальный режим работы.",
            "📖 Сформируйте привычку регулярно проверять свои знания: после прочтения книги или статьи запишите 3-5 ключевых идей и как их можно применить."
        ],
        "Эмоциональный": [
            "📓 Практикуйте «эмоциональный дневник»: записывайте свои эмоции в течение дня и их триггеры. Это помогает лучше понимать свои чувства и реакции.",
            "🧘 Используйте технику «дыхание 4-7-8»: вдох на 4 счета, задержка на 7, выдох на 8. Это эффективно снижает тревожность и помогает восстановить эмоциональный баланс.",
            "🙏 Выделите 5 минут в день для практики благодарности: запишите три вещи, за которые вы благодарны. Это повышает общий эмоциональный фон.",
            "🌱 Если вы чувствуете сильные эмоции, попробуйте технику «физическое заземление»: назовите 5 вещей, которые вы видите, 4 вещи, которые можно потрогать, 3 звука, 2 запаха и 1 вкус.",
            "👂 Практикуйте активное слушание в разговорах: перефразируйте слова собеседника, чтобы убедиться, что вы правильно поняли. Это углубляет эмоциональную связь.",
            "❤️ Создайте ритуал самозаботы: выделите 15-20 минут в день только для себя, для деятельности, которая приносит вам удовольствие и спокойствие.",
            "💌 Напишите письмо благодарности человеку, который оказал на вас положительное влияние, но которому вы, возможно, не выразили своей признательности в полной мере.",
            "🌈 Создайте «банк позитивных эмоций»: соберите фотографии, сообщения или предметы, которые вызывают у вас положительные эмоции, и обращайтесь к ним в трудные моменты.",
            "🗣️ Практикуйте «честное общение»: выражайте свои потребности и границы вежливо, но четко, используя формулировку «Я чувствую... когда... потому что... и мне нужно...».",
            "🫂 Проводите регулярный «эмоциональный чекин» с близкими людьми: выделите время, чтобы поговорить о чувствах и переживаниях, а не только о повседневных делах."
        ],
        "Практический": [
            "🐸 Используйте технику «ешьте лягушку»: начинайте день с самой сложной и неприятной задачи, и остальной день пройдет более продуктивно.",
            "⏱️ Применяйте правило «двух минут»: если задача требует менее двух минут, сделайте ее сразу, не откладывая — это значительно сократит ваш список дел.",
            "✅ Вечером составляйте список из трех самых важных задач на завтра. Не начинайте другие дела, пока не завершите эти три.",
            "🍅 Используйте технику Помодоро: работайте 25 минут, затем сделайте перерыв 5 минут. После четырех таких циклов сделайте длинный перерыв 15-30 минут.",
            "🧹 Оптимизируйте свое рабочее пространство по принципу «все имеет свое место»: регулярно возвращайте предметы на их места, это снижает когнитивную нагрузку.",
            "📊 Применяйте принцип Парето (80/20): определите, какие 20% ваших действий приносят 80% результатов, и сосредоточьтесь на них.",
            "🚫 Внедрите «тайм-блокировку»: установите определенное время (например, с 10:00 до 12:00), когда вас нельзя беспокоить, и используйте его для глубокой работы.",
            "📋 Создайте систему еженедельного обзора: в конце недели просматривайте все выполненные задачи, оценивайте результаты и планируйте следующую неделю.",
            "🗂️ Используйте метод «контекстных списков»: группируйте задачи по контексту их выполнения (дома, в офисе, по телефону, за компьютером) для более эффективного выполнения.",
            "🚶‍♂️ Практикуйте «прогулки для решения проблем»: многие известные люди (от Стива Джобса до Чарльза Дарвина) практиковали прогулки для более ясного мышления и решения сложных задач."
        ],
        "Творческий": [
            "📝 Практикуйте «утренние страницы»: после пробуждения напишите три страницы текста без цензуры и редактирования. Это стимулирует творческое мышление.",
            "🔄 Используйте технику «случайное слово»: выберите любое слово из словаря и попробуйте связать его с задачей, над которой работаете, чтобы найти новые идеи.",
            "🎨 Уделите 15 минут в день творческому хобби, не связанному с основной работой: рисование, игра на инструменте, лепка. Это развивает творческие нейронные связи.",
            "🧠 Экспериментируйте с «мозговым штурмом наоборот»: вместо поиска решений, сначала перечислите все способы, которыми можно усугубить проблему. Затем поменяйте их на противоположные.",
            "🚶‍♀️ Смените обстановку для повышения креативности: работайте в новом месте, выйдите в парк, посетите музей или галерею. Новые визуальные стимулы способствуют генерации идей.",
            "🌈 Практикуйте синестезию творчества: попробуйте «нарисовать» музыку, «написать» вкус или «сочинить» цвет. Это помогает активировать нестандартные нейронные связи.",
            "🧩 Используйте технику SCAMPER для развития идей: Substitute (замените), Combine (объедините), Adapt (адаптируйте), Modify (измените), Put to another use (используйте по-другому), Eliminate (уберите), Reverse (переверните).",
            "🎭 Примерьте на себя роль другого человека: как бы вашу проблему решил художник? Инженер? Ребенок? Смена перспективы часто приводит к прорывным решениям.",
            "🧠 Практикуйте «невозможные сочетания»: соедините две несовместимые идеи и попытайтесь найти в этом смысл. Например, «квадратное колесо» может натолкнуть на идею гусеничного механизма.",
            "🗂️ Создайте «коллекцию вдохновения»: сохраняйте изображения, цитаты, фрагменты музыки и все, что вызывает у вас творческий отклик, в одном месте. Обращайтесь к ней, когда чувствуете творческий застой."
        ]
    }
    
    # Получаем список советов для данного типа личности
    advice_list = advice_by_type.get(personality_type, advice_by_type["Интеллектуальный"])
    
    # Выбираем случайный совет
    import random
    advice = random.choice(advice_list)
    
    # Логируем выбранный совет
    logger.info(f"Выбран персонализированный совет для типа личности {personality_type}")
    
    # Форматируем совет для лучшего отображения
    formatted_advice = f"{advice}"
    
    return formatted_advice

# Обработчик для callback "start_survey"
@survey_router.callback_query(F.data == "start_survey")
async def start_survey_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для начала опроса через callback.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    await callback.message.delete()
    await start_survey(callback.message, state)
    await callback.answer("Начинаем опрос") 