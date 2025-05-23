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
    Форматтер логов для Railway с дополнительной информацией.
    """
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.is_railway = os.environ.get('RAILWAY_ENVIRONMENT', '') != ''
    
    def format(self, record):
        """
        Форматирование записи лога.
        Добавляет префикс для Railway.
        """
        formatted = super().format(record)
        
        # Добавляем специальные префиксы для видимости в Railway
        if record.levelno >= logging.ERROR:
            return f"ОШИБКА: {formatted}"
        elif record.levelno >= logging.WARNING:
            return f"ПРЕДУПРЕЖДЕНИЕ: {formatted}"
        elif record.levelno >= logging.INFO:
            return f"ИНФО: {formatted}"
        elif record.levelno >= logging.DEBUG:
            return f"ОТЛАДКА: {formatted}"
        return formatted

def setup_railway_logging(logger_name=None, level=logging.INFO):
    """
    Настраивает логирование для Railway.
    
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
    
    # Добавляем обработчик к логгеру
    logger.addHandler(console_handler)
    
    # Если среда - Railway, добавляем информацию
    if os.environ.get('RAILWAY_ENVIRONMENT', ''):
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
    Функция для удобного вывода сообщений в Railway.
    
    Args:
        message: Сообщение для вывода
        level: Уровень сообщения (INFO, ERROR, WARNING, DEBUG)
    """
    prefix = "ИНФО"
    if level.upper() == "ERROR":
        prefix = "ОШИБКА"
    elif level.upper() == "WARNING":
        prefix = "ПРЕДУПРЕЖДЕНИЕ"
    elif level.upper() == "DEBUG":
        prefix = "ОТЛАДКА"
    
    print(f"{prefix}: {message}")
    sys.stdout.flush()  # Принудительный сброс буфера для Railway 