import asyncio
import logging
from dotenv import load_dotenv
from supabase_db import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_supabase")

# Загрузка переменных окружения
load_dotenv()

async def test_connection():
    """Проверка соединения с Supabase"""
    if db.is_connected:
        logger.info("✅ Подключение к Supabase успешно установлено!")
        
        # Проверяем доступные таблицы
        try:
            response = db.supabase.table('users').select('*').limit(1).execute()
            logger.info("✅ Таблица users доступна")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к таблице users: {e}")
        
        try:
            response = db.supabase.table('profiles').select('*').limit(1).execute()
            logger.info("✅ Таблица profiles доступна")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к таблице profiles: {e}")
        
        try:
            response = db.supabase.table('reminders').select('*').limit(1).execute()
            logger.info("✅ Таблица reminders доступна")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к таблице reminders: {e}")
        
        try:
            response = db.supabase.table('answers').select('*').limit(1).execute()
            logger.info("✅ Таблица answers доступна")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к таблице answers: {e}")
    else:
        logger.error("❌ Ошибка подключения к Supabase. Проверьте переменные окружения SUPABASE_URL и SUPABASE_KEY")

async def test_user_operations():
    """Тестирование операций с пользователями"""
    if not db.is_connected:
        logger.error("❌ Нет подключения к Supabase. Пропускаем тесты операций с пользователями")
        return
    
    logger.info("🔍 Тестирование операций с пользователями...")
    
    # Тестовый идентификатор пользователя
    test_telegram_id = 123456789
    
    try:
        # Создание пользователя
        user = await db.create_user(
            telegram_id=test_telegram_id,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        
        if user:
            logger.info(f"✅ Пользователь успешно создан: {user}")
        else:
            logger.warning("⚠️ Не удалось создать пользователя")
        
        # Получение пользователя
        user = await db.get_user(test_telegram_id)
        
        if user:
            logger.info(f"✅ Пользователь успешно получен: {user}")
        else:
            logger.warning("⚠️ Не удалось получить пользователя")
        
        # Обновление пользователя
        updated_user = await db.create_user(
            telegram_id=test_telegram_id,
            username="updated_user",
            first_name="Updated",
            last_name="User"
        )
        
        if updated_user:
            logger.info(f"✅ Пользователь успешно обновлен: {updated_user}")
        else:
            logger.warning("⚠️ Не удалось обновить пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании операций с пользователями: {e}")

async def test_profile_operations():
    """Тестирование операций с профилями"""
    if not db.is_connected:
        logger.error("❌ Нет подключения к Supabase. Пропускаем тесты операций с профилями")
        return
    
    logger.info("🔍 Тестирование операций с профилями...")
    
    # Тестовый идентификатор пользователя
    test_telegram_id = 123456789
    
    try:
        # Сохранение профиля
        profile_saved = await db.save_profile(
            telegram_id=test_telegram_id,
            profile_text="Тестовый профиль",
            details_text="Детальный тестовый профиль",
            answers={"name": "Test", "age": "25"}
        )
        
        if profile_saved:
            logger.info("✅ Профиль успешно сохранен")
        else:
            logger.warning("⚠️ Не удалось сохранить профиль")
        
        # Получение профиля
        profile = await db.get_profile(test_telegram_id)
        
        if profile:
            logger.info(f"✅ Профиль успешно получен: {profile}")
        else:
            logger.warning("⚠️ Не удалось получить профиль")
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании операций с профилями: {e}")

async def test_reminder_operations():
    """Тестирование операций с напоминаниями"""
    if not db.is_connected:
        logger.error("❌ Нет подключения к Supabase. Пропускаем тесты операций с напоминаниями")
        return
    
    logger.info("🔍 Тестирование операций с напоминаниями...")
    
    # Тестовый идентификатор пользователя
    test_telegram_id = 123456789
    
    try:
        # Сохранение напоминания
        reminder_saved = await db.save_reminder(
            telegram_id=test_telegram_id,
            time="12:00",
            days=["mon", "wed", "fri"],
            active=True
        )
        
        if reminder_saved:
            logger.info("✅ Напоминание успешно сохранено")
        else:
            logger.warning("⚠️ Не удалось сохранить напоминание")
        
        # Получение напоминания
        reminder = await db.get_reminder(test_telegram_id)
        
        if reminder:
            logger.info(f"✅ Напоминание успешно получено: {reminder}")
        else:
            logger.warning("⚠️ Не удалось получить напоминание")
        
        # Получение всех активных напоминаний
        reminders = await db.get_all_active_reminders()
        
        logger.info(f"✅ Получено {len(reminders)} активных напоминаний")
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании операций с напоминаниями: {e}")

async def test_answer_operations():
    """Тестирование операций с ответами"""
    if not db.is_connected:
        logger.error("❌ Нет подключения к Supabase. Пропускаем тесты операций с ответами")
        return
    
    logger.info("🔍 Тестирование операций с ответами...")
    
    # Тестовый идентификатор пользователя
    test_telegram_id = 123456789
    
    try:
        # Сохранение ответа
        answer_saved = await db.save_answer(
            telegram_id=test_telegram_id,
            question_id="test_question",
            answer_text="Тестовый ответ"
        )
        
        if answer_saved:
            logger.info("✅ Ответ успешно сохранен")
        else:
            logger.warning("⚠️ Не удалось сохранить ответ")
        
        # Получение ответов пользователя
        answers = await db.get_user_answers(test_telegram_id)
        
        logger.info(f"✅ Получено {len(answers)} ответов пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании операций с ответами: {e}")

async def main():
    """Основная функция тестирования"""
    logger.info("=== НАЧАЛО ТЕСТИРОВАНИЯ SUPABASE ===")
    
    # Тестирование соединения
    await test_connection()
    
    # Тестирование операций с пользователями
    await test_user_operations()
    
    # Тестирование операций с профилями
    await test_profile_operations()
    
    # Тестирование операций с напоминаниями
    await test_reminder_operations()
    
    # Тестирование операций с ответами
    await test_answer_operations()
    
    logger.info("=== ТЕСТИРОВАНИЕ SUPABASE ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    asyncio.run(main()) 