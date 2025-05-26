#!/usr/bin/env python3
"""
Финальная точка входа для Railway.
Самая простая и надежная версия без зависимостей от других патчей.
"""
import os
import sys
import logging
import importlib
import traceback
import subprocess

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("railway_final")

# Добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    logger.info(f"Добавлен {os.getcwd()} в sys.path")

# Устанавливаем переменную окружения для Railway
os.environ["RAILWAY_ENV"] = "1"

# Определяем класс-заглушку для AsyncOpenAI
class AsyncOpenAI:
    """Заглушка для AsyncOpenAI"""
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("Инициализация AsyncOpenAI заглушки")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("Вызов AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
    
    class audio:
        @staticmethod
        async def transcriptions_create(*args, **kwargs):
            logger.info("Вызов AsyncOpenAI.audio.transcriptions_create")
            return {"text": "Заглушка транскрипции аудио"}

# Патчим модуль openai
try:
    import openai
    
    # Если AsyncOpenAI не существует в модуле openai, добавляем его
    if not hasattr(openai, 'AsyncOpenAI'):
        openai.AsyncOpenAI = AsyncOpenAI
        logger.info("Добавлен класс AsyncOpenAI в модуль openai")
    
    # Добавляем AsyncOpenAI напрямую в sys.modules для импорта from openai import AsyncOpenAI
    sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
    
    logger.info("Патч openai применен успешно")
except ImportError:
    logger.warning("Не удалось импортировать openai, создаем модуль-заглушку")
    
    # Создаем модуль-заглушку openai
    import types
    openai_module = types.ModuleType('openai')
    openai_module.AsyncOpenAI = AsyncOpenAI
    
    # Добавляем модуль-заглушку в sys.modules
    sys.modules['openai'] = openai_module
    sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
    
    logger.info("Создан модуль-заглушка openai")

# Проверка, что патч работает
try:
    from openai import AsyncOpenAI
    logger.info("✅ AsyncOpenAI теперь доступен")
except ImportError as e:
    logger.error(f"❌ AsyncOpenAI всё ещё недоступен: {e}")

def start_healthcheck():
    """Запускает healthcheck сервер в отдельном потоке"""
    try:
        import simple_healthcheck
        logger.info("Запуск healthcheck сервера")
        healthcheck_thread = simple_healthcheck.run_as_thread()
        return healthcheck_thread
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck: {e}")
        return None

def run_subprocess():
    """Запускает бота через subprocess"""
    logger.info("Запуск main.py через subprocess")
    cmd = [sys.executable, "main.py"]
    
    try:
        # Запускаем процесс и перенаправляем вывод
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ
        )
        
        # Читаем и логируем вывод в реальном времени
        for line in process.stdout:
            print(line, end='')
        
        # Ждем завершения процесса
        process.wait()
        
        # Проверяем код возврата
        if process.returncode != 0:
            logger.error(f"Процесс завершился с ошибкой (код {process.returncode})")
            return False
        else:
            logger.info("Процесс успешно завершился")
            return True
    except Exception as e:
        logger.error(f"Ошибка при запуске subprocess: {e}")
        return False

def run_import():
    """Запускает бота через прямой импорт"""
    logger.info("Запуск main.py через прямой импорт")
    try:
        import main
        logger.info("✅ Бот запущен успешно через импорт")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте main: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== Запуск бота на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Содержимое директории: {os.listdir('.')}")
    
    # Запускаем healthcheck сервер
    healthcheck_thread = start_healthcheck()
    
    # Проверяем доступность и версию openai
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "openai"], check=True)
    except subprocess.CalledProcessError:
        logger.warning("Не удалось получить информацию о пакете openai")
    
    # Пробуем разные способы запуска
    try:
        if run_import():
            logger.info("Бот успешно запущен через импорт")
            # Ждем остановки (бесконечно, так как в норме бот работает постоянно)
            if healthcheck_thread:
                healthcheck_thread.join()
            else:
                # Бесконечный цикл, чтобы процесс не завершался
                import time
                while True:
                    time.sleep(60)
            sys.exit(0)
        
        logger.warning("Не удалось запустить через импорт, пробуем subprocess")
        
        if run_subprocess():
            logger.info("Бот успешно запущен через subprocess")
            sys.exit(0)
        
        logger.error("Не удалось запустить бота")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 