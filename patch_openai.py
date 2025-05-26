#!/usr/bin/env python3
'''
Скрипт для monkey-patch модуля openai
'''
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("patch_openai")

# Заглушки для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Monkey patch] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Monkey patch] Вызов метода AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Monkey patch] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Monkey patch] Вызов метода OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

try:
    # Применяем monkey-patch к модулю openai
    import openai
    logger.info("Применяем monkey-patch к модулю openai")
    
    # Добавляем заглушки в модуль openai
    openai.AsyncOpenAI = AsyncOpenAI
    openai.OpenAI = OpenAI
    
    # Подтверждаем успешность патча
    logger.info("Monkey-patch успешно применен")
    logger.info(f"openai.AsyncOpenAI доступен: {hasattr(openai, 'AsyncOpenAI')}")
    logger.info(f"openai.OpenAI доступен: {hasattr(openai, 'OpenAI')}")
    
except ImportError:
    logger.error("Не удалось импортировать модуль openai")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Скрипт patch_openai.py выполнен успешно")
    sys.exit(0)
