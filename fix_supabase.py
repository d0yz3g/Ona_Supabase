#!/usr/bin/env python
"""Скрипт для проверки и исправления проблем с Supabase в Railway."""

import os
import sys
import subprocess
import logging
import importlib
from typing import List, Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [SUPABASE_FIX] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase_fix")

def check_supabase_module() -> bool:
    """
    Проверяет наличие модуля supabase.
    
    Returns:
        bool: True если модуль установлен, False в противном случае
    """
    try:
        import supabase
        logger.info(f"✅ Модуль supabase установлен (версия: {supabase.__version__})")
        return True
    except ImportError as e:
        logger.error(f"❌ Модуль supabase не установлен: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке модуля supabase: {e}")
        return False

def install_supabase() -> bool:
    """
    Устанавливает модуль supabase-py.
    
    Returns:
        bool: True если установка прошла успешно, False в противном случае
    """
    try:
        logger.info("Установка модуля supabase-py...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase-py==2.3.1"])
        logger.info("✅ Модуль supabase-py успешно установлен")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Ошибка при установке модуля supabase-py: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при установке модуля supabase-py: {e}")
        return False

def check_dependencies() -> Dict[str, bool]:
    """
    Проверяет наличие всех зависимостей для работы с Supabase.
    
    Returns:
        Dict[str, bool]: Словарь с результатами проверки зависимостей
    """
    dependencies = {
        "supabase-py": False,
        "httpx": False,
        "postgrest-py": False,
        "python-dotenv": False,
        "storage3": False,
        "gotrue": False,
        "realtime": False
    }
    
    for dependency in dependencies:
        try:
            module = importlib.import_module(dependency.replace("-py", ""))
            dependencies[dependency] = True
            logger.info(f"✅ Зависимость {dependency} найдена")
        except ImportError:
            logger.warning(f"❌ Зависимость {dependency} не найдена")
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке зависимости {dependency}: {e}")
    
    return dependencies

def install_missing_dependencies(dependencies: Dict[str, bool]) -> bool:
    """
    Устанавливает отсутствующие зависимости.
    
    Args:
        dependencies: Словарь с результатами проверки зависимостей
        
    Returns:
        bool: True если все зависимости установлены успешно, False в противном случае
    """
    all_success = True
    
    for dependency, installed in dependencies.items():
        if not installed:
            try:
                logger.info(f"Установка зависимости {dependency}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
                logger.info(f"✅ Зависимость {dependency} успешно установлена")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Ошибка при установке зависимости {dependency}: {e}")
                all_success = False
            except Exception as e:
                logger.error(f"❌ Неизвестная ошибка при установке зависимости {dependency}: {e}")
                all_success = False
    
    return all_success

def check_env_variables() -> Dict[str, bool]:
    """
    Проверяет наличие переменных окружения для Supabase.
    
    Returns:
        Dict[str, bool]: Словарь с результатами проверки переменных окружения
    """
    env_vars = {
        "SUPABASE_URL": False,
        "SUPABASE_KEY": False
    }
    
    for var in env_vars:
        if os.getenv(var):
            env_vars[var] = True
            # Не выводим значение, чтобы не раскрывать API ключ
            logger.info(f"✅ Переменная окружения {var} найдена")
        else:
            logger.warning(f"❌ Переменная окружения {var} не найдена")
    
    return env_vars

def check_supabase_connection() -> bool:
    """
    Проверяет подключение к Supabase.
    
    Returns:
        bool: True если подключение успешно, False в противном случае
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Не заданы переменные окружения SUPABASE_URL и/или SUPABASE_KEY")
        return False
    
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        
        # Проверяем подключение запросом к основной таблице
        response = client.table("user_profiles").select("id").limit(1).execute()
        
        logger.info("✅ Успешное подключение к Supabase")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при подключении к Supabase: {e}")
        return False

def main():
    """
    Основная функция скрипта.
    """
    logger.info("=== ПРОВЕРКА И ИСПРАВЛЕНИЕ ПРОБЛЕМ С SUPABASE ===")
    
    # Проверяем наличие модуля supabase
    supabase_installed = check_supabase_module()
    
    # Если модуль не установлен, пытаемся установить его
    if not supabase_installed:
        install_success = install_supabase()
        if install_success:
            logger.info("✅ Модуль supabase-py успешно установлен")
        else:
            logger.error("❌ Не удалось установить модуль supabase-py")
            # Проверяем зависимости даже если не удалось установить модуль напрямую
    
    # Проверяем зависимости
    dependencies = check_dependencies()
    all_dependencies_installed = all(dependencies.values())
    
    # Если не все зависимости установлены, пытаемся установить их
    if not all_dependencies_installed:
        install_success = install_missing_dependencies(dependencies)
        if install_success:
            logger.info("✅ Все зависимости успешно установлены")
        else:
            logger.error("❌ Не удалось установить все зависимости")
    
    # Проверяем переменные окружения
    env_vars = check_env_variables()
    all_env_vars_set = all(env_vars.values())
    
    if not all_env_vars_set:
        logger.error("❌ Не все переменные окружения для Supabase заданы")
        logger.error("   Задайте переменные SUPABASE_URL и SUPABASE_KEY в Railway Dashboard или .env файле")
    else:
        # Проверяем подключение к Supabase
        connection_ok = check_supabase_connection()
        if connection_ok:
            logger.info("✅ Подключение к Supabase работает корректно")
        else:
            logger.error("❌ Не удалось подключиться к Supabase")
            logger.error("   Проверьте правильность переменных SUPABASE_URL и SUPABASE_KEY")
    
    # Проверяем снова наличие модуля supabase после всех исправлений
    if not supabase_installed:
        supabase_installed = check_supabase_module()
        if supabase_installed:
            logger.info("✅ Модуль supabase-py успешно установлен после исправлений")
        else:
            logger.error("❌ Модуль supabase-py не удалось установить")
    
    # Выводим итоговый статус
    if supabase_installed and all_dependencies_installed and all_env_vars_set:
        logger.info("✅ Все проверки прошли успешно, Supabase должен работать корректно")
        return 0
    else:
        logger.error("❌ Не все проверки прошли успешно, могут быть проблемы с Supabase")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 