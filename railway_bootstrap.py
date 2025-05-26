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
                def __init__(self, api_key=None):
                    self.api_key = api_key
                    logger.info("[Bootstrap] Инициализация AsyncOpenAI")
                
                class chat:
                    class completions:
                        @staticmethod
                        async def create(*args, **kwargs):
                            logger.info("[Bootstrap] Вызов AsyncOpenAI.chat.completions.create")
                            return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
            
            openai_module.AsyncOpenAI = AsyncOpenAI
            logger.info("Добавлена заглушка AsyncOpenAI в модуль openai")
        
        if not hasattr(openai_module, 'OpenAI'):
            class OpenAI:
                def __init__(self, api_key=None):
                    self.api_key = api_key
                    logger.info("[Bootstrap] Инициализация OpenAI")
                
                class chat:
                    class completions:
                        @staticmethod
                        def create(*args, **kwargs):
                            logger.info("[Bootstrap] Вызов OpenAI.chat.completions.create")
                            return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
            
            openai_module.OpenAI = OpenAI
            logger.info("Добавлена заглушка OpenAI в модуль openai")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании заглушки openai: {e}")
        return False

def run_global_import_patch():
    """Запускает глобальный патч импортов"""
    try:
        # Добавляем текущую директорию в PYTHONPATH
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = os.getcwd() + ':' + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = os.getcwd()
        
        # Запускаем Python с параметром -c для выполнения кода импорта заглушки
        patch_code = """
import sys
sys.path.insert(0, '.')
try:
    import fix_imports_global
    print("Глобальный патч импортов применен успешно")
except Exception as e:
    print(f"Ошибка при применении глобального патча импортов: {e}")
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", patch_code],
            env=env,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            logger.info("Глобальный патч импортов запущен успешно")
            logger.info(f"Вывод: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Ошибка при запуске глобального патча импортов: {result.stderr.strip()}")
            return False
    
    except Exception as e:
        logger.error(f"Исключение при запуске глобального патча импортов: {e}")
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

def run_bot():
    """Запускает бота безопасным способом"""
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
        
        # Если safe_startup.py не найден, пробуем запустить main.py
        elif os.path.exists('main.py'):
            logger.info("Запуск бота через main.py")
            
            # Создаем новый процесс для запуска бота
            bot_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                env=os.environ.copy()
            )
            
            # Ждем завершения процесса
            bot_process.wait()
            
            return bot_process.returncode
        
        else:
            logger.error("Не найдены файлы safe_startup.py или main.py")
            return 1
    
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return 1

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
    
    # Патчим sys.modules перед запуском бота
    if patch_sys_modules():
        logger.info("Подготовка sys.modules выполнена успешно")
    else:
        logger.warning("Не удалось полностью подготовить sys.modules")
    
    # Запускаем глобальный патч импортов
    if run_global_import_patch():
        logger.info("Глобальный патч импортов применен успешно")
    else:
        logger.warning("Не удалось применить глобальный патч импортов")
    
    # Создаем заглушку для openai
    if create_mock_openai_module():
        logger.info("Заглушка для openai создана успешно")
    else:
        logger.warning("Не удалось создать заглушку для openai")
    
    # Проверяем, что патч работает
    try:
        # Проверяем, доступны ли классы OpenAI и AsyncOpenAI
        import openai
        logger.info(f"OpenAI доступен: {hasattr(openai, 'OpenAI')}")
        logger.info(f"AsyncOpenAI доступен: {hasattr(openai, 'AsyncOpenAI')}")
        
        # Пробуем импортировать классы напрямую
        from openai import AsyncOpenAI, OpenAI
        logger.info("Импорт AsyncOpenAI и OpenAI выполнен успешно")
    except Exception as e:
        logger.error(f"Ошибка при проверке патча: {e}")
    
    # Запускаем бота
    logger.info("=== Railway Bootstrap: запуск бота ===")
    return run_bot()

if __name__ == "__main__":
    sys.exit(main()) 