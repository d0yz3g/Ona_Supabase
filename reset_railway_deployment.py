#!/usr/bin/env python
"""
Скрипт для полного сброса и пересоздания конфигурации webhook на Railway.
Используйте этот скрипт, если у вас продолжаются проблемы с работой бота в режиме webhook.
"""

import os
import sys
import logging
import requests
import time
import argparse
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RAILWAY_RESET] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("railway_reset.log")]
)
logger = logging.getLogger("railway_reset")

# Загружаем переменные окружения
load_dotenv()

def delete_webhook(bot_token, drop_updates=False):
    """
    Полностью удаляет webhook и все ожидающие обновления
    
    Args:
        bot_token (str): Токен бота
        drop_updates (bool): Удалять ли ожидающие обновления
        
    Returns:
        bool: True, если webhook успешно удален, иначе False
    """
    logger.info(f"🔄 Удаление webhook{' и ожидающих обновлений' if drop_updates else ''}...")
    
    try:
        # Формируем URL для удаления webhook
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        params = {"drop_pending_updates": drop_updates}
        
        # Отправляем запрос
        response = requests.get(url, params=params, timeout=30)
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get("ok"):
            logger.info(f"✅ Webhook успешно удален")
            return True
        else:
            logger.error(f"❌ Ошибка при удалении webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при удалении webhook: {e}")
        return False

def set_webhook(bot_token, webhook_url):
    """
    Устанавливает новый webhook
    
    Args:
        bot_token (str): Токен бота
        webhook_url (str): URL для установки webhook
        
    Returns:
        bool: True, если webhook успешно установлен, иначе False
    """
    logger.info(f"🔄 Установка webhook на URL: {webhook_url}...")
    
    try:
        # Формируем URL и данные для запроса
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        data = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query", "inline_query"],
            "drop_pending_updates": True
        }
        
        # Отправляем запрос
        response = requests.post(url, json=data, timeout=30)
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get("ok"):
            logger.info(f"✅ Webhook успешно установлен: {response.json().get('description')}")
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при установке webhook: {e}")
        return False

def get_webhook_info(bot_token):
    """
    Получает информацию о текущих настройках webhook
    
    Args:
        bot_token (str): Токен бота
        
    Returns:
        dict|None: Информация о webhook или None в случае ошибки
    """
    logger.info("🔍 Получение информации о webhook...")
    
    try:
        # Формируем URL для запроса
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        
        # Отправляем запрос
        response = requests.get(url, timeout=30)
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get("ok"):
            webhook_info = response.json().get("result", {})
            webhook_url = webhook_info.get("url", "")
            last_error = webhook_info.get("last_error_message", "нет")
            pending_updates = webhook_info.get("pending_update_count", 0)
            
            logger.info(f"ℹ️ Текущий webhook URL: {webhook_url}")
            logger.info(f"ℹ️ Последняя ошибка: {last_error}")
            logger.info(f"ℹ️ Ожидающие обновления: {pending_updates}")
            
            return webhook_info
        else:
            logger.error(f"❌ Ошибка при получении информации о webhook: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при получении информации о webhook: {e}")
        return None

def reset_webhook_config(bot_token, webhook_url=None, railway_domain=None):
    """
    Полностью сбрасывает и пересоздает webhook
    
    Args:
        bot_token (str): Токен бота
        webhook_url (str|None): URL для установки webhook или None
        railway_domain (str|None): Домен приложения на Railway или None
        
    Returns:
        bool: True, если операция успешно выполнена, иначе False
    """
    # Если webhook_url не указан, но указан railway_domain, формируем URL
    if not webhook_url and railway_domain:
        webhook_url = f"https://{railway_domain}/webhook/{bot_token}"
        logger.info(f"🔧 Сформирован webhook URL на основе Railway домена: {webhook_url}")
    
    # Проверяем наличие URL
    if not webhook_url:
        logger.error("❌ Не указан URL для webhook")
        return False
    
    # Получаем текущую информацию о webhook
    logger.info("1️⃣ Получение текущей информации о webhook...")
    initial_info = get_webhook_info(bot_token)
    
    # Удаляем текущий webhook и все ожидающие обновления
    logger.info("2️⃣ Удаление текущего webhook и всех ожидающих обновлений...")
    if not delete_webhook(bot_token, drop_updates=True):
        logger.error("❌ Не удалось удалить webhook")
        return False
    
    # Ждем несколько секунд
    logger.info("⏳ Ожидание 5 секунд...")
    time.sleep(5)
    
    # Проверяем, что webhook удален
    logger.info("3️⃣ Проверка удаления webhook...")
    deleted_info = get_webhook_info(bot_token)
    
    if deleted_info and deleted_info.get("url"):
        logger.warning("⚠️ Webhook не был полностью удален")
    else:
        logger.info("✅ Webhook успешно удален")
    
    # Устанавливаем новый webhook
    logger.info("4️⃣ Установка нового webhook...")
    if not set_webhook(bot_token, webhook_url):
        logger.error("❌ Не удалось установить webhook")
        return False
    
    # Проверяем новый webhook
    logger.info("5️⃣ Проверка нового webhook...")
    new_info = get_webhook_info(bot_token)
    
    if not new_info or new_info.get("url") != webhook_url:
        logger.error("❌ Webhook не установлен или установлен с неправильным URL")
        return False
    
    # Тестируем новый webhook
    logger.info("6️⃣ Тестирование нового webhook...")
    try:
        # Отправляем тестовый запрос напрямую на URL
        test_data = {
            "update_id": 12345,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "test_user"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "test_user",
                    "type": "private"
                },
                "date": 1616142831,
                "text": "/start"
            }
        }
        
        # Сначала проверяем доступность /health endpoint
        health_url = webhook_url.replace("/webhook/" + bot_token, "/health")
        logger.info(f"🔍 Проверка доступности /health endpoint: {health_url}")
        
        health_response = requests.get(health_url, timeout=30)
        if health_response.status_code == 200:
            logger.info(f"✅ Health endpoint доступен: {health_response.text}")
        else:
            logger.warning(f"⚠️ Health endpoint недоступен: {health_response.status_code} - {health_response.text}")
        
        # Теперь тестируем webhook
        logger.info(f"🔍 Отправка тестового запроса на webhook URL: {webhook_url}")
        response = requests.post(webhook_url, json=test_data, timeout=30)
        
        logger.info(f"ℹ️ Код ответа: {response.status_code}")
        logger.info(f"ℹ️ Текст ответа: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Webhook обрабатывает запросы корректно")
        else:
            logger.warning(f"⚠️ Webhook не обрабатывает запросы корректно: {response.status_code}")
            if response.status_code == 404:
                logger.warning("⚠️ Ошибка 404 указывает на проблему с маршрутизацией в приложении")
    except Exception as e:
        logger.error(f"❌ Исключение при тестировании webhook: {e}")
    
    logger.info("✅ Процедура сброса и пересоздания webhook завершена")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сброс и пересоздание webhook на Railway")
    parser.add_argument("--token", help="Токен бота Telegram")
    parser.add_argument("--webhook-url", help="URL для установки webhook")
    parser.add_argument("--railway-domain", help="Домен приложения на Railway")
    args = parser.parse_args()
    
    # Получаем токен бота из аргументов или из .env
    bot_token = args.token or os.environ.get("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ Не указан токен бота. Используйте --token или добавьте BOT_TOKEN в .env")
        sys.exit(1)
    
    # Получаем URL webhook из аргументов или из .env
    webhook_url = args.webhook_url or os.environ.get("WEBHOOK_URL")
    
    # Получаем домен Railway из аргументов или из .env
    railway_domain = args.railway_domain or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    # Выполняем сброс и пересоздание webhook
    logger.info("🚀 Запуск процедуры сброса и пересоздания webhook на Railway")
    success = reset_webhook_config(bot_token, webhook_url, railway_domain)
    
    if success:
        logger.info("🎉 Процедура сброса и пересоздания webhook успешно завершена")
        sys.exit(0)
    else:
        logger.error("❌ Не удалось выполнить сброс и пересоздание webhook")
        sys.exit(1) 