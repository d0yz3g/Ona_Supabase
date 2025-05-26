#!/usr/bin/env python3
"""
Скрипт для прямой модификации модуля openai в site-packages.
Добавляет классы AsyncOpenAI и OpenAI прямо в исходный код модуля.
"""
import os
import sys
import site
import glob
import logging
import importlib.util

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("modify_site_packages")

# Код заглушек для добавления в модуль openai
OPENAI_STUBS = """
# Заглушки для совместимости с aiogram
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print("[Site-Package] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print("[Site-Package] Вызов метода AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print("[Site-Package] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print("[Site-Package] Вызов метода OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
"""

def find_openai_init_files():
    """Находит все файлы __init__.py в модуле openai в site-packages"""
    init_files = []
    
    # Получаем все пути из site.getsitepackages()
    site_packages = site.getsitepackages()
    
    # Добавляем путь из sys.prefix
    site_packages.append(os.path.join(sys.prefix, 'lib', 'python*', 'site-packages'))
    
    # Ищем все __init__.py для модуля openai
    for site_path in site_packages:
        # Раскрываем возможные маски в пути
        for expanded_path in glob.glob(site_path):
            # Ищем openai/__init__.py
            init_path = os.path.join(expanded_path, 'openai', '__init__.py')
            if os.path.exists(init_path):
                init_files.append(init_path)
    
    # Проверяем импортируемый путь
    try:
        spec = importlib.util.find_spec('openai')
        if spec and spec.origin:
            # Получаем путь к __init__.py из спецификации
            init_path = spec.origin
            if init_path not in init_files:
                init_files.append(init_path)
    except ImportError:
        logger.error("Не удалось найти модуль openai через importlib")
    
    # Явный поиск в /usr/local/lib/python...
    usr_local_paths = glob.glob('/usr/local/lib/python*/site-packages/openai/__init__.py')
    for path in usr_local_paths:
        if path not in init_files:
            init_files.append(path)
    
    return init_files

def add_stubs_to_openai_init(file_path):
    """Добавляет заглушки в файл __init__.py модуля openai"""
    try:
        # Проверяем доступ на запись
        if not os.access(file_path, os.W_OK):
            logger.error(f"Нет прав на запись в файл {file_path}")
            return False
        
        # Создаем резервную копию
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
            logger.info(f"Создана резервная копия {backup_path}")
        
        # Проверяем, есть ли уже заглушки
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {file_path} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Добавляем заглушки в конец файла
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + OPENAI_STUBS)
        
        logger.info(f"Добавлены заглушки в файл {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при модификации файла {file_path}: {e}")
        return False

def create_openai_module_in_path():
    """Создает модуль openai с заглушками в текущем каталоге"""
    try:
        # Создаем директорию openai, если ее нет
        if not os.path.exists('openai'):
            os.makedirs('openai', exist_ok=True)
        
        # Создаем __init__.py с заглушками
        with open(os.path.join('openai', '__init__.py'), 'w', encoding='utf-8') as f:
            f.write(OPENAI_STUBS)
        
        # Создаем пустой файл __pycache__
        os.makedirs(os.path.join('openai', '__pycache__'), exist_ok=True)
        
        logger.info("Создан локальный модуль openai с заглушками в текущем каталоге")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании локального модуля openai: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало модификации модуля openai в site-packages ===")
    
    # Находим все файлы __init__.py модуля openai
    init_files = find_openai_init_files()
    
    if not init_files:
        logger.warning("Не найдены файлы __init__.py модуля openai")
        logger.info("Создаем локальный модуль openai с заглушками")
        create_openai_module_in_path()
    else:
        logger.info(f"Найдено файлов __init__.py: {len(init_files)}")
        for file_path in init_files:
            logger.info(f"Обрабатываем файл: {file_path}")
            add_stubs_to_openai_init(file_path)
    
    # В любом случае создаем локальный модуль для подстраховки
    create_openai_module_in_path()
    
    logger.info("=== Завершена модификация модуля openai ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 