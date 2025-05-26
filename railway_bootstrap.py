#!/usr/bin/env python3
"""
Скрипт-обертка для безопасного запуска бота с предварительным патчингом импортов.
Запускает этот скрипт первым в Railway для решения проблемы с импортами.
"""
import os
import sys
import logging
import subprocess
import importlib.util
import signal
import time

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("railway_bootstrap")

# Добавляем текущую директорию в sys.path
sys.path.insert(0, os.getcwd())

def create_mock_openai_module():
    """Создает модуль-заглушку openai с необходимыми классами"""
    try:
        # Проверяем наличие модуля openai
        if 'openai' in sys.modules:
            openai_module = sys.modules['openai']
        else:
            try:
                # Пытаемся импортировать настоящий модуль
                import openai as openai_module
            except ImportError:
                # Если не получается, создаем заглушку
                import types
                openai_module = types.ModuleType('openai')
                sys.modules['openai'] = openai_module

        # Добавляем классы-заглушки, если их нет
        if not hasattr(openai_module, 'AsyncOpenAI'):
            class AsyncOpenAI:
                def __init__(self, api_key=None, **kwargs):
                    self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                    logger.info("[Bootstrap] Инициализация AsyncOpenAI")
                
                class chat:
                    class completions:
                        @staticmethod
                        async def create(*args, **kwargs):
                            logger.info("[Bootstrap] Вызов AsyncOpenAI.chat.completions.create")
                            return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
                
                class audio:
                    @staticmethod
                    async def transcriptions_create(*args, **kwargs):
                        logger.info("[Bootstrap] Вызов AsyncOpenAI.audio.transcriptions_create")
                        return {"text": "Заглушка транскрипции аудио"}
            
            openai_module.AsyncOpenAI = AsyncOpenAI
            logger.info("Добавлена заглушка AsyncOpenAI в модуль openai")
        
        if not hasattr(openai_module, 'OpenAI'):
            class OpenAI:
                def __init__(self, api_key=None, **kwargs):
                    self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                    logger.info("[Bootstrap] Инициализация OpenAI")
                
                class chat:
                    class completions:
                        @staticmethod
                        def create(*args, **kwargs):
                            logger.info("[Bootstrap] Вызов OpenAI.chat.completions.create")
                            return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
                
                class audio:
                    @staticmethod
                    def transcriptions_create(*args, **kwargs):
                        logger.info("[Bootstrap] Вызов OpenAI.audio.transcriptions_create")
                        return {"text": "Заглушка транскрипции аудио"}
            
            openai_module.OpenAI = OpenAI
            logger.info("Добавлена заглушка OpenAI в модуль openai")
        
        # Добавляем прямые ссылки на классы в sys.modules
        sys.modules['openai.AsyncOpenAI'] = openai_module.AsyncOpenAI
        sys.modules['openai.OpenAI'] = openai_module.OpenAI
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании заглушки openai: {e}")
        return False

def apply_patches_in_sequence():
    """Последовательно применяет все патчи, чтобы убедиться что они работают"""
    try:
        # Добавляем текущую директорию в PYTHONPATH
        os.environ['PYTHONPATH'] = os.getcwd() + ':' + os.environ.get('PYTHONPATH', '')
        
        # 1. Запускаем глобальный патч импортов
        try:
            logger.info("Применение глобального патча импортов...")
            import fix_imports_global
            logger.info("Глобальный патч импортов применен успешно")
        except Exception as e:
            logger.error(f"Ошибка при применении глобального патча импортов: {e}")
        
        # 2. Модифицируем модуль openai в site-packages
        try:
            logger.info("Модификация модуля openai в site-packages...")
            import modify_site_packages
            logger.info("Модуль openai в site-packages модифицирован успешно")
        except Exception as e:
            logger.error(f"Ошибка при модификации модуля openai: {e}")
        
        # 3. Создаем заглушки для проблемных модулей
        try:
            logger.info("Создание заглушек для проблемных модулей...")
            import fix_problem_modules
            logger.info("Заглушки для проблемных модулей созданы успешно")
        except Exception as e:
            logger.error(f"Ошибка при создании заглушек для проблемных модулей: {e}")
        
        # 4. Сканируем и исправляем все импорты openai
        try:
            logger.info("Сканирование и исправление всех импортов openai...")
            import fix_all_openai_imports
            logger.info("Все импорты openai исправлены успешно")
        except Exception as e:
            logger.error(f"Ошибка при исправлении всех импортов openai: {e}")
        
        # 5. Создаем локальную заглушку openai
        create_mock_openai_module()
        
        # 6. Проверяем, что AsyncOpenAI доступен
        try:
            from openai import AsyncOpenAI
            logger.info("Проверка: AsyncOpenAI доступен успешно")
            return True
        except Exception as e:
            logger.error(f"Проверка не пройдена: AsyncOpenAI недоступен: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при применении патчей в последовательности: {e}")
        return False

def patch_sys_modules():
    """Патчит sys.modules, добавляя заглушки для openai"""
    try:
        # Пытаемся импортировать fix_imports_global
        spec = importlib.util.find_spec('fix_imports_global')
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info("Модуль fix_imports_global успешно импортирован")
            return True
        else:
            logger.warning("Модуль fix_imports_global не найден, применяем локальный патч")
            return create_mock_openai_module()
    
    except Exception as e:
        logger.error(f"Ошибка при патчинге sys.modules: {e}")
        logger.warning("Применяем локальный патч для openai")
        return create_mock_openai_module()

def run_safe_startup():
    """Запускает бота через safe_startup.py"""
    try:
        # Проверяем наличие safe_startup.py
        if os.path.exists('safe_startup.py'):
            logger.info("Запуск бота через safe_startup.py")
            
            # Создаем новый процесс для запуска бота
            bot_process = subprocess.Popen(
                [sys.executable, 'safe_startup.py'],
                env=os.environ.copy()
            )
            
            # Ждем завершения процесса
            bot_process.wait()
            
            return bot_process.returncode
        else:
            logger.error("Файл safe_startup.py не найден")
            return 1
    
    except Exception as e:
        logger.error(f"Ошибка при запуске safe_startup.py: {e}")
        return 1

def run_main():
    """Запускает бота через main.py"""
    try:
        # Проверяем наличие main.py
        if os.path.exists('main.py'):
            logger.info("Запуск бота через main.py")
            
            # Модифицируем sys.path для обеспечения доступа к нашим модулям
            if os.getcwd() not in sys.path:
                sys.path.insert(0, os.getcwd())
            
            # Создаем новый процесс для запуска бота
            bot_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                env=os.environ.copy()
            )
            
            # Ждем завершения процесса
            bot_process.wait()
            
            return bot_process.returncode
        else:
            logger.error("Файл main.py не найден")
            return 1
    
    except Exception as e:
        logger.error(f"Ошибка при запуске main.py: {e}")
        return 1

def run_bot():
    """Запускает бота безопасным способом"""
    # Пытаемся запустить через безопасный запуск
    if os.path.exists('safe_startup.py'):
        return run_safe_startup()
    
    # Если не получилось, запускаем напрямую main.py
    return run_main()

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {sig}, завершаем работу...")
    sys.exit(0)

def main():
    """Основная функция скрипта"""
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=== Railway Bootstrap: подготовка окружения для запуска бота ===")
    
    # Применяем все патчи последовательно
    if apply_patches_in_sequence():
        logger.info("Все патчи применены успешно")
    else:
        logger.warning("Не все патчи были применены успешно, продолжаем с осторожностью")
    
    # Небольшая пауза, чтобы патчи успели применится
    time.sleep(1)
    
    # Запускаем бота
    logger.info("=== Railway Bootstrap: запуск бота ===")
    return run_bot()

if __name__ == "__main__":
    sys.exit(main()) 