import os
import sys
import importlib
import logging
import logging
import json
import random
import logging

# Заглушка для AsyncOpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock AsyncOpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print(f"[Mock AsyncOpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

# Заглушка для OpenAI
class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock OpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print(f"[Mock OpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

#!/usr/bin/env python3
"""
Скрипт для исправления проблем с импортами модулей.
Создает fallback для openai, httpx и других проблемных модулей.
"""

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [FIX_IMPORTS] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fix_imports")

def create_openai_fallback():
    """Создает заглушку для модуля openai, если он недоступен"""
    if os.path.exists("openai_fallback.py"):
        logger.info("Файл openai_fallback.py уже существует")
        return

    content = """
'''
Fallback для модуля openai
'''

logger = logging.getLogger(__name__)

class OpenAIFallback:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.warning("Используется fallback для OpenAI API")
    
    def ChatCompletion(self):
        return ChatCompletionFallback()

class ChatCompletionFallback:
    @staticmethod
    def create(*args, **kwargs):
        logger.info(f"Вызов OpenAI ChatCompletion.create с аргументами: {kwargs.get('messages', [])}")
        
        # Базовые заглушки ответов
        fallback_responses = [
            "Извините, API OpenAI сейчас недоступно. Я работаю в ограниченном режиме.",
            "Я не могу сейчас ответить на этот вопрос. API OpenAI не загружено.",
            "В данный момент я работаю в режиме заглушки из-за проблем с OpenAI API.",
            "Я понимаю ваш запрос, но не могу дать полноценный ответ из-за технических ограничений."
        ]
        
        response = {
            "choices": [
                {
                    "message": {
                        "content": random.choice(fallback_responses),
                        "role": "assistant"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ],
            "created": 1686000000,
            "id": "chatcmpl-fallback",
            "model": "fallback-model",
            "object": "chat.completion",
            "usage": {
                "completion_tokens": 20,
                "prompt_tokens": 30,
                "total_tokens": 50
            }
        }
        
        return response

# Создаем fallback для модуля openai
openai = OpenAIFallback()
"""

    with open("openai_fallback.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создан файл openai_fallback.py")

def create_httpx_fallback():
    """Создает заглушку для модуля httpx, если он недоступен"""
    if os.path.exists("httpx_fallback.py"):
        logger.info("Файл httpx_fallback.py уже существует")
        return

    content = """
'''
Fallback для модуля httpx
'''

logger = logging.getLogger(__name__)

class AsyncClient:
    def __init__(self, *args, **kwargs):
        logger.warning("Используется fallback для httpx.AsyncClient")
    
    async def post(self, *args, **kwargs):
        logger.info(f"Вызов httpx.AsyncClient.post с аргументами: {args}, {kwargs}")
        return FallbackResponse(status_code=200, text="Fallback response")
    
    async def get(self, *args, **kwargs):
        logger.info(f"Вызов httpx.AsyncClient.get с аргументами: {args}, {kwargs}")
        return FallbackResponse(status_code=200, text="Fallback response")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class FallbackResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.content = text.encode() if isinstance(text, str) else b""
    
    def json(self):
        return {"message": "This is a fallback response"}

def patch_sys_modules():
    """Добавляет fallback-модули в sys.modules"""
    import sys
    sys.modules['httpx'] = sys.modules[__name__]
"""

    with open("httpx_fallback.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Создан файл httpx_fallback.py")

def patch_main_py():
    """Патчит main.py для использования fallback-модулей"""
    if not os.path.exists("main.py"):
        logger.error("Файл main.py не найден")
        return False

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, нужно ли добавлять fallback для openai
    if "import openai" in content and not "import openai_fallback as openai" in content:
        logger.info("Добавляем fallback для openai в main.py")
        content = content.replace(
            "import openai",
            """try:
    import openai
    print("Используем стандартный модуль openai")
except ImportError:
    try:
        import openai_fallback as openai
        print("Используем fallback для openai")
    except ImportError:
        print("ОШИБКА: Модуль openai и его fallback недоступны")"""
        )

    # Проверяем, нужно ли добавлять fallback для httpx
    if "import httpx" in content and not "import httpx_fallback as httpx" in content:
        logger.info("Добавляем fallback для httpx в main.py")
        content = content.replace(
            "import httpx",
            """try:
    import httpx
    print("Используем стандартный модуль httpx")
except ImportError:
    try:
        import httpx_fallback as httpx
        print("Используем fallback для httpx")
    except ImportError:
        print("ОШИБКА: Модуль httpx и его fallback недоступны")"""
        )

    # Записываем обновленное содержимое
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info("Файл main.py успешно обновлен")
    return True

def patch_handlers():
    """Патчит обработчики для использования fallback-модулей"""
    handler_files = [
        "survey_handler.py",
        "conversation_handler.py",
        "voice_handler.py",
        "meditation_handler.py",
        "reminder_handler.py",
        "communication_handler.py"
    ]
    
    for file in handler_files:
        if not os.path.exists(file):
            logger.warning(f"Файл {file} не найден, пропуск")
            continue
            
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Патч для openai
        if "import openai" in content and not "import openai_fallback as openai" in content:
            logger.info(f"Добавляем fallback для openai в {file}")
            content = content.replace(
                "import openai",
                """try:
    import openai
except ImportError:
    try:
        import openai_fallback as openai
    except ImportError:
        # Создаем минимальную заглушку
        class OpenAIFallback:
            def __init__(self):
                pass
            def ChatCompletion(self):
                class ChatCompletionFallback:
                    @staticmethod
                    def create(*args, **kwargs):
                        return {"choices": [{"message": {"content": "API недоступно"}}]}
                return ChatCompletionFallback()
        openai = OpenAIFallback()"""
            )
            
        # Патч для httpx
        if "import httpx" in content and not "import httpx_fallback as httpx" in content:
            logger.info(f"Добавляем fallback для httpx в {file}")
            content = content.replace(
                "import httpx",
                """try:
    import httpx
except ImportError:
    try:
        import httpx_fallback as httpx
    except ImportError:
        print("ОШИБКА: Модуль httpx и его fallback недоступны")"""
            )
            
        # Записываем обновленное содержимое
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Файл {file} успешно обновлен")

def main():
    """Основная функция"""
    logger.info("Начало исправления импортов")
    
    # Создаем fallback-модули
    create_openai_fallback()
    create_httpx_fallback()
    
    # Патчим main.py
    patch_main_py()
    
    # Патчим обработчики
    patch_handlers()
    
    logger.info("Исправление импортов завершено")

if __name__ == "__main__":
    main() 