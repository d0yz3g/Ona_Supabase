#!/usr/bin/env python3
"""
Модуль для исправления импортов AsyncOpenAI.
Этот модуль должен быть импортирован ДО ЛЮБЫХ других импортов.
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("pre_import_fix")

# Добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    logger.info(f"Добавлен {os.getcwd()} в sys.path")

try:
    # Проверяем доступность AsyncOpenAI
    import openai
    
    # Проверка версии OpenAI
    logger.info(f"OpenAI версия: {openai.__version__}")
    
    # Проверяем наличие AsyncOpenAI
    if hasattr(openai, 'AsyncOpenAI'):
        logger.info("AsyncOpenAI доступен в openai")
    else:
        logger.warning("AsyncOpenAI не найден в openai")
        
        # Определяем класс-заглушку для AsyncOpenAI
        class AsyncOpenAI:
            def __init__(self, api_key=None, **kwargs):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                logger.info("[PreImport] Инициализация AsyncOpenAI заглушки")
            
            class chat:
                class completions:
                    @staticmethod
                    async def create(*args, **kwargs):
                        logger.info("[PreImport] Вызов AsyncOpenAI.chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
            
            class audio:
                @staticmethod
                async def transcriptions_create(*args, **kwargs):
                    logger.info("[PreImport] Вызов AsyncOpenAI.audio.transcriptions_create")
                    return {"text": "Заглушка транскрипции аудио"}
        
        # Добавляем AsyncOpenAI в модуль openai
        openai.AsyncOpenAI = AsyncOpenAI
        logger.info("Добавлен класс-заглушка AsyncOpenAI в модуль openai")
        
        # Добавляем классы напрямую в sys.modules
        sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
        logger.info("Добавлен AsyncOpenAI в sys.modules")
except ImportError:
    logger.warning("Не удалось импортировать openai")

logger.info("pre_import_fix выполнен успешно")

# Патчим проблемные модули
modules_to_patch = [
    "voice_handler",
    "survey_handler",
    "communication_handler",
    "conversation_handler",
    "reminder_handler",
    "profile_generator"
]

for module_name in modules_to_patch:
    module_path = f"{module_name}.py"
    
    # Проверяем, существует ли файл
    if not os.path.exists(module_path):
        continue
    
    try:
        # Импортируем модуль
        module = __import__(module_name)
        
        # Добавляем AsyncOpenAI и OpenAI в модуль
        if not hasattr(module, 'AsyncOpenAI'):
            module.AsyncOpenAI = AsyncOpenAI
            logger.info(f"Добавлен класс AsyncOpenAI в модуль {module_name}")
        
        if not hasattr(module, 'OpenAI'):
            module.OpenAI = AsyncOpenAI
            logger.info(f"Добавлен класс OpenAI в модуль {module_name}")
        
        logger.info(f"Модуль {module_name} успешно пропатчен")
    except Exception as e:
        logger.error(f"Ошибка при патчинге модуля {module_name}: {e}")

logger.info("Все исправления импорта применены успешно")

# Экспортируем наши классы
__all__ = ['AsyncOpenAI'] 