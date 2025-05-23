#!/usr/bin/env python
"""
Скрипт для исправления путей импорта в среде Railway.
Запускается перед основным скриптом бота для обеспечения корректного импорта модулей.
"""

import os
import sys
import shutil
import importlib
import logging
from pathlib import Path

# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [IMPORT_FIX] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_imports")

def check_environment():
    """Проверяет текущее окружение и пути Python."""
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Переменные окружения: {os.environ.get('PYTHONPATH', 'Не установлена')}")
    logger.info(f"Файлы в текущей директории: {[f for f in os.listdir('.') if f.endswith('.py')]}")

def fix_imports():
    """
    Исправляет пути импорта для корректной работы в Railway.
    
    1. Добавляет текущую директорию в sys.path
    2. Проверяет наличие всех необходимых модулей
    3. Пытается импортировать основные модули
    """
    # Добавляем текущую директорию в sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Добавлен путь {current_dir} в sys.path")
    
    # Проверка наличия ключевых файлов
    required_files = [
        "main.py", 
        "survey_handler.py", 
        "meditation_handler.py", 
        "conversation_handler.py",
        "reminder_handler.py",
        "voice_handler.py",
        "railway_logging.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        logger.info("Попытка найти файлы в других директориях...")
        
        # Поиск файлов в других директориях
        for root, dirs, files in os.walk("."):
            for file in missing_files[:]:
                if file in files:
                    src_path = os.path.join(root, file)
                    logger.info(f"Найден файл {file} в директории {root}")
                    
                    # Копируем файл в корневую директорию
                    try:
                        shutil.copy2(src_path, file)
                        logger.info(f"Файл {file} скопирован в корневую директорию")
                        missing_files.remove(file)
                    except Exception as e:
                        logger.error(f"Ошибка при копировании файла {file}: {e}")
    
    # Проверка оставшихся отсутствующих файлов
    if missing_files:
        logger.error(f"Не удалось найти следующие файлы: {', '.join(missing_files)}")
        create_placeholders_for_missing_files(missing_files)
    
    # Попытка импорта ключевых модулей
    try_import_modules()

def create_placeholders_for_missing_files(missing_files):
    """Создает заглушки для отсутствующих файлов."""
    for file in missing_files:
        try:
            module_name = file.replace(".py", "")
            with open(file, "w") as f:
                f.write(f"""# Placeholder module for {file}
import logging
logger = logging.getLogger(__name__)
logger.warning("This is a placeholder module created by fix_imports.py")

# Базовые импорты для совместимости
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Создаем роутер
{module_name}_router = Router(name="{module_name}")

# Базовые функции, необходимые для импорта в main.py
def get_main_keyboard():
    \"\"\"Заглушка для функции get_main_keyboard\"\"\"
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard

# Другие переменные, которые могут потребоваться
scheduler = None
""")
            logger.info(f"Создана заглушка для {file}")
        except Exception as e:
            logger.error(f"Ошибка при создании заглушки для {file}: {e}")

def try_import_modules():
    """Пытается импортировать ключевые модули."""
    modules_to_import = [
        "survey_handler", 
        "meditation_handler", 
        "conversation_handler",
        "reminder_handler",
        "voice_handler",
        "railway_logging"
    ]
    
    for module_name in modules_to_import:
        try:
            module = importlib.import_module(module_name)
            logger.info(f"Модуль {module_name} успешно импортирован")
        except ImportError as e:
            logger.error(f"Ошибка импорта модуля {module_name}: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при импорте {module_name}: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СКРИПТА ИСПРАВЛЕНИЯ ИМПОРТОВ ДЛЯ RAILWAY")
    print("=" * 50)
    
    check_environment()
    fix_imports()
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ СКРИПТА ИСПРАВЛЕНИЯ ИМПОРТОВ")
    print("=" * 50) 