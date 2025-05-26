#!/usr/bin/env python3
"""
Прямой запуск бота без дополнительных проверок.
Обеспечивает, что процесс никогда не завершится даже при ошибках.
"""
import os
import sys
import time
import logging
import importlib
import subprocess
import traceback

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("direct_start")

def setup_paths():
    """Добавляет текущую директорию в sys.path"""
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        logger.info(f"Добавлен {os.getcwd()} в sys.path")

def import_modules():
    """Пытается импортировать критические модули"""
    try:
        # Импортируем pre_import_fix перед всем остальным
        import pre_import_fix
        logger.info("✅ pre_import_fix импортирован успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте pre_import_fix: {e}")
        return False

def run_bot_directly():
    """Запускает бота напрямую через импорт main"""
    try:
        # Устанавливаем переменную окружения для Railway
        os.environ["RAILWAY_ENV"] = "1"
        
        # Импортируем main
        import main
        logger.info("✅ Бот запущен успешно через main")
        
        # Ждем бесконечно, чтобы процесс не завершился
        while True:
            time.sleep(3600)  # Ждем час и повторяем
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота через main: {e}")
        logger.error(traceback.format_exc())
        return False

def run_bot_subprocess():
    """Запускает бота в отдельном процессе"""
    try:
        # Устанавливаем переменную окружения для Railway
        env = os.environ.copy()
        env["RAILWAY_ENV"] = "1"
        
        # Запускаем бота через subprocess
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Читаем и логируем вывод
        logger.info(f"✅ Бот запущен в отдельном процессе (PID: {process.pid})")
        
        # Читаем вывод в реальном времени
        for line in process.stdout:
            logger.info(f"BOT: {line.strip()}")
        
        # Ждем завершения процесса
        returncode = process.wait()
        logger.error(f"❌ Процесс бота завершился с кодом {returncode}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота через subprocess: {e}")
        return False

def run_bootstrap():
    """Запускает бота через bootstrap"""
    try:
        # Устанавливаем переменную окружения для Railway
        os.environ["RAILWAY_ENV"] = "1"
        
        # Импортируем bootstrap
        import railway_bootstrap
        logger.info("✅ Бот запущен успешно через bootstrap")
        
        # Ждем бесконечно, чтобы процесс не завершился
        while True:
            time.sleep(3600)  # Ждем час и повторяем
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота через bootstrap: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Основная функция, запускает бота и поддерживает процесс живым"""
    logger.info("=== Прямой запуск бота на Railway ===")
    
    # Устанавливаем пути
    setup_paths()
    
    # Импортируем критические модули
    import_result = import_modules()
    
    # Пробуем разные способы запуска бота
    while True:
        try:
            if import_result:
                # Если импортировать pre_import_fix удалось, запускаем напрямую
                run_bot_directly()
            else:
                # Иначе пробуем через bootstrap
                run_bootstrap()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            logger.error(traceback.format_exc())
        
        # Ждем перед повторной попыткой
        logger.info("⚠️ Перезапуск бота через 5 секунд...")
        time.sleep(5)

if __name__ == "__main__":
    main() 