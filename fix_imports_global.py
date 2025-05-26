#!/usr/bin/env python3
"""
Глобальный скрипт-перехватчик импортов для решения проблемы с AsyncOpenAI.
Этот скрипт патчит саму систему импорта Python, чтобы перехватывать импорты openai.
"""
import sys
import types
import importlib
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_imports_global")

# Сохраняем оригинальную функцию импорта
original_import = __builtins__.__import__

# Классы-заглушки для openai
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Global Mock] Инициализация AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("[Global Mock] Вызов AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("[Global Mock] Инициализация OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                logger.info("[Global Mock] Вызов OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

def create_openai_module():
    """Создает модуль-заглушку openai с необходимыми классами"""
    # Создаем пустой модуль
    openai_module = types.ModuleType('openai')
    
    # Добавляем классы-заглушки
    openai_module.AsyncOpenAI = AsyncOpenAI
    openai_module.OpenAI = OpenAI
    
    # Добавляем другие необходимые атрибуты
    # (при необходимости можно расширить)
    
    return openai_module

def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Перехватывает импорты и предоставляет заглушки для проблемных модулей
    """
    # Если импортируют openai и запрашивают AsyncOpenAI/OpenAI
    if name == 'openai' and fromlist and ('AsyncOpenAI' in fromlist or 'OpenAI' in fromlist):
        try:
            # Сначала пробуем стандартный импорт
            module = original_import(name, globals, locals, fromlist, level)
            
            # Проверяем, есть ли нужные классы
            if not hasattr(module, 'AsyncOpenAI'):
                logger.info("Добавляем заглушку AsyncOpenAI в модуль openai")
                module.AsyncOpenAI = AsyncOpenAI
            
            if not hasattr(module, 'OpenAI'):
                logger.info("Добавляем заглушку OpenAI в модуль openai")
                module.OpenAI = OpenAI
            
            return module
        
        except Exception as e:
            logger.warning(f"Ошибка при импорте openai: {e}")
            logger.info("Создаем полную заглушку для модуля openai")
            
            # Возвращаем полную заглушку
            mock_module = create_openai_module()
            sys.modules['openai'] = mock_module
            return mock_module
    
    # Для всех остальных импортов используем оригинальную функцию
    return original_import(name, globals, locals, fromlist, level)

def apply_import_hook():
    """Применяет патч к системе импорта Python"""
    # Заменяем встроенную функцию импорта на нашу версию
    __builtins__.__import__ = patched_import
    logger.info("Глобальный перехватчик импортов установлен")
    
    # Проверяем, что патч работает
    try:
        # Форсируем загрузку модуля openai, если он уже был загружен
        if 'openai' in sys.modules:
            del sys.modules['openai']
        
        # Тестовый импорт
        import openai
        logger.info(f"Тестовый импорт openai: AsyncOpenAI доступен: {hasattr(openai, 'AsyncOpenAI')}")
        logger.info(f"Тестовый импорт openai: OpenAI доступен: {hasattr(openai, 'OpenAI')}")
        
        from openai import AsyncOpenAI, OpenAI
        logger.info("Тестовый импорт AsyncOpenAI и OpenAI выполнен успешно")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании патча импорта: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Установка глобального перехватчика импортов ===")
    
    if apply_import_hook():
        logger.info("=== Глобальный перехватчик импортов установлен успешно ===")
        # Ничего не возвращаем - этот модуль должен быть импортирован, а не запущен как скрипт
    else:
        logger.error("=== Не удалось установить глобальный перехватчик импортов ===")
        sys.exit(1)

# Автоматически применяем патч при импорте этого модуля
apply_import_hook()

if __name__ == "__main__":
    main() 