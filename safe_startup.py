#!/usr/bin/env python3
"""
Безопасная обертка для запуска main.py с предварительным патчингом openai.
"""
import os
import sys
import logging
import importlib.util

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("safe_startup")

def add_openai_stubs():
    """Добавляет заглушки AsyncOpenAI и OpenAI в модуль openai"""
    try:
        import openai
        logger.info("Импортирован модуль openai")
        
        # Добавляем заглушки, если их нет
        if not hasattr(openai, 'AsyncOpenAI'):
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
            
            openai.AsyncOpenAI = AsyncOpenAI
            logger.info("Добавлена заглушка AsyncOpenAI в модуль openai")
        
        if not hasattr(openai, 'OpenAI'):
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
            
            openai.OpenAI = OpenAI
            logger.info("Добавлена заглушка OpenAI в модуль openai")
        
        # Проверяем успешность патча
        if hasattr(openai, 'AsyncOpenAI') and hasattr(openai, 'OpenAI'):
            logger.info("Модуль openai успешно пропатчен")
            return True
        else:
            logger.error("Не удалось пропатчить модуль openai")
            return False
    
    except ImportError as e:
        logger.error(f"Не удалось импортировать модуль openai: {e}")
        return False

def run_main():
    """Запускает main.py"""
    logger.info("Запуск main.py...")
    
    # Проверяем наличие main.py
    if not os.path.exists("main.py"):
        logger.error("Файл main.py не найден")
        return 1
    
    try:
        # Загружаем main.py как модуль
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # Вызываем main() из main.py, если она есть
        if hasattr(main_module, 'main'):
            logger.info("Вызов функции main() из main.py")
            return main_module.main()
        else:
            logger.info("Функция main() не найдена в main.py")
            return 0
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении main.py: {e}")
        return 1

def main():
    """Основная функция скрипта"""
    logger.info("=== Безопасный запуск приложения ===")
    
    # Добавляем заглушки в модуль openai
    add_openai_stubs()
    
    # Запускаем main.py
    result = run_main()
    
    logger.info(f"=== Завершение работы с кодом возврата {result} ===")
    return result

if __name__ == "__main__":
    sys.exit(main()) 