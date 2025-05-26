#!/usr/bin/env python
"""
Скрипт для запуска бота с предварительной проверкой версии aiogram
"""

import sys
import os
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [STARTER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("bot_starter")

def main():
    """
    Основная функция для запуска бота с проверкой совместимости
    """
    logger.info("Запуск бота с проверкой совместимости версии aiogram")
    
    # Проверяем наличие файла проверки
    if not os.path.exists("check_aiogram_version.py"):
        logger.error("Файл check_aiogram_version.py не найден")
        return 1
    
    # Запускаем скрипт проверки версии aiogram
    logger.info("Запуск проверки версии aiogram...")
    try:
        subprocess.run([sys.executable, "check_aiogram_version.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при проверке версии aiogram: {e}")
        return 1
    
    # Запускаем основной скрипт
    logger.info("Запуск основного скрипта main.py...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при запуске main.py: {e}")
        return 1
    
    logger.info("Бот успешно завершил работу")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 