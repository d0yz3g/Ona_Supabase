#!/usr/bin/env python
"""
Вспомогательный модуль для обеспечения корректной работы бота в Railway.
Предоставляет функции для инициализации, проверки и восстановления модулей.
"""

import os
import sys
import importlib
import logging
import pkgutil
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RAILWAY_HELPER] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("railway_helper")

class RailwayHelper:
    """
    Класс для помощи в работе с Railway.
    Обеспечивает корректную инициализацию и работу бота в Railway.
    """
    
    def __init__(self):
        """
        Инициализация Railway Helper.
        """
        self.is_railway = os.environ.get('RAILWAY_ENVIRONMENT', '') != ''
        logger.info(f"Railway Environment: {'Да' if self.is_railway else 'Нет'}")
        
        # Добавляем текущую директорию в sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logger.info(f"Добавлен путь {current_dir} в sys.path")
    
    def check_environment(self) -> Dict[str, Any]:
        """
        Проверяет окружение Railway и возвращает информацию о нем.
        
        Returns:
            Dict[str, Any]: Информация об окружении
        """
        env_info = {
            "is_railway": self.is_railway,
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "sys_path": sys.path,
            "environment_variables": {k: v for k, v in os.environ.items() if not k.startswith('_')},
            "python_modules": [m for m, _ in pkgutil.iter_modules()]
        }
        
        logger.info(f"Текущая директория: {env_info['working_directory']}")
        logger.info(f"Python версия: {env_info['python_version']}")
        
        return env_info
    
    def check_modules(self, required_modules: List[str]) -> Dict[str, bool]:
        """
        Проверяет наличие необходимых модулей.
        
        Args:
            required_modules: Список необходимых модулей
            
        Returns:
            Dict[str, bool]: Словарь с результатами проверки
        """
        results = {}
        
        for module_name in required_modules:
            try:
                module = importlib.import_module(module_name)
                results[module_name] = True
                logger.info(f"Модуль {module_name} успешно импортирован")
            except ImportError as e:
                results[module_name] = False
                logger.error(f"Ошибка импорта модуля {module_name}: {e}")
        
        return results
    
    def create_placeholder_router(self, module_name: str) -> None:
        """
        Создает заглушку для роутера модуля.
        
        Args:
            module_name: Имя модуля
        """
        file_name = f"{module_name}.py"
        
        if os.path.exists(file_name):
            logger.info(f"Файл {file_name} уже существует, пропуск создания заглушки")
            return
        
        try:
            with open(file_name, "w") as f:
                f.write(f"""# Placeholder module for {file_name} created by railway_helper.py
import logging
from aiogram import Router

logger = logging.getLogger(__name__)
{module_name}_router = Router(name="{module_name}")

# Minimal functions required by main.py
def get_main_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
        ],
        resize_keyboard=True
    )

# Additional variables
scheduler = None
""")
            logger.info(f"Заглушка для {file_name} успешно создана")
        except Exception as e:
            logger.error(f"Ошибка при создании заглушки для {file_name}: {e}")
    
    def ensure_modules_available(self, modules: List[str]) -> None:
        """
        Обеспечивает доступность всех необходимых модулей.
        Создает заглушки для отсутствующих модулей.
        
        Args:
            modules: Список необходимых модулей
        """
        for module_name in modules:
            try:
                # Пытаемся импортировать модуль
                importlib.import_module(module_name)
                logger.info(f"Модуль {module_name} уже доступен")
            except ImportError:
                # Если не получается, создаем заглушку
                logger.warning(f"Модуль {module_name} не найден, создаем заглушку")
                self.create_placeholder_router(module_name)
                
                # Пытаемся импортировать созданную заглушку
                try:
                    importlib.import_module(module_name)
                    logger.info(f"Заглушка для модуля {module_name} успешно импортирована")
                except ImportError as e:
                    logger.error(f"Не удалось импортировать заглушку для модуля {module_name}: {e}")
    
    @staticmethod
    def print_railway_info(message: str, level: str = "INFO") -> None:
        """
        Выводит информацию в Railway-friendly формате.
        
        Args:
            message: Сообщение для вывода
            level: Уровень сообщения (INFO, ERROR, WARNING, DEBUG)
        """
        prefix = "ИНФО"
        if level.upper() == "ERROR":
            prefix = "ОШИБКА"
        elif level.upper() == "WARNING":
            prefix = "ПРЕДУПРЕЖДЕНИЕ"
        elif level.upper() == "DEBUG":
            prefix = "ОТЛАДКА"
        
        print(f"{prefix}: {message}")
        sys.stdout.flush()

# Создаем глобальный экземпляр Railway Helper
railway_helper = RailwayHelper()

# Экспортируем функции для удобного использования
check_environment = railway_helper.check_environment
check_modules = railway_helper.check_modules
ensure_modules_available = railway_helper.ensure_modules_available
print_railway_info = railway_helper.print_railway_info

if __name__ == "__main__":
    # Если запущен напрямую, выполняем инициализацию
    print("=" * 50)
    print("ЗАПУСК RAILWAY HELPER")
    print("=" * 50)
    
    env_info = railway_helper.check_environment()
    
    print_railway_info(f"Python версия: {env_info['python_version']}")
    print_railway_info(f"Рабочая директория: {env_info['working_directory']}")
    
    # Проверяем и обеспечиваем наличие необходимых модулей
    required_modules = [
        "survey_handler",
        "meditation_handler",
        "conversation_handler",
        "reminder_handler",
        "voice_handler"
    ]
    
    ensure_modules_available(required_modules)
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ RAILWAY HELPER")
    print("=" * 50) 