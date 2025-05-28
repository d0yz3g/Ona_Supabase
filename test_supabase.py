import os
import logging
import sys
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("supabase_test")

# Загружаем переменные окружения
load_dotenv()

def check_env_variables():
    """Проверяет наличие необходимых переменных окружения."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Отсутствуют обязательные переменные окружения для Supabase.")
        logger.error("   SUPABASE_URL: %s", "✅ Задан" if supabase_url else "❌ Отсутствует")
        logger.error("   SUPABASE_KEY: %s", "✅ Задан" if supabase_key else "❌ Отсутствует")
        logger.error("   Проверьте файл .env и убедитесь, что переменные заданы корректно.")
        return False
    
    logger.info("✅ Переменные окружения для Supabase настроены корректно.")
    return True

def check_supabase_module():
    """Проверяет наличие модуля supabase."""
    try:
        import supabase
        logger.info(f"✅ Модуль supabase установлен (версия: {supabase.__version__})")
        return True
    except ImportError as e:
        logger.error(f"❌ Модуль supabase не установлен: {e}")
        logger.error("   Установите модуль командой: pip install supabase-py")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке модуля supabase: {e}")
        return False

def test_supabase_connection():
    """Тестирует подключение к Supabase."""
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            return False
            
        client = create_client(supabase_url, supabase_key)
        
        # Простой тест - получаем версию PostgreSQL
        response = client.rpc('get_postgres_version').execute()
        
        if hasattr(response, 'data'):
            logger.info(f"✅ Успешное подключение к Supabase! PostgreSQL версия: {response.data}")
            return True
        else:
            logger.error(f"❌ Ошибка при получении данных из Supabase: {response}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при подключении к Supabase: {e}")
        logger.error("   Проверьте правильность URL и ключа API.")
        return False

def main():
    """Основная функция для тестирования подключения к Supabase."""
    logger.info("🔍 Начинаем тестирование подключения к Supabase...")
    
    # Проверяем переменные окружения
    env_ok = check_env_variables()
    if not env_ok:
        logger.error("❌ Тестирование не может быть продолжено: отсутствуют переменные окружения.")
        return
    
    # Проверяем наличие модуля supabase
    module_ok = check_supabase_module()
    if not module_ok:
        logger.error("❌ Тестирование не может быть продолжено: модуль supabase не установлен.")
        return
    
    # Тестируем подключение
    connection_ok = test_supabase_connection()
    if connection_ok:
        logger.info("✅ Все тесты пройдены успешно! Подключение к Supabase работает корректно.")
    else:
        logger.error("❌ Тестирование завершено с ошибками. Подключение к Supabase не работает.")

if __name__ == "__main__":
    main() 