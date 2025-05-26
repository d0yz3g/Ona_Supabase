#!/usr/bin/env python3
"""
Скрипт для создания заглушек для конкретных проблемных модулей.
Создает полностью новые версии модулей, которые вызывают ошибки.
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_problem_modules")

# Список проблемных модулей и содержимое заглушек
PROBLEM_MODULES = {
    "survey_handler.py": """#!/usr/bin/env python3
# Заглушка для survey_handler.py
import logging
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI в survey_handler")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create в survey_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки OpenAI в survey_handler")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create в survey_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

survey_router = Router()

@survey_router.message(Command("survey"))
async def handle_survey(message: Message):
    await message.answer("Это заглушка для команды /survey")

def get_survey_router():
    logger.info("Вызов get_survey_router()")
    return survey_router
""",
    
    "voice_handler.py": """#!/usr/bin/env python3
# Заглушка для voice_handler.py
import logging
import os
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI в voice_handler")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create в voice_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки OpenAI в voice_handler")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create в voice_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

voice_router = Router()

@voice_router.message(F.voice)
async def handle_voice(message: Message):
    await message.answer("Это заглушка для обработки голосовых сообщений")

def get_voice_router():
    logger.info("Вызов get_voice_router()")
    return voice_router
""",
    
    "communication_handler.py": """#!/usr/bin/env python3
# Заглушка для communication_handler.py
import logging
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI в communication_handler")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create в communication_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки OpenAI в communication_handler")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create в communication_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

communication_router = Router()

@communication_router.message(Command("chat"))
async def handle_chat(message: Message):
    await message.answer("Это заглушка для команды /chat")

@communication_router.message(F.text)
async def handle_text(message: Message):
    await message.answer("Это заглушка для обработки текстовых сообщений")

def get_communication_router():
    logger.info("Вызов get_communication_router()")
    return communication_router
""",
    
    "conversation_handler.py": """#!/usr/bin/env python3
# Заглушка для conversation_handler.py
import logging
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI в conversation_handler")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create в conversation_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки OpenAI в conversation_handler")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create в conversation_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

conversation_router = Router()

@conversation_router.message(Command("talk"))
async def handle_talk(message: Message):
    await message.answer("Это заглушка для команды /talk")

def get_conversation_router():
    logger.info("Вызов get_conversation_router()")
    return conversation_router
""",
    
    "reminder_handler.py": """#!/usr/bin/env python3
# Заглушка для reminder_handler.py
import logging
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки AsyncOpenAI в reminder_handler")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Stub] Вызов AsyncOpenAI.chat.completions.create в reminder_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("[Stub] Инициализация заглушки OpenAI в reminder_handler")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Stub] Вызов OpenAI.chat.completions.create в reminder_handler")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

reminder_router = Router()

@reminder_router.message(Command("remind"))
async def handle_remind(message: Message):
    await message.answer("Это заглушка для команды /remind")

def get_reminder_router():
    logger.info("Вызов get_reminder_router()")
    return reminder_router
"""
}

def create_module_stub(module_name, content):
    """Создает файл-заглушку для модуля"""
    try:
        # Создаем резервную копию, если файл существует
        if os.path.exists(module_name):
            backup_path = f"{module_name}.bak"
            if not os.path.exists(backup_path):
                with open(module_name, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Создана резервная копия {backup_path}")
        
        # Записываем содержимое заглушки
        with open(module_name, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Создана заглушка для модуля {module_name}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании заглушки для модуля {module_name}: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало создания заглушек для проблемных модулей ===")
    
    success_count = 0
    for module_name, content in PROBLEM_MODULES.items():
        if create_module_stub(module_name, content):
            success_count += 1
    
    logger.info(f"=== Завершено. Создано заглушек: {success_count}/{len(PROBLEM_MODULES)} ===")
    return 0 if success_count == len(PROBLEM_MODULES) else 1

if __name__ == "__main__":
    sys.exit(main()) 