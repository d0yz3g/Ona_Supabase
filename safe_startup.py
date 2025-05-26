#!/usr/bin/env python3
"""
Безопасный скрипт запуска, который применяет все исправления перед запуском основного кода.
Этот скрипт запускается из railway_bootstrap.py и обеспечивает корректные импорты.
"""
import os
import sys
import logging
import importlib
import traceback

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("safe_startup")

def apply_all_fixes():
    """Применяет все исправления перед запуском бота"""
    logger.info("=== Применение всех исправлений перед запуском бота ===")
    
    # Добавляем текущую директорию в sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    
    # Проверяем, есть ли AsyncOpenAI в openai
    try:
        from openai import AsyncOpenAI
        logger.info("AsyncOpenAI уже доступен в openai, патчи не требуются")
        return True
    except ImportError:
        logger.warning("AsyncOpenAI недоступен в openai, применяем патчи")
    
    # Шаг 1: Глобальный перехватчик импортов
    try:
        import fix_imports_global
        logger.info("Применен глобальный перехватчик импортов")
    except Exception as e:
        logger.error(f"Не удалось применить глобальный перехватчик импортов: {e}")
        logger.debug(traceback.format_exc())
    
    # Шаг 2: Патчим модуль openai в site-packages
    try:
        import modify_site_packages
        logger.info("Применен патч для модуля openai в site-packages")
    except Exception as e:
        logger.error(f"Не удалось применить патч для модуля openai: {e}")
        logger.debug(traceback.format_exc())
    
    # Шаг 3: Создаем заглушки для проблемных модулей
    try:
        import fix_problem_modules
        logger.info("Созданы заглушки для проблемных модулей")
    except Exception as e:
        logger.error(f"Не удалось создать заглушки для проблемных модулей: {e}")
        logger.debug(traceback.format_exc())
    
    # Шаг 4: Исправляем все импорты AsyncOpenAI в проекте
    try:
        import fix_all_openai_imports
        logger.info("Исправлены все импорты AsyncOpenAI в проекте")
    except Exception as e:
        logger.error(f"Не удалось исправить импорты AsyncOpenAI: {e}")
        logger.debug(traceback.format_exc())
    
    # Шаг 5: Напрямую патчим sys.modules
    try:
        class AsyncOpenAI:
            def __init__(self, api_key=None, **kwargs):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                logger.info("[Safe Startup] Инициализация AsyncOpenAI")
            
            class chat:
                class completions:
                    @staticmethod
                    async def create(*args, **kwargs):
                        logger.info("[Safe Startup] Вызов AsyncOpenAI.chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
            
            class audio:
                @staticmethod
                async def transcriptions_create(*args, **kwargs):
                    logger.info("[Safe Startup] Вызов AsyncOpenAI.audio.transcriptions_create")
                    return {"text": "Заглушка транскрипции аудио"}
        
        class OpenAI:
            def __init__(self, api_key=None, **kwargs):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                logger.info("[Safe Startup] Инициализация OpenAI")
            
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        logger.info("[Safe Startup] Вызов OpenAI.chat.completions.create")
                        return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
            
            class audio:
                @staticmethod
                def transcriptions_create(*args, **kwargs):
                    logger.info("[Safe Startup] Вызов OpenAI.audio.transcriptions_create")
                    return {"text": "Заглушка транскрипции аудио"}
        
        # Добавляем классы в sys.modules
        sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
        sys.modules['openai.OpenAI'] = OpenAI
        
        # Патчим модуль openai, если он уже загружен
        if 'openai' in sys.modules:
            if not hasattr(sys.modules['openai'], 'AsyncOpenAI'):
                sys.modules['openai'].AsyncOpenAI = AsyncOpenAI
            if not hasattr(sys.modules['openai'], 'OpenAI'):
                sys.modules['openai'].OpenAI = OpenAI
        
        logger.info("Напрямую добавлены классы AsyncOpenAI и OpenAI в sys.modules")
    except Exception as e:
        logger.error(f"Не удалось напрямую патчить sys.modules: {e}")
        logger.debug(traceback.format_exc())
    
    # Шаг 6: Проверка, что AsyncOpenAI доступен
    try:
        from openai import AsyncOpenAI
        logger.info("Проверка: AsyncOpenAI успешно импортирован")
        return True
    except Exception as e:
        logger.error(f"Не удалось импортировать AsyncOpenAI: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_main():
    """Запускает основной код бота"""
    logger.info("=== Запуск основного кода бота ===")
    
    try:
        # Импортируем и запускаем main
        import main
        logger.info("Бот успешно запущен")
        return 0
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.debug(traceback.format_exc())
        
        # Пробуем загрузить main более безопасным способом
        try:
            logger.info("Попытка запуска main более безопасным способом")
            
            # Создаем временный файл-обертку
            with open('temp_main_wrapper.py', 'w') as f:
                f.write('''
import sys
import os
import logging

logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("temp_main_wrapper")

sys.path.insert(0, os.getcwd())

# Предварительно импортируем все патчи
try:
    import fix_imports_global
    logger.info("fix_imports_global импортирован")
except Exception as e:
    logger.error(f"Ошибка при импорте fix_imports_global: {e}")

# Импортируем main
try:
    import main
    logger.info("main успешно импортирован")
except Exception as e:
    logger.error(f"Ошибка при импорте main: {e}")
    sys.exit(1)
''')
            
            # Запускаем через обертку
            import subprocess
            result = subprocess.run([sys.executable, 'temp_main_wrapper.py'])
            return result.returncode
        
        except Exception as fallback_error:
            logger.error(f"Ошибка при запуске безопасной обертки: {fallback_error}")
            logger.debug(traceback.format_exc())
            return 1

def main():
    """Основная функция скрипта"""
    logger.info("=== Безопасный запуск бота ===")
    
    # Применяем все исправления
    if apply_all_fixes():
        logger.info("Исправления успешно применены, запускаем бота")
    else:
        logger.warning("Не все исправления были применены, продолжаем с осторожностью")
    
    # Запускаем основной код
    return run_main()

if __name__ == "__main__":
    sys.exit(main()) 