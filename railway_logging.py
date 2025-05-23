#!/usr/bin/env python
"""
Модуль для настройки логирования в Railway.
Обеспечивает корректное отображение логов в среде Railway.
"""

import logging
import sys
import os
from datetime import datetime

class RailwayFormatter(logging.Formatter):
    """
    Форматтер логов для Railway с правильными префиксами для разных уровней.
    """
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.is_railway = os.environ.get('RAILWAY_ENVIRONMENT', '') != ''
        
        # Маппинг уровней логирования на префиксы
        self.level_prefixes = {
            logging.DEBUG: "ОТЛАДКА",
            logging.INFO: "ИНФО",
            logging.WARNING: "ПРЕДУПРЕЖДЕНИЕ",
            logging.ERROR: "ОШИБКА",
            logging.CRITICAL: "КРИТИЧЕСКАЯ ОШИБКА"
        }
    
    def format(self, record):
        """
        Форматирование записи лога.
        Добавляет префикс для Railway в зависимости от уровня.
        """
        # Получаем стандартное форматирование
        formatted = super().format(record)
        
        # Если сообщение уже имеет префикс, не добавляем еще один
        if any(formatted.startswith(prefix) for prefix in ["ИНФО:", "ПРЕДУПРЕЖДЕНИЕ:", "ОШИБКА:", "ОТЛАДКА:", "КРИТИЧЕСКАЯ ОШИБКА:"]):
            return formatted
        
        # Добавляем специальные префиксы для видимости в Railway
        prefix = self.level_prefixes.get(record.levelno, "ИНФО")
        return f"{prefix}: {formatted}"

def setup_railway_logging(logger_name=None, level=logging.INFO):
    """
    Настраивает логирование для Railway с правильными префиксами.
    
    Args:
        logger_name: Имя логгера
        level: Уровень логирования
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем или получаем логгер
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    
    # Устанавливаем уровень логирования
    logger.setLevel(level)
    
    # Очищаем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Создаем новый обработчик для stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Настраиваем форматтер
    formatter = RailwayFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Создаем обработчик для файла логов
    try:
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/bot.log")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"ПРЕДУПРЕЖДЕНИЕ: Не удалось создать файловый обработчик логов: {e}")
    
    # Добавляем консольный обработчик к логгеру
    logger.addHandler(console_handler)
    
    # Если среда - Railway, добавляем информацию
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT', '') != ''
    if is_railway:
        logger.info(f"Логирование настроено для Railway. Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Уровень логирования: {logging.getLevelName(level)}")
    
    return logger

# Функция для преобразования строкового уровня логирования в константу
def get_log_level(level_str):
    """
    Преобразует строковое представление уровня логирования в константу.
    
    Args:
        level_str: Строковое представление уровня логирования
        
    Returns:
        int: Константа уровня логирования
    """
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    return levels.get(level_str.lower(), logging.INFO)

# Функция для упрощенного вывода сообщений для Railway
def railway_print(message, level="INFO"):
    """
    Функция для удобного вывода сообщений в Railway с правильными префиксами.
    
    Args:
        message: Сообщение для вывода
        level: Уровень сообщения (INFO, ERROR, WARNING, DEBUG)
    """
    # Маппинг уровней на префиксы
    prefixes = {
        "INFO": "ИНФО",
        "ERROR": "ОШИБКА",
        "WARNING": "ПРЕДУПРЕЖДЕНИЕ",
        "DEBUG": "ОТЛАДКА",
        "CRITICAL": "КРИТИЧЕСКАЯ ОШИБКА"
    }
    
    # Получаем префикс или используем ИНФО по умолчанию
    prefix = prefixes.get(level.upper(), "ИНФО")
    
    # Проверяем, не имеет ли сообщение уже префикс
    if any(message.startswith(f"{p}: ") for p in prefixes.values()):
        print(message)
    else:
        print(f"{prefix}: {message}")
    
    sys.stdout.flush()  # Принудительный сброс буфера для Railway

# Если модуль запущен напрямую, выполняем тестирование
if __name__ == "__main__":
    # Тестируем настройку логирования
    logger = setup_railway_logging("railway_logging_test", logging.DEBUG)
    
    logger.debug("Это отладочное сообщение")
    logger.info("Это информационное сообщение")
    logger.warning("Это предупреждение")
    logger.error("Это сообщение об ошибке")
    logger.critical("Это критическая ошибка")
    
    # Тестируем функцию railway_print
    railway_print("Тестовое информационное сообщение")
    railway_print("Тестовое сообщение об ошибке", "ERROR")
    railway_print("Тестовое предупреждение", "WARNING")
    railway_print("Тестовое отладочное сообщение", "DEBUG")
    
    print("Тестирование логирования для Railway завершено успешно") 