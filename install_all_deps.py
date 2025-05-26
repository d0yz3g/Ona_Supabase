#!/usr/bin/env python3
"""
Скрипт для установки всех зависимостей, включая правильную версию openai.
Этот скрипт будет выполняться в Railway для обеспечения установки нужных версий пакетов.
"""
import os
import sys
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("install_all_deps")

# Список критических зависимостей для установки в правильном порядке
CRITICAL_DEPS = [
    "python-dotenv==1.0.0",
    "httpx==0.23.3",
    "openai==1.3.3",    # Версия с AsyncOpenAI
    "pydantic==2.1.1",  # Совместима с aiogram 3.0.0
    "aiogram==3.0.0",
]

# Флаг для принудительной переустановки
FORCE_REINSTALL = True

def check_openai_version():
    """Проверяет установленную версию openai"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "openai"],
            capture_output=True,
            text=True
        )
        
        # Ищем строку с версией
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                version = line.split(":")[1].strip()
                logger.info(f"Установленная версия openai: {version}")
                return version
        
        logger.warning("Не удалось определить версию openai")
        return None
    
    except Exception as e:
        logger.error(f"Ошибка при проверке версии openai: {e}")
        return None

def install_from_requirements():
    """Устанавливает зависимости из файла requirements.txt"""
    if not os.path.exists("requirements.txt"):
        logger.error("Файл requirements.txt не найден")
        return False
    
    try:
        logger.info("Установка зависимостей из requirements.txt")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Зависимости из requirements.txt установлены успешно")
            return True
        else:
            logger.error(f"Ошибка при установке зависимостей из requirements.txt: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Исключение при установке зависимостей из requirements.txt: {e}")
        return False

def install_critical_deps():
    """Устанавливает критические зависимости принудительно"""
    success_count = 0
    
    for dep in CRITICAL_DEPS:
        try:
            logger.info(f"Установка {dep}")
            cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir"]
            
            if FORCE_REINSTALL:
                cmd.append("--force-reinstall")
            
            cmd.append(dep)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Успешно установлен {dep}")
                success_count += 1
            else:
                logger.error(f"Ошибка при установке {dep}: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Исключение при установке {dep}: {e}")
    
    return success_count == len(CRITICAL_DEPS)

def verify_openai_has_asyncopenai():
    """Проверяет, что установленная версия openai имеет класс AsyncOpenAI"""
    try:
        # Пытаемся импортировать AsyncOpenAI из openai
        code = """
import sys
try:
    from openai import AsyncOpenAI
    print("AsyncOpenAI успешно импортирован")
    sys.exit(0)
except ImportError as e:
    print(f"Не удалось импортировать AsyncOpenAI: {e}")
    sys.exit(1)
"""
        
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Проверка прошла успешно: AsyncOpenAI доступен")
            return True
        else:
            logger.error(f"Проверка не пройдена: AsyncOpenAI недоступен. {result.stdout}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при проверке AsyncOpenAI: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало установки зависимостей ===")
    
    # Проверяем текущую версию openai
    current_version = check_openai_version()
    
    # Устанавливаем зависимости из requirements.txt
    install_from_requirements()
    
    # Устанавливаем критические зависимости
    if install_critical_deps():
        logger.info("Критические зависимости установлены успешно")
    else:
        logger.warning("Не все критические зависимости были установлены успешно")
    
    # Проверяем, что openai имеет AsyncOpenAI
    if verify_openai_has_asyncopenai():
        logger.info("=== Установка зависимостей завершена успешно ===")
        return 0
    else:
        logger.error("=== Установка зависимостей завершена с ошибками ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 