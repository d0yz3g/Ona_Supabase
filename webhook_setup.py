#!/usr/bin/env python
"""
Скрипт для настройки webhook режима работы Telegram-бота
Рекомендуется для продакшн-окружения на Railway и других хостингах
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK_SETUP] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("webhook_setup")

def setup_webhook():
    """
    Настраивает webhook для Telegram-бота
    
    Returns:
        bool: True если webhook успешно настроен, False в противном случае
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем необходимые переменные
    bot_token = os.environ.get('BOT_TOKEN')
    webhook_url = os.environ.get('WEBHOOK_URL')
    railway_service_id = os.environ.get('RAILWAY_SERVICE_ID')
    railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    
    # Если нет WEBHOOK_URL, но есть Railway-специфичные переменные, формируем URL
    if not webhook_url and railway_public_domain:
        webhook_url = f"https://{railway_public_domain}/webhook/{bot_token}"
        logger.info(f"Сформирован WEBHOOK_URL на основе Railway-домена: {webhook_url}")
    
    # Проверяем наличие необходимых переменных
    if not bot_token:
        logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
        return False
        
    if not webhook_url:
        logger.error("❌ Переменная WEBHOOK_URL не найдена в .env или переменных окружения")
        logger.error("Укажите WEBHOOK_URL в формате: https://your-domain.com/webhook/{bot_token}")
        return False
    
    logger.info(f"Настройка webhook для бота с токеном: {bot_token[:5]}...{bot_token[-5:]}")
    logger.info(f"Webhook URL: {webhook_url}")
    
    # Формируем URL для API Telegram
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    try:
        # Отправляем запрос на установку webhook
        response = requests.post(
            api_url,
            json={
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query', 'inline_query'],
                'drop_pending_updates': True
            }
        )
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get('ok'):
            result = response.json().get('result', {})
            description = response.json().get('description', 'Нет описания')
            
            logger.info(f"✅ Webhook успешно установлен: {description}")
            
            # Получаем информацию о текущем webhook
            get_webhook_info(bot_token)
            
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при настройке webhook: {e}")
        return False

def get_webhook_info(bot_token=None):
    """
    Получает информацию о текущем webhook
    
    Args:
        bot_token (str, optional): Токен Telegram-бота. Если не указан, берется из переменных окружения.
        
    Returns:
        dict: Информация о webhook или None в случае ошибки
    """
    # Загружаем переменные окружения, если токен не передан
    if not bot_token:
        load_dotenv()
        bot_token = os.environ.get('BOT_TOKEN')
    
    # Проверяем наличие токена
    if not bot_token:
        logger.error("❌ Токен бота не найден")
        return None
    
    logger.info(f"Получение информации о webhook для бота с токеном: {bot_token[:5]}...{bot_token[-5:]}")
    
    try:
        # Отправляем запрос на получение информации о webhook
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get('ok'):
            webhook_info = response.json().get('result', {})
            url = webhook_info.get('url', 'Не установлен')
            pending_update_count = webhook_info.get('pending_update_count', 0)
            last_error_date = webhook_info.get('last_error_date')
            last_error_message = webhook_info.get('last_error_message')
            max_connections = webhook_info.get('max_connections', 40)
            allowed_updates = webhook_info.get('allowed_updates', [])
            
            logger.info(f"Текущий webhook URL: {url}")
            logger.info(f"Ожидающих обновлений: {pending_update_count}")
            logger.info(f"Максимальное количество соединений: {max_connections}")
            logger.info(f"Разрешенные типы обновлений: {', '.join(allowed_updates) if allowed_updates else 'все'}")
            
            if last_error_date:
                logger.warning(f"Последняя ошибка webhook: {last_error_message}")
            
            return webhook_info
        else:
            logger.error(f"❌ Ошибка при получении информации о webhook: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Исключение при получении информации о webhook: {e}")
        return None

def remove_webhook(bot_token=None):
    """
    Удаляет webhook для указанного бота
    
    Args:
        bot_token (str, optional): Токен Telegram-бота. Если не указан, берется из переменных окружения.
        
    Returns:
        bool: True если webhook успешно удален, False в противном случае
    """
    # Загружаем переменные окружения, если токен не передан
    if not bot_token:
        load_dotenv()
        bot_token = os.environ.get('BOT_TOKEN')
    
    # Проверяем наличие токена
    if not bot_token:
        logger.error("❌ Токен бота не найден")
        return False
    
    logger.info(f"Удаление webhook для бота с токеном: {bot_token[:5]}...{bot_token[-5:]}")
    
    try:
        # Отправляем запрос на удаление webhook
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
            json={'drop_pending_updates': True}
        )
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Webhook успешно удален")
            return True
        else:
            logger.error(f"❌ Ошибка при удалении webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при удалении webhook: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск настройки webhook...")
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            success = remove_webhook()
            if success:
                logger.info("✅ Webhook успешно удален")
                sys.exit(0)
            else:
                logger.error("❌ Не удалось удалить webhook")
                sys.exit(1)
        elif sys.argv[1] == "--info":
            webhook_info = get_webhook_info()
            if webhook_info:
                logger.info("✅ Информация о webhook успешно получена")
                sys.exit(0)
            else:
                logger.error("❌ Не удалось получить информацию о webhook")
                sys.exit(1)
    else:
        success = setup_webhook()
        if success:
            logger.info("✅ Webhook успешно настроен")
            sys.exit(0)
        else:
            logger.error("❌ Не удалось настроить webhook")
            sys.exit(1) 