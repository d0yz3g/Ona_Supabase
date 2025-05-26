#!/usr/bin/env python3
"""
Скрипт для добавления заглушки OpenAI и AsyncOpenAI в main.py
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_main_openai")

# Файл, который нужно исправить
MAIN_FILE = "main.py"

# Код заглушки OpenAI, который нужно добавить
OPENAI_MOCK_CODE = """
# Заглушка OpenAI для совместимости
try:
    from openai import OpenAI, AsyncOpenAI
    logger.info("Импортированы OpenAI и AsyncOpenAI из openai")
except ImportError:
    logger.warning("Не удалось импортировать OpenAI из openai, использую заглушку")
    # Заглушка для AsyncOpenAI
    class AsyncOpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key
            logger.info("[AsyncOpenAI Mock] Инициализация заглушки AsyncOpenAI")
        
        class chat:
            @staticmethod
            def completions():
                class Create:
                    @staticmethod
                    async def create(*args, **kwargs):
                        logger.info("[AsyncOpenAI Mock] Вызов метода chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
                return Create()
    
    # Заглушка для OpenAI
    class OpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key
            logger.info("[OpenAI Mock] Инициализация заглушки OpenAI")
        
        class chat:
            @staticmethod
            def completions():
                class Create:
                    @staticmethod
                    def create(*args, **kwargs):
                        logger.info("[OpenAI Mock] Вызов метода chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
                return Create()
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

def fix_main_file():
    """Исправляет main.py, добавляя в него заглушку для OpenAI"""
    if not os.path.exists(MAIN_FILE):
        logger.error(f"Файл {MAIN_FILE} не найден")
        return False
    
    # Создаем резервную копию
    if not backup_file(MAIN_FILE):
        return False
    
    try:
        with open(MAIN_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже заглушка OpenAI
        if "class AsyncOpenAI" in content and "class OpenAI" in content:
            logger.info(f"Файл {MAIN_FILE} уже содержит заглушки OpenAI и AsyncOpenAI")
            return True
        
        # Находим место для вставки заглушки - после импортов
        import_section_end = 0
        in_import_section = False
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                in_import_section = True
                import_section_end = i
            elif in_import_section and line.strip() and not (line.startswith('import ') or line.startswith('from ')):
                break
        
        # Вставляем заглушку после импортов
        insert_pos = import_section_end + 1
        lines.insert(insert_pos, OPENAI_MOCK_CODE)
        
        # Записываем изменения обратно в файл
        with open(MAIN_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Файл {MAIN_FILE} успешно исправлен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {MAIN_FILE}: {e}")
        # Восстанавливаем из резервной копии
        try:
            with open(f"{MAIN_FILE}.bak", 'r', encoding='utf-8') as src:
                with open(MAIN_FILE, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Файл {MAIN_FILE} восстановлен из резервной копии")
        except Exception as restore_error:
            logger.error(f"Ошибка при восстановлении файла {MAIN_FILE}: {restore_error}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало исправления main.py ===")
    
    if fix_main_file():
        logger.info("=== Исправление main.py выполнено успешно ===")
        return 0
    else:
        logger.error("=== Не удалось исправить main.py ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 