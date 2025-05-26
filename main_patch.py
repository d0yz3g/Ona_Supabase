#!/usr/bin/env python3
"""
Патчит main.py и затем импортирует его.
Используется как точка входа для Railway.
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
logger = logging.getLogger("main_patch")

def setup_paths():
    """Добавляет текущую директорию в sys.path"""
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        logger.info(f"Добавлен {os.getcwd()} в sys.path")

def apply_patches():
    """Применяет все патчи"""
    try:
        logger.info("Импортирую fix_imports_global...")
        import fix_imports_global
        logger.info("✅ fix_imports_global успешно импортирован")
        
        logger.info("Импортирую pre_import_fix...")
        import pre_import_fix
        logger.info("✅ pre_import_fix успешно импортирован")
        
        logger.info("Проверка AsyncOpenAI...")
        try:
            from openai import AsyncOpenAI
            logger.info("✅ AsyncOpenAI доступен")
        except ImportError as e:
            logger.error(f"❌ AsyncOpenAI недоступен: {e}")
            logger.info("Патчинг импортов для обхода проблемы...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при применении патчей: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Основная функция"""
    logger.info("=== Запуск бота с патчингом для Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    
    # Настраиваем пути
    setup_paths()
    
    # Применяем патчи
    apply_patches()
    
    # Устанавливаем переменную окружения для Railway
    os.environ["RAILWAY_ENV"] = "1"
    
    try:
        # Импортируем main
        logger.info("Импортирую main...")
        import main
        logger.info("✅ Бот запущен успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 