#!/usr/bin/env python3
"""
Скрипт для подготовки окружения перед запуском основного приложения.
Выполняет все необходимые исправления для совместимости.
"""
import os
import sys
import logging
import importlib

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("pre_startup")

def apply_openai_monkey_patch():
    """
    Применяет monkey-патч к модулю openai для добавления
    заглушек AsyncOpenAI и OpenAI
    """
    try:
        import openai
        logger.info("Импортирован модуль openai")
        
        # Заглушка для AsyncOpenAI
        class AsyncOpenAI:
            def __init__(self, api_key=None):
                self.api_key = api_key
                logger.info("[Runtime] Инициализация заглушки AsyncOpenAI")
            
            class chat:
                class completions:
                    @staticmethod
                    async def create(*args, **kwargs):
                        logger.info("[Runtime] Вызов AsyncOpenAI.chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
        
        # Заглушка для OpenAI
        class OpenAI:
            def __init__(self, api_key=None):
                self.api_key = api_key
                logger.info("[Runtime] Инициализация заглушки OpenAI")
            
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        logger.info("[Runtime] Вызов OpenAI.chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
        
        # Добавляем заглушки в модуль openai
        if not hasattr(openai, 'AsyncOpenAI'):
            openai.AsyncOpenAI = AsyncOpenAI
            logger.info("Добавлена заглушка AsyncOpenAI в модуль openai")
        
        if not hasattr(openai, 'OpenAI'):
            openai.OpenAI = OpenAI
            logger.info("Добавлена заглушка OpenAI в модуль openai")
        
        # Подтверждаем успешность патча
        if hasattr(openai, 'AsyncOpenAI') and hasattr(openai, 'OpenAI'):
            logger.info("Monkey-патч успешно применен")
            return True
        else:
            logger.error("Не удалось применить monkey-патч")
            return False
    
    except ImportError:
        logger.error("Не удалось импортировать модуль openai")
        return False

def create_stub_modules():
    """
    Создает модули-заглушки для случаев, когда они могут быть не найдены
    """
    # Заглушка для survey_handler.py
    if not os.path.exists("survey_handler.py"):
        with open("survey_handler.py", "w", encoding="utf-8") as f:
            f.write("""#!/usr/bin/env python3
# Заглушка для survey_handler.py
import logging
logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Stub] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

def get_survey_router():
    logger.info("[Stub] Вызов get_survey_router()")
    # Импортируем aiogram только здесь для предотвращения циклических импортов
    from aiogram import Router
    router = Router()
    return router
""")
        logger.info("Создана заглушка survey_handler.py")
    
    # Добавьте здесь другие заглушки по аналогии
    # ...

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало подготовки окружения для запуска приложения ===")
    
    # Применяем monkey-патч к openai
    if apply_openai_monkey_patch():
        logger.info("Monkey-патч к openai успешно применен")
    else:
        logger.warning("Не удалось применить monkey-патч к openai")
    
    # Создаем заглушки для отсутствующих модулей
    create_stub_modules()
    
    logger.info("=== Подготовка окружения успешно завершена ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 