#!/usr/bin/env python
"""
Скрипт для проверки версии aiogram и внесения необходимых корректировок в main.py
"""

import re
import sys
import os
import importlib.metadata
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [AIOGRAM_CHECK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("aiogram_check")

def get_aiogram_version():
    """Получает установленную версию aiogram"""
    try:
        version = importlib.metadata.version("aiogram")
        logger.info(f"Установленная версия aiogram: {version}")
        return version
    except Exception as e:
        logger.error(f"Не удалось определить версию aiogram: {e}")
        return "unknown"

def check_and_fix_main_py():
    """Проверяет и исправляет main.py для совместимости с текущей версией aiogram"""
    version = get_aiogram_version()
    
    # Разбираем версию на компоненты
    version_parts = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not version_parts:
        logger.warning(f"Не удалось разобрать версию aiogram: {version}")
        return
    
    major, minor, patch = map(int, version_parts.groups())
    
    # Проверяем версию для определения необходимых изменений
    is_version_gte_3_7 = (major > 3) or (major == 3 and minor >= 7)
    
    logger.info(f"Проверка совместимости с aiogram {version} (>= 3.7.0: {is_version_gte_3_7})")
    
    # Проверяем существование файла main.py
    if not os.path.exists("main.py"):
        logger.error("Файл main.py не найден")
        return
    
    # Читаем текущее содержимое файла
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    modified = False
    
    # Исправления для версии 3.7.0 и выше
    if is_version_gte_3_7:
        # Проверяем, есть ли импорт DefaultBotProperties
        if "from aiogram.client.default import DefaultBotProperties" not in content:
            import_pattern = r"from aiogram.types import BufferedInputFile"
            replacement = (
                "from aiogram.types import BufferedInputFile\n"
                "from aiogram.client.default import DefaultBotProperties"
            )
            content = re.sub(import_pattern, replacement, content)
            modified = True
        
        # Проверяем, используется ли DefaultBotProperties в инициализации бота
        bot_init_pattern = r"bot = Bot\(\s*token=BOT_TOKEN,\s*parse_mode=\"HTML\"\s*\)"
        if re.search(bot_init_pattern, content):
            replacement = (
                "bot = Bot(\n"
                "    token=BOT_TOKEN,\n"
                "    default=DefaultBotProperties(\n"
                "        parse_mode=\"HTML\",\n"
                "        link_preview_is_disabled=True,\n"
                "        protect_content=False\n"
                "    )\n"
                ")"
            )
            content = re.sub(bot_init_pattern, replacement, content)
            modified = True
    
    # Исправления для версии ниже 3.7.0
    else:
        # Удаляем импорт DefaultBotProperties, если он есть
        if "from aiogram.client.default import DefaultBotProperties" in content:
            content = content.replace("from aiogram.client.default import DefaultBotProperties", "# DefaultBotProperties не поддерживается в aiogram < 3.7.0")
            modified = True
        
        # Проверяем, используется ли DefaultBotProperties в инициализации бота
        bot_init_pattern = r"bot = Bot\(\s*token=BOT_TOKEN,\s*default=DefaultBotProperties\([^)]*\)\s*\)"
        if re.search(bot_init_pattern, content):
            replacement = (
                "bot = Bot(\n"
                "    token=BOT_TOKEN,\n"
                "    parse_mode=\"HTML\"  # Используем старый формат для aiogram < 3.7.0\n"
                ")"
            )
            content = re.sub(bot_init_pattern, replacement, content)
            modified = True
    
    # Сохраняем изменения, если они были внесены
    if modified:
        logger.info("Внесены изменения в main.py для совместимости с текущей версией aiogram")
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        logger.info("Файл main.py уже совместим с текущей версией aiogram")

if __name__ == "__main__":
    logger.info("Проверка совместимости с установленной версией aiogram...")
    check_and_fix_main_py()
    logger.info("Проверка завершена")
    
    # Продолжаем выполнение основного скрипта, если скрипт запущен с аргументом --continue
    if len(sys.argv) > 1 and sys.argv[1] == "--continue":
        logger.info("Запуск основного скрипта...")
        try:
            import main
        except ImportError as e:
            logger.error(f"Не удалось импортировать main.py: {e}")
            sys.exit(1) 