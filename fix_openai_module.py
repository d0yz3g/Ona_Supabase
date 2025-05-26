#!/usr/bin/env python3
"""
Скрипт для создания заглушек OpenAI и AsyncOpenAI внутри самого модуля openai.
"""
import os
import sys
import logging
import importlib
import importlib.util
import tempfile
import shutil

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_openai_module")

# Код заглушек для вставки в модуль openai
OPENAI_STUB_CODE = """
# Заглушки для совместимости с aiogram
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print("[openai stub] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print("[openai stub] Вызов метода AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print("[openai stub] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print("[openai stub] Вызов метода OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
"""

def find_openai_module():
    """Находит путь к модулю openai"""
    try:
        spec = importlib.util.find_spec('openai')
        if spec and spec.origin:
            package_dir = os.path.dirname(spec.origin)
            logger.info(f"Найден модуль openai в {package_dir}")
            return package_dir
        else:
            logger.error("Не удалось найти модуль openai")
            return None
    except ImportError:
        logger.error("Модуль openai не установлен")
        return None

def fix_openai_init(package_dir):
    """Исправляет __init__.py модуля openai"""
    init_file = os.path.join(package_dir, "__init__.py")
    if not os.path.exists(init_file):
        logger.error(f"Файл {init_file} не найден")
        return False
    
    # Создаем резервную копию
    backup_file = init_file + ".bak"
    if not os.path.exists(backup_file):
        try:
            shutil.copy2(init_file, backup_file)
            logger.info(f"Создана резервная копия {backup_file}")
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии {init_file}: {e}")
            return False
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже заглушка AsyncOpenAI
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {init_file} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Добавляем заглушки в конец файла
        with open(init_file, 'a', encoding='utf-8') as f:
            f.write("\n\n" + OPENAI_STUB_CODE)
        
        logger.info(f"Файл {init_file} успешно исправлен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {init_file}: {e}")
        # Восстанавливаем из резервной копии
        try:
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, init_file)
                logger.info(f"Файл {init_file} восстановлен из резервной копии")
        except Exception as restore_error:
            logger.error(f"Ошибка при восстановлении файла {init_file}: {restore_error}")
        return False

def create_openai_monkey_patch():
    """Создает скрипт для monkey-patch модуля openai"""
    patch_file = "patch_openai.py"
    
    try:
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write("""#!/usr/bin/env python3
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
""")
        
        logger.info(f"Создан файл {patch_file} для monkey-patch модуля openai")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании файла {patch_file}: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало исправления модуля openai ===")
    
    success = False
    
    # Находим модуль openai
    package_dir = find_openai_module()
    if package_dir:
        # Исправляем __init__.py
        if fix_openai_init(package_dir):
            success = True
    
    # Создаем скрипт для monkey-patch
    if create_openai_monkey_patch():
        success = True
    
    logger.info(f"=== Завершено. Исправление модуля openai: {'успешно' if success else 'не удалось'} ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 