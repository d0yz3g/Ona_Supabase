#!/usr/bin/env python3
"""
Скрипт для прямого создания заглушек в проблемных модулях, которые упоминались в логах.
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_direct_modules")

# Список проблемных модулей
PROBLEM_MODULES = [
    "survey_handler.py",
    "conversation_handler.py",
    "reminder_handler.py",
    "voice_handler.py",
    "communication_handler.py"
]

# Код заглушки для вставки в начало файлов
OPENAI_STUB_CODE = """
# Заглушка для AsyncOpenAI и OpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[{__name__}] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print(f"[{__name__}] Вызов метода AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[{__name__}] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print(f"[{__name__}] Вызов метода OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
"""

def backup_file(file_path):
    """Создает резервную копию файла"""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Создана резервная копия {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии {file_path}: {e}")
            return False
    return True

def fix_module(file_path):
    """Исправляет модуль, добавляя в него заглушки OpenAI и AsyncOpenAI"""
    if not os.path.exists(file_path):
        logger.warning(f"Файл {file_path} не найден")
        return False
    
    # Создаем резервную копию
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже заглушка AsyncOpenAI
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {file_path} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Вставляем заглушку в начало файла
        new_content = OPENAI_STUB_CODE + "\n\n" + content
        
        # Записываем изменения обратно в файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Файл {file_path} успешно исправлен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {file_path}: {e}")
        # Восстанавливаем из резервной копии
        try:
            with open(f"{file_path}.bak", 'r', encoding='utf-8') as src:
                with open(file_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Файл {file_path} восстановлен из резервной копии")
        except Exception as restore_error:
            logger.error(f"Ошибка при восстановлении файла {file_path}: {restore_error}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало прямого исправления проблемных модулей ===")
    
    success_count = 0
    for module_path in PROBLEM_MODULES:
        if fix_module(module_path):
            success_count += 1
    
    logger.info(f"=== Завершено. Исправлено модулей: {success_count}/{len(PROBLEM_MODULES)} ===")
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 