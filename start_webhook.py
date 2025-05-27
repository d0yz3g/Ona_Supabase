#!/usr/bin/env python
"""
Скрипт для запуска бота Telegram в режиме webhook
Решает проблему с ошибкой "TelegramConflictError: Conflict: terminated by other getUpdates request"
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("webhook.log")]
)
logger = logging.getLogger("webhook")

# Загружаем переменные окружения
load_dotenv()

# Устанавливаем режим webhook
os.environ["WEBHOOK_MODE"] = "true"

# Получаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
    sys.exit(1)

def check_env_variables():
    """Проверяет наличие необходимых переменных окружения"""
    webhook_url = os.getenv("WEBHOOK_URL")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if not webhook_url and not railway_public_domain:
        logger.warning("⚠️ Не указаны WEBHOOK_URL и RAILWAY_PUBLIC_DOMAIN")
        logger.warning("⚠️ Webhook будет создан автоматически, но его URL может быть недоступен")
        return False
    
    if webhook_url:
        logger.info(f"Webhook URL: {webhook_url}")
    elif railway_public_domain:
        webhook_url = f"https://{railway_public_domain}/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован webhook URL: {webhook_url}")
    
    return True

def start_webhook_server():
    """Запускает webhook сервер для бота"""
    try:
        # Импортируем необходимые модули
        from webhook_server import run_webhook_server
        
        # Запускаем webhook сервер
        logger.info("Запуск webhook сервера...")
        exit_code = run_webhook_server()
        
        if exit_code != 0:
            logger.error(f"❌ Webhook сервер завершился с кодом {exit_code}")
            return exit_code
        
        return 0
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать webhook_server: {e}")
        logger.error("Убедитесь, что файл webhook_server.py находится в текущей директории")
        return 1
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске webhook сервера: {e}")
        return 1

def main():
    """Основная функция для запуска бота в режиме webhook"""
    logger.info("=== Запуск бота в режиме webhook ===")
    
    # Проверяем переменные окружения
    check_env_variables()
    
    # Запускаем webhook сервер
    exit_code = start_webhook_server()
    
    return exit_code

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("👋 Webhook сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 