import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from button_states import ReminderStates
from survey_handler import get_main_keyboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройка логирования
logger = logging.getLogger(__name__)

try:
    from supabase_db import db  # Импортируем Supabase клиент
    logger.info("Успешный импорт модуля supabase_db в reminder_handler")
except ImportError:
    logger.warning("Модуль supabase не найден, используем SQLite-заглушку в reminder_handler")
    try:
        from supabase_fallback import db  # Импортируем заглушку SQLite
        logger.info("Подключена SQLite-заглушка вместо Supabase в reminder_handler")
    except Exception as fallback_error:
        logger.error(f"Ошибка при подключении SQLite-заглушки в reminder_handler: {fallback_error}")

# Создаем роутер для обработки напоминаний
reminder_router = Router()

# Инициализация планировщика задач
scheduler = AsyncIOScheduler()

# Словарь для хранения пользователей с включенными напоминаниями
# {user_id: {"time": "HH:MM", "days": ["mon", "tue", ...], "active": True}}
reminder_users = {}

# Функция для загрузки напоминаний из Supabase при запуске бота
async def load_reminders_from_db(bot: Bot):
    """
    Загружает все активные напоминания из Supabase и добавляет их в планировщик
    
    Args:
        bot: Экземпляр бота для отправки напоминаний
    """
    try:
        if not db.is_connected:
            logger.error("Не удалось загрузить напоминания: нет подключения к Supabase")
            return
        
        # Получаем все активные напоминания
        reminders = await db.get_all_active_reminders()
        
        for reminder in reminders:
            # Получаем данные напоминания
            user_id = reminder.get("telegram_id")
            time_str = reminder.get("time", "20:00")
            days = reminder.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
            
            # Проверяем корректность данных
            if not user_id or not time_str or not days:
                logger.warning(f"Пропускаем некорректное напоминание: {reminder}")
                continue
            
            # Создаем уникальный ID для задачи
            job_id = f"reminder_{user_id}"
            
            # Удаляем существующую задачу, если она есть
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
            
            try:
                # Парсим время
                hour, minute = map(int, time_str.split(":"))
                
                # Дни недели в формате APScheduler
                day_of_week = ",".join(days)
                
                # Добавляем новую задачу в планировщик
                scheduler.add_job(
                    send_reminder,
                    CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week),
                    id=job_id,
                    args=[bot, user_id],
                    replace_existing=True
                )
                
                logger.info(f"Добавлено напоминание для пользователя {user_id} в {time_str} в дни: {day_of_week}")
            except Exception as e:
                logger.error(f"Ошибка при добавлении напоминания для пользователя {user_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке напоминаний из Supabase: {e}")

# Функция для создания клавиатуры напоминаний
def get_reminder_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для управления напоминаниями
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками управления напоминаниями
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки управления напоминаниями
    builder.button(text="✅ Включить напоминания", callback_data="reminder_on")
    builder.button(text="❌ Отключить напоминания", callback_data="reminder_off")
    builder.button(text="⏰ Изменить время", callback_data="reminder_set_time")
    builder.button(text="📅 Настроить дни недели", callback_data="reminder_set_days")
    builder.button(text="ℹ️ Справка по напоминаниям", callback_data="reminder_help")
    builder.button(text="◀️ Назад в меню", callback_data="main_menu")
    
    # Размещаем кнопки в столбик
    builder.adjust(1)
    
    return builder.as_markup()

# Клавиатура для выбора времени напоминания
def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Предустановленные варианты времени
    times = ["08:00", "12:00", "16:00", "20:00", "22:00"]
    
    for time in times:
        builder.button(text=time, callback_data=f"time_{time}")
    
    builder.button(text="◀️ Назад", callback_data="reminder_menu")
    
    # Размещаем кнопки по 3 в строке
    builder.adjust(3, 2, 1)
    
    return builder.as_markup()

# Клавиатура для выбора дней недели
def get_days_selection_keyboard(selected_days=None) -> InlineKeyboardMarkup:
    if selected_days is None:
        selected_days = []
    
    builder = InlineKeyboardBuilder()
    
    # Дни недели
    days = [
        ("Понедельник", "mon"), ("Вторник", "tue"), ("Среда", "wed"),
        ("Четверг", "thu"), ("Пятница", "fri"), ("Суббота", "sat"), ("Воскресенье", "sun")
    ]
    
    # Добавляем каждый день в отдельной строке с четким статусом
    for day_name, day_code in days:
        # Используем более заметные эмодзи для визуального выделения выбранных дней
        status = "✅ Выбрано" if day_code in selected_days else "⬜️ Не выбрано"
        builder.button(
            text=f"{day_name} - {status}",
            callback_data=f"day_{day_code}"
        )
    
    # Добавляем кнопки управления
    builder.button(text="💾 Сохранить настройки", callback_data="days_save")
    builder.button(text="◀️ Назад в меню напоминаний", callback_data="reminder_menu")
    
    # Размещаем кнопки: каждый день в отдельной строке, затем кнопки управления
    builder.adjust(1)
    
    return builder.as_markup()

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

# Обработчики команд
@reminder_router.message(Command("reminders"))
@reminder_router.message(F.text == "⏰ Напоминания")
async def cmd_reminders(message: Message, state: FSMContext):
    """
    Обработчик команды /reminders и кнопки "Напоминания".
    """
    user_id = message.from_user.id
    
    try:
        # Проверяем подключение к Supabase
        if not db.is_connected:
            await message.answer(
                "⚠️ <b>Ошибка подключения к базе данных</b>\n\n"
                "В данный момент невозможно получить информацию о напоминаниях. "
                "Пожалуйста, попробуйте позже.",
                parse_mode="HTML"
            )
            return
        
        # Получаем информацию о текущих напоминаниях для пользователя
        reminder_info = await db.get_reminder(user_id)
        
        if reminder_info and reminder_info.get("active", False):
            time = reminder_info.get("time", "20:00")
            days = reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
            
            # Преобразуем коды дней недели в русские названия
            day_names = {
                "mon": "понедельник", "tue": "вторник", "wed": "среду", 
                "thu": "четверг", "fri": "пятницу", "sat": "субботу", "sun": "воскресенье"
            }
            days_text = ", ".join([day_names[day] for day in days if day in day_names])
            
            status_text = f"✅ <b>Напоминания включены</b>\n\nВы получаете напоминания в {time} в {days_text}."
        else:
            status_text = "❌ <b>Напоминания выключены</b>\n\nВключите напоминания, чтобы не забывать о практиках."
        
        await message.answer(
            "⏰ <b>Управление напоминаниями</b>\n\n"
            f"{status_text}\n\n"
            "Используйте кнопки ниже для настройки напоминаний:",
            reply_markup=get_reminder_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении информации о напоминаниях для пользователя {user_id}: {e}")
        await message.answer(
            "⚠️ <b>Произошла ошибка</b>\n\n"
            "Не удалось получить информацию о напоминаниях. Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )
    
    # Устанавливаем состояние настройки напоминаний
    await state.set_state(ReminderStates.main_menu)

# Обработчики для инлайн-кнопок напоминаний
@reminder_router.callback_query(F.data == "reminder_on")
async def reminder_on(callback: CallbackQuery, state: FSMContext):
    """
    Включает напоминания для пользователя.
    """
    user_id = callback.from_user.id
    
    try:
        # Проверяем подключение к Supabase
        if not db.is_connected:
            await callback.answer("Ошибка подключения к базе данных", show_alert=True)
            return
        
        # Получаем текущие настройки напоминаний
        reminder_info = await db.get_reminder(user_id)
        
        if not reminder_info:
            # Получаем время по умолчанию из переменных окружения
            default_time = os.getenv("DEFAULT_REMINDER_TIME", "20:00")
            default_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            
            # Создаем настройки напоминаний по умолчанию
            await db.save_reminder(
                telegram_id=user_id,
                time=default_time,
                days=default_days,
                active=True
            )
            
            # Используем значения по умолчанию
            hour, minute = map(int, default_time.split(":"))
            days = default_days
        else:
            # Активируем существующие настройки
            time_str = reminder_info.get("time", "20:00")
            days = reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
            
            # Обновляем статус напоминаний в базе данных
            await db.save_reminder(
                telegram_id=user_id,
                time=time_str,
                days=days,
                active=True
            )
            
            # Парсим время
            hour, minute = map(int, time_str.split(":"))
        
        # Создаем уникальный ID для задачи
        job_id = f"reminder_{user_id}"
        
        # Удаляем существующую задачу, если она есть
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        # Дни недели в формате APScheduler
        day_of_week = ",".join(days)
        
        # Добавляем новую задачу в планировщик
        scheduler.add_job(
            send_reminder,
            CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week),
            id=job_id,
            args=[callback.bot, user_id],
            replace_existing=True
        )
        
        # Если планировщик не запущен, запускаем его
        if not scheduler.running:
            scheduler.start()
        
        # Преобразуем коды дней недели в русские названия
        day_names = {
            "mon": "понедельник", "tue": "вторник", "wed": "среду", 
            "thu": "четверг", "fri": "пятницу", "sat": "субботу", "sun": "воскресенье"
        }
        days_text = ", ".join([day_names[day] for day in days if day in day_names])
        
        # Обновляем текст сообщения
        await callback.message.edit_text(
            "⏰ <b>Управление напоминаниями</b>\n\n"
            f"✅ <b>Напоминания включены</b>\n\nВы будете получать напоминания в {hour:02d}:{minute:02d} в {days_text}.\n\n"
            "Используйте кнопки ниже для изменения настроек:",
            reply_markup=get_reminder_keyboard(),
            parse_mode="HTML"
        )
        
        # Отвечаем на callback
        await callback.answer("Напоминания включены!")
        
        logger.info(f"Пользователь {user_id} включил напоминания на {hour:02d}:{minute:02d} в дни: {day_of_week}")
    except Exception as e:
        logger.error(f"Ошибка при включении напоминаний для пользователя {user_id}: {e}")
        await callback.answer("Произошла ошибка при включении напоминаний", show_alert=True)

@reminder_router.callback_query(F.data == "reminder_off")
async def reminder_off(callback: CallbackQuery):
    """
    Отключает напоминания для пользователя.
    """
    user_id = callback.from_user.id
    
    try:
        # Проверяем подключение к Supabase
        if not db.is_connected:
            await callback.answer("Ошибка подключения к базе данных", show_alert=True)
            return
        
        # Получаем текущие настройки напоминаний
        reminder_info = await db.get_reminder(user_id)
        
        if reminder_info:
            # Обновляем статус напоминаний в базе данных
            await db.save_reminder(
                telegram_id=user_id,
                time=reminder_info.get("time", "20:00"),
                days=reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
                active=False
            )
        
        # Удаляем задачу из планировщика
        job_id = f"reminder_{user_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Удалена задача напоминания для пользователя {user_id}")
        
        # Обновляем текст сообщения
        await callback.message.edit_text(
            "⏰ <b>Управление напоминаниями</b>\n\n"
            "❌ <b>Напоминания выключены</b>\n\nВы не будете получать напоминания о практиках.\n\n"
            "Используйте кнопки ниже для изменения настроек:",
            reply_markup=get_reminder_keyboard(),
            parse_mode="HTML"
        )
        
        # Отвечаем на callback
        await callback.answer("Напоминания отключены!")
        
        logger.info(f"Пользователь {user_id} отключил напоминания")
    except Exception as e:
        logger.error(f"Ошибка при отключении напоминаний для пользователя {user_id}: {e}")
        await callback.answer("Произошла ошибка при отключении напоминаний", show_alert=True)

@reminder_router.callback_query(F.data == "reminder_set_time")
async def set_reminder_time(callback: CallbackQuery, state: FSMContext):
    """
    Отображает меню выбора времени напоминания.
    """
    await callback.message.edit_text(
        "⏰ <b>Выберите время для напоминаний</b>\n\n"
        "В какое время вы хотели бы получать напоминания о практиках?",
        reply_markup=get_time_selection_keyboard(),
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние для выбора времени
    await state.set_state(ReminderStates.selecting_time)
    
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} открыл меню выбора времени напоминаний")

@reminder_router.callback_query(F.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор времени для напоминаний.
    """
    user_id = callback.from_user.id
    selected_time = callback.data.split("_")[1]
    
    try:
        # Проверяем подключение к Supabase
        if not db.is_connected:
            await callback.answer("Ошибка подключения к базе данных", show_alert=True)
            return
        
        # Получаем текущие настройки напоминаний
        reminder_info = await db.get_reminder(user_id)
        
        if reminder_info:
            # Обновляем время напоминаний
            await db.save_reminder(
                telegram_id=user_id,
                time=selected_time,
                days=reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
                active=reminder_info.get("active", True)
            )
        else:
            # Создаем новые настройки напоминаний
            await db.save_reminder(
                telegram_id=user_id,
                time=selected_time,
                days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                active=True
            )
        
        # Если напоминания активны, обновляем задачу в планировщике
        if not reminder_info or reminder_info.get("active", False):
            # Создаем уникальный ID для задачи
            job_id = f"reminder_{user_id}"
            
            # Удаляем существующую задачу, если она есть
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
            
            # Парсим время
            hour, minute = map(int, selected_time.split(":"))
            
            # Получаем дни недели
            days = reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]) if reminder_info else ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            
            # Дни недели в формате APScheduler
            day_of_week = ",".join(days)
            
            # Добавляем новую задачу в планировщик
            scheduler.add_job(
                send_reminder,
                CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week),
                id=job_id,
                args=[callback.bot, user_id],
                replace_existing=True
            )
            
            # Если планировщик не запущен, запускаем его
            if not scheduler.running:
                scheduler.start()
        
        # Переходим обратно в меню напоминаний
        await back_to_reminder_menu(callback, state)
        
        # Отвечаем на callback
        await callback.answer(f"Время напоминаний установлено на {selected_time}")
        
        logger.info(f"Пользователь {user_id} установил время напоминаний на {selected_time}")
    except Exception as e:
        logger.error(f"Ошибка при установке времени напоминаний для пользователя {user_id}: {e}")
        await callback.answer("Произошла ошибка при установке времени напоминаний", show_alert=True)

@reminder_router.callback_query(F.data == "reminder_set_days")
async def set_reminder_days(callback: CallbackQuery, state: FSMContext):
    """
    Отображает меню выбора дней недели для напоминаний.
    """
    user_id = callback.from_user.id
    
    # Получаем текущие выбранные дни или устанавливаем все дни по умолчанию
    selected_days = reminder_users.get(user_id, {}).get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
    
    await callback.message.edit_text(
        "📅 <b>Выберите дни недели для напоминаний</b>\n\n"
        "Нажмите на день, чтобы выбрать или отменить его:\n"
        "✅ Выбрано - напоминания будут приходить в этот день\n"
        "⬜️ Не выбрано - напоминания не будут приходить в этот день\n\n"
        "После завершения выбора нажмите кнопку 💾 Сохранить настройки.",
        reply_markup=get_days_selection_keyboard(selected_days),
        parse_mode="HTML"
    )
    
    # Сохраняем текущий выбор в состоянии
    await state.update_data(selected_days=selected_days)
    
    # Устанавливаем состояние для выбора дней
    await state.set_state(ReminderStates.selecting_days)
    
    await callback.answer("Выберите дни для напоминаний")
    logger.info(f"Пользователь {callback.from_user.id} открыл меню выбора дней недели для напоминаний")

@reminder_router.callback_query(F.data.startswith("day_"))
async def process_day_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор дня недели для напоминаний.
    """
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
    
    day_code = callback.data.split("_")[1]
    
    # Добавляем или удаляем день из списка выбранных
    if day_code in selected_days:
        selected_days.remove(day_code)
    else:
        selected_days.append(day_code)
    
    # Обновляем клавиатуру с выбранными днями
    await callback.message.edit_text(
        "📅 <b>Выберите дни недели для напоминаний</b>\n\n"
        "Нажмите на день, чтобы выбрать или отменить его:\n"
        "✅ Выбрано - напоминания будут приходить в этот день\n"
        "⬜️ Не выбрано - напоминания не будут приходить в этот день\n\n"
        "После завершения выбора нажмите кнопку 💾 Сохранить настройки.",
        reply_markup=get_days_selection_keyboard(selected_days),
        parse_mode="HTML"
    )
    
    # Сохраняем обновленный выбор в состоянии
    await state.update_data(selected_days=selected_days)
    
    # Подтверждаем действие пользователя
    day_names = {
        "mon": "Понедельник", "tue": "Вторник", "wed": "Среда", 
        "thu": "Четверг", "fri": "Пятница", "sat": "Суббота", "sun": "Воскресенье"
    }
    status = "добавлен" if day_code in selected_days else "удален"
    await callback.answer(f"{day_names[day_code]} {status}")

@reminder_router.callback_query(F.data == "days_save")
async def save_reminder_days(callback: CallbackQuery, state: FSMContext):
    """
    Сохраняет выбранные дни недели для напоминаний.
    """
    user_id = callback.from_user.id
    
    try:
        # Получаем выбранные дни из состояния
        data = await state.get_data()
        selected_days = data.get("selected_days", [])
        
        # Проверяем подключение к Supabase
        if not db.is_connected:
            await callback.answer("Ошибка подключения к базе данных", show_alert=True)
            return
        
        # Получаем текущие настройки напоминаний
        reminder_info = await db.get_reminder(user_id)
        
        if reminder_info:
            # Обновляем дни напоминаний
            await db.save_reminder(
                telegram_id=user_id,
                time=reminder_info.get("time", "20:00"),
                days=selected_days,
                active=reminder_info.get("active", True)
            )
        else:
            # Создаем новые настройки напоминаний
            await db.save_reminder(
                telegram_id=user_id,
                time="20:00",
                days=selected_days,
                active=True
            )
        
        # Если напоминания активны, обновляем задачу в планировщике
        if not reminder_info or reminder_info.get("active", False):
            # Создаем уникальный ID для задачи
            job_id = f"reminder_{user_id}"
            
            # Удаляем существующую задачу, если она есть
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
            
            # Проверяем, что есть выбранные дни
            if selected_days:
                # Получаем время
                time_str = reminder_info.get("time", "20:00") if reminder_info else "20:00"
                
                # Парсим время
                hour, minute = map(int, time_str.split(":"))
                
                # Дни недели в формате APScheduler
                day_of_week = ",".join(selected_days)
                
                # Добавляем новую задачу в планировщик
                scheduler.add_job(
                    send_reminder,
                    CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week),
                    id=job_id,
                    args=[callback.bot, user_id],
                    replace_existing=True
                )
                
                # Если планировщик не запущен, запускаем его
                if not scheduler.running:
                    scheduler.start()
        
        # Переходим обратно в меню напоминаний
        await back_to_reminder_menu(callback, state)
        
        # Отвечаем на callback
        if selected_days:
            # Преобразуем коды дней недели в русские названия
            day_names = {
                "mon": "понедельник", "tue": "вторник", "wed": "среда", 
                "thu": "четверг", "fri": "пятница", "sat": "суббота", "sun": "воскресенье"
            }
            days_text = ", ".join([day_names[day] for day in selected_days if day in day_names])
            await callback.answer(f"Дни напоминаний сохранены: {days_text}")
        else:
            await callback.answer("Вы не выбрали ни одного дня для напоминаний")
        
        logger.info(f"Пользователь {user_id} сохранил дни напоминаний: {selected_days}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении дней напоминаний для пользователя {user_id}: {e}")
        await callback.answer("Произошла ошибка при сохранении дней напоминаний", show_alert=True)

@reminder_router.callback_query(F.data == "reminder_help")
async def reminder_help(callback: CallbackQuery):
    """
    Отображает справку по напоминаниям.
    """
    await callback.message.edit_text(
        "ℹ️ <b>Справка по напоминаниям:</b>\n\n"
        "Напоминания помогают вам регулярно выполнять психологические практики и не забывать о них "
        "в суете повседневной жизни.\n\n"
        "<b>Как настроить напоминания:</b>\n"
        "• Включите напоминания с помощью кнопки \"Включить напоминания\"\n"
        "• Выберите удобное время в разделе \"Изменить время\"\n"
        "• Выберите дни недели в разделе \"Настроить дни недели\"\n\n"
        "<b>Рекомендации:</b>\n"
        "• Выбирайте время, когда вы обычно не заняты\n"
        "• Старайтесь придерживаться регулярного расписания практик\n"
        "• Выделяйте хотя бы 5-10 минут в день для медитации или другой практики",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запросил справку по напоминаниям")

@reminder_router.callback_query(F.data == "reminder_menu")
async def back_to_reminder_menu(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в меню напоминаний.
    """
    user_id = callback.from_user.id
    
    # Получаем информацию о текущих напоминаниях для пользователя
    reminder_info = reminder_users.get(user_id, None)
    
    if reminder_info and reminder_info.get("active", False):
        time = reminder_info.get("time", "20:00")
        days = reminder_info.get("days", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        
        # Преобразуем коды дней недели в русские названия
        day_names = {
            "mon": "понедельник", "tue": "вторник", "wed": "среду", 
            "thu": "четверг", "fri": "пятницу", "sat": "субботу", "sun": "воскресенье"
        }
        days_text = ", ".join([day_names[day] for day in days])
        
        status_text = f"✅ <b>Напоминания включены</b>\n\nВы получаете напоминания в {time} в {days_text}."
    else:
        status_text = "❌ <b>Напоминания выключены</b>\n\nВключите напоминания, чтобы не забывать о практиках."
    
    await callback.message.edit_text(
        "⏰ <b>Управление напоминаниями</b>\n\n"
        f"{status_text}\n\n"
        "Используйте кнопки ниже для настройки напоминаний:",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние меню напоминаний
    await state.set_state(ReminderStates.main_menu)
    
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} вернулся в меню напоминаний")

@reminder_router.callback_query(F.data == "main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню приложения.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Очищаем состояние
    await state.clear()
    
    # Отправляем сообщение с основной клавиатурой
    await callback.message.answer(
        "✅ Вы вернулись в главное меню. Выберите нужную опцию:",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Возврат в главное меню")
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню из напоминаний") 