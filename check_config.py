#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед запуском бота.
Проверяет наличие всех необходимых модулей и переменных окружения.
"""
import os
import sys
import logging
import importlib
import subprocess

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [CONFIG_CHECK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("config_check")

# Список необходимых переменных окружения
REQUIRED_ENV_VARS = [
    "BOT_TOKEN"
]

# Список необходимых модулей
REQUIRED_MODULES = [
    ("aiogram", "3.0.0", True),  # (название, версия, обязательный)
    ("pydantic", "1.10.12", True),
    ("openai", "0.28.1", True),
    ("httpx", None, True),
    ("python-dotenv", None, False),  # Для этого есть fallback
    ("APScheduler", None, True)
]

def check_env_vars():
    """Проверяет наличие необходимых переменных окружения"""
    logger.info("Проверка переменных окружения...")
    missing_vars = []
    
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
            logger.error(f"❌ Переменная окружения {var} не задана")
        else:
            logger.info(f"✅ Переменная окружения {var} задана")
    
    return len(missing_vars) == 0

def is_module_installed(module_name):
    """Проверяет, установлен ли модуль"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False

def install_package(package_name, version=None):
    """Устанавливает пакет через pip"""
    package_str = f"{package_name}=={version}" if version else package_name
    logger.info(f"Установка пакета {package_str}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", package_str])
        logger.info(f"✅ Успешно установлен пакет {package_str}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Не удалось установить пакет {package_str}: {e}")
        return False

def check_modules():
    """Проверяет наличие необходимых модулей и пытается установить отсутствующие"""
    logger.info("Проверка наличия необходимых модулей...")
    all_required_available = True
    
    for module, version, required in REQUIRED_MODULES:
        # Для python-dotenv используем специальное имя модуля
        module_import_name = "dotenv" if module == "python-dotenv" else module
        
        if is_module_installed(module_import_name):
            logger.info(f"✅ Модуль {module} доступен")
        else:
            logger.warning(f"⚠️ Модуль {module} не установлен")
            if install_package(module, version):
                logger.info(f"✅ Модуль {module} успешно установлен")
            elif required:
                all_required_available = False
                logger.error(f"❌ Не удалось установить обязательный модуль {module}")
            else:
                logger.warning(f"⚠️ Не удалось установить необязательный модуль {module}")
    
    return all_required_available

def check_fallbacks():
    """Проверяет и создает fallback-реализации для отсутствующих модулей"""
    logger.info("Проверка fallback-модулей...")
    
    # Проверяем и создаем fallback для python-dotenv
    if not is_module_installed("dotenv"):
        logger.warning("⚠️ Модуль dotenv не найден, проверка fallback...")
        
        if os.path.exists("dotenv.py") or os.path.exists("dotenv_fallback.py"):
            logger.info("✅ Fallback для dotenv найден")
        else:
            logger.warning("⚠️ Создание fallback для dotenv...")
            try:
                with open("dotenv_minimal.py", "w") as f:
                    f.write("""
import os

def load_dotenv(dotenv_path=None, **kwargs):
    print("[dotenv_minimal] Using minimal implementation")
    return True

def find_dotenv(*args, **kwargs):
    return '.env' if os.path.exists('.env') else ''
""")
                logger.info("✅ Создан fallback для dotenv")
            except Exception as e:
                logger.error(f"❌ Не удалось создать fallback для dotenv: {e}")
    
    # Проверяем и создаем fallback для openai
    if not is_module_installed("openai"):
        logger.warning("⚠️ Модуль openai не найден, проверка fallback...")
        
        if os.path.exists("openai_fallback.py"):
            logger.info("✅ Fallback для openai найден")
        else:
            try:
                # Запускаем скрипт создания fallback
                if os.path.exists("fix_imports.py"):
                    logger.info("Запуск fix_imports.py для создания fallback...")
                    subprocess.call([sys.executable, "fix_imports.py"])
                    logger.info("✅ Запущен fix_imports.py")
                else:
                    logger.error("❌ Файл fix_imports.py не найден")
            except Exception as e:
                logger.error(f"❌ Не удалось создать fallback для openai: {e}")
    
    # Проверяем заглушки для обработчиков
    handlers = ["survey_handler.py", "conversation_handler.py", "voice_handler.py", 
                "meditation_handler.py", "reminder_handler.py", "communication_handler.py"]
    
    for handler in handlers:
        if not os.path.exists(handler):
            logger.warning(f"⚠️ Файл {handler} не найден")
            try:
                # Запускаем скрипт создания заглушек
                if os.path.exists("create_placeholders.py"):
                    logger.info("Запуск create_placeholders.py для создания заглушек...")
                    subprocess.call([sys.executable, "create_placeholders.py"])
                    logger.info("✅ Запущен create_placeholders.py")
                    break  # Запускаем скрипт только один раз
                else:
                    logger.error("❌ Файл create_placeholders.py не найден")
            except Exception as e:
                logger.error(f"❌ Не удалось создать заглушки: {e}")
            break  # Проверяем только первый отсутствующий файл

def main():
    """Основная функция проверки конфигурации"""
    logger.info("=== Проверка конфигурации перед запуском бота ===")
    
    # Проверка переменных окружения
    env_ok = check_env_vars()
    if not env_ok:
        logger.error("❌ Не все необходимые переменные окружения заданы")
    
    # Проверка модулей
    modules_ok = check_modules()
    if not modules_ok:
        logger.warning("⚠️ Не все необходимые модули доступны")
    
    # Проверка и создание fallback-модулей
    check_fallbacks()
    
    # Вывод результата
    if env_ok and modules_ok:
        logger.info("✅ Все проверки пройдены успешно")
        return 0
    else:
        logger.warning("⚠️ Не все проверки пройдены, но бот будет запущен с ограниченной функциональностью")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 