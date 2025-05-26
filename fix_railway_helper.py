#!/usr/bin/env python3
"""
Скрипт для исправления railway_helper.py, добавляя в него заглушку для AsyncOpenAI
"""
import os
import re
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_railway_helper")

# Файл, который нужно исправить
RAILWAY_HELPER_FILE = "railway_helper.py"

# Код заглушки AsyncOpenAI, который нужно добавить
OPENAI_MOCK_CODE = """
# Заглушка для AsyncOpenAI из openai
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print("[AsyncOpenAI Mock] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        @staticmethod
        async def completions():
            class Create:
                @staticmethod
                async def create(*args, **kwargs):
                    print("[AsyncOpenAI Mock] Вызов метода chat.completions.create")
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

def fix_railway_helper():
    """Исправляет railway_helper.py, добавляя в него заглушку для AsyncOpenAI"""
    if not os.path.exists(RAILWAY_HELPER_FILE):
        logger.error(f"Файл {RAILWAY_HELPER_FILE} не найден")
        return False
    
    # Создаем резервную копию
    if not backup_file(RAILWAY_HELPER_FILE):
        return False
    
    try:
        with open(RAILWAY_HELPER_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже заглушка AsyncOpenAI
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {RAILWAY_HELPER_FILE} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Находим место для вставки заглушки (перед функцией main или в конце файла)
        if "def main" in content:
            pattern = re.compile(r'def\s+main.*?[\(:]')
            match = pattern.search(content)
            if match:
                insert_pos = match.start()
                content = content[:insert_pos] + OPENAI_MOCK_CODE + "\n\n" + content[insert_pos:]
            else:
                content += "\n\n" + OPENAI_MOCK_CODE
        else:
            content += "\n\n" + OPENAI_MOCK_CODE
        
        # Добавляем импорт для использования в других файлах
        import_line = "\n# Экспортируем AsyncOpenAI для использования в других модулях\n__all__ = ['AsyncOpenAI']\n"
        if "__all__" in content:
            # Модифицируем существующий __all__
            pattern = re.compile(r'__all__\s*=\s*\[.*?\]')
            match = pattern.search(content)
            if match:
                current_all = match.group(0)
                new_all = current_all[:-1] + ", 'AsyncOpenAI']"
                content = content.replace(current_all, new_all)
            else:
                content += import_line
        else:
            # Добавляем новый __all__
            content += import_line
        
        # Записываем изменения обратно в файл
        with open(RAILWAY_HELPER_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Файл {RAILWAY_HELPER_FILE} успешно исправлен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {RAILWAY_HELPER_FILE}: {e}")
        # Восстанавливаем из резервной копии
        try:
            with open(f"{RAILWAY_HELPER_FILE}.bak", 'r', encoding='utf-8') as src:
                with open(RAILWAY_HELPER_FILE, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Файл {RAILWAY_HELPER_FILE} восстановлен из резервной копии")
        except Exception as restore_error:
            logger.error(f"Ошибка при восстановлении файла {RAILWAY_HELPER_FILE}: {restore_error}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало исправления railway_helper.py ===")
    
    if fix_railway_helper():
        logger.info("=== Исправление railway_helper.py выполнено успешно ===")
        return 0
    else:
        logger.error("=== Не удалось исправить railway_helper.py ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 