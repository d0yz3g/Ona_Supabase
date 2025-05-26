#!/usr/bin/env python3
"""
Альтернативный метод запуска для Railway без Docker.
Выполняет все необходимые исправления и запускает бота напрямую из Python.
"""
import os
import sys
import logging
import subprocess
import threading
import time

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("run_railway")

def setup_paths():
    """Добавляет текущую директорию в sys.path"""
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        logger.info(f"Добавлен {os.getcwd()} в sys.path")

def install_dependencies():
    """Устанавливает зависимости"""
    try:
        logger.info("Установка критических зависимостей...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--force-reinstall",
            "python-dotenv==1.0.0", "httpx==0.23.3", "openai==1.3.3", 
            "pydantic==2.1.1", "aiogram==3.0.0"
        ], check=True)
        
        logger.info("Установка зависимостей из requirements.txt...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=False)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке зависимостей: {e}")
        return False

def run_healthcheck_server():
    """Запускает сервер для health check"""
    try:
        # Импортируем модуль
        import healthcheck
        
        # Запускаем сервер в отдельном потоке
        thread = healthcheck.run_in_thread()
        logger.info("Health check сервер запущен успешно")
        return thread
    except Exception as e:
        logger.error(f"Ошибка при запуске health check сервера: {e}")
        return None

def patch_main_file():
    """Патчит файл main.py"""
    try:
        # Импортируем модуль
        import patch_main
        
        # Патчим файл
        if patch_main.patch_main_py():
            logger.info("Файл main.py успешно пропатчен")
            return True
        else:
            logger.error("Не удалось пропатчить файл main.py")
            return False
    except Exception as e:
        logger.error(f"Ошибка при патчинге main.py: {e}")
        return False

def run_bot():
    """Запускает бота"""
    try:
        # Импортируем pre_import_fix перед импортом main
        import pre_import_fix
        logger.info("pre_import_fix успешно импортирован")
        
        # Устанавливаем переменную окружения для Railway
        os.environ["RAILWAY_ENV"] = "1"
        
        # Запускаем main
        import main
        logger.info("Бот успешно запущен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return False

def run_alternative_bot():
    """Запускает бота альтернативным способом"""
    try:
        # Импортируем pre_import_fix перед импортом bootstrap
        import pre_import_fix
        logger.info("pre_import_fix успешно импортирован")
        
        # Устанавливаем переменную окружения для Railway
        os.environ["RAILWAY_ENV"] = "1"
        
        # Запускаем bootstrap
        import railway_bootstrap
        logger.info("Бот успешно запущен через bootstrap")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота через bootstrap: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Запуск бота на Railway ===")
    
    # Устанавливаем пути
    setup_paths()
    
    # Устанавливаем зависимости
    if not install_dependencies():
        logger.warning("Были проблемы при установке зависимостей, но продолжаем запуск")
    
    # Запускаем health check сервер
    health_thread = run_healthcheck_server()
    
    # Патчим main.py
    patch_main_file()
    
    # Пробуем запустить бота
    if not run_bot():
        logger.warning("Не удалось запустить бота напрямую, пробуем через bootstrap")
        if not run_alternative_bot():
            logger.error("Не удалось запустить бота ни одним из способов")
            return 1
    
    # Ждем завершения работы
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения, останавливаем процессы")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 