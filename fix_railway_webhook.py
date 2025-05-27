#!/usr/bin/env python
"""
Скрипт для исправления проблем с webhook на Railway
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RAILWAY_FIX] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("railway_fix.log")]
)
logger = logging.getLogger("railway_fix")

# Загружаем переменные окружения
load_dotenv()

def check_railway_status():
    """Проверяет статус приложения на Railway"""
    railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if not railway_url:
        railway_url = os.environ.get("WEBHOOK_URL", "").split("/webhook/")[0]
        
    if not railway_url:
        logger.error("❌ Не удалось определить URL приложения на Railway")
        return False
    
    # Проверяем доступность приложения
    try:
        if not railway_url.startswith("http"):
            railway_url = f"https://{railway_url}"
        
        logger.info(f"🔍 Проверка доступности приложения на Railway: {railway_url}")
        response = requests.get(f"{railway_url}/health", timeout=30)
        
        if response.status_code == 200:
            logger.info(f"✅ Приложение на Railway доступно: {response.text}")
            return True
        else:
            logger.error(f"❌ Ошибка при проверке приложения на Railway: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при проверке приложения на Railway: {e}")
        return False

def delete_and_set_webhook():
    """Удаляет текущий webhook и устанавливает новый"""
    bot_token = os.environ.get("BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ Переменная BOT_TOKEN не найдена")
        return False
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    railway_public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if not webhook_url and railway_public_domain:
        webhook_url = f"https://{railway_public_domain}/webhook/{bot_token}"
        logger.info(f"🔧 Сгенерирован webhook URL на основе Railway домена: {webhook_url}")
    
    if not webhook_url:
        logger.error("❌ Не удалось определить WEBHOOK_URL")
        return False
    
    # Удаляем текущий webhook
    try:
        logger.info("🔄 Удаление текущего webhook...")
        delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
        delete_response = requests.get(delete_url, timeout=30)
        
        if delete_response.status_code == 200 and delete_response.json().get("ok"):
            logger.info("✅ Webhook успешно удален")
        else:
            logger.error(f"❌ Ошибка при удалении webhook: {delete_response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при удалении webhook: {e}")
        return False
    
    # Устанавливаем новый webhook
    try:
        logger.info(f"🔄 Установка нового webhook на URL: {webhook_url}")
        set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        
        set_data = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query", "inline_query"],
            "drop_pending_updates": True,
        }
        
        set_response = requests.post(set_url, json=set_data, timeout=30)
        
        if set_response.status_code == 200 and set_response.json().get("ok"):
            logger.info(f"✅ Webhook успешно установлен: {set_response.json().get('description')}")
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {set_response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при установке webhook: {e}")
        return False

def check_webhook_info():
    """Проверяет текущие настройки webhook"""
    bot_token = os.environ.get("BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ Переменная BOT_TOKEN не найдена")
        return False
    
    try:
        logger.info("🔍 Проверка текущих настроек webhook...")
        info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        info_response = requests.get(info_url, timeout=30)
        
        if info_response.status_code == 200 and info_response.json().get("ok"):
            webhook_info = info_response.json().get("result", {})
            webhook_url = webhook_info.get("url", "")
            last_error = webhook_info.get("last_error_message", "нет")
            pending_updates = webhook_info.get("pending_update_count", 0)
            
            logger.info(f"ℹ️ Текущий webhook URL: {webhook_url}")
            logger.info(f"ℹ️ Последняя ошибка: {last_error}")
            logger.info(f"ℹ️ Ожидающие обновления: {pending_updates}")
            
            return webhook_info
        else:
            logger.error(f"❌ Ошибка при получении информации о webhook: {info_response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при получении информации о webhook: {e}")
        return None

def test_webhook():
    """Отправляет тестовый запрос на webhook URL для проверки доступности"""
    webhook_url = os.environ.get("WEBHOOK_URL")
    
    if not webhook_url:
        logger.error("❌ Переменная WEBHOOK_URL не найдена")
        return False
    
    try:
        logger.info(f"🔄 Отправка тестового запроса на webhook URL: {webhook_url}")
        
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
        
        response = requests.post(webhook_url, json=test_data, timeout=30)
        
        logger.info(f"ℹ️ Код ответа: {response.status_code}")
        logger.info(f"ℹ️ Текст ответа: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Webhook URL доступен и отвечает корректно")
            return True
        else:
            logger.error(f"❌ Ошибка при тестировании webhook URL: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при тестировании webhook URL: {e}")
        return False

def fix_railway_application():
    """Исправляет проблемы с приложением на Railway"""
    logger.info("🔧 Запуск процедуры исправления приложения на Railway")
    
    # Проверяем текущие настройки webhook
    webhook_info = check_webhook_info()
    
    if not webhook_info:
        logger.error("❌ Не удалось получить информацию о webhook")
        return False
    
    # Проверяем статус приложения на Railway
    railway_status = check_railway_status()
    
    if not railway_status:
        logger.error("❌ Приложение на Railway недоступно")
        logger.info("ℹ️ Рекомендуется проверить настройки на Railway и перезапустить приложение")
        return False
    
    # Перенастраиваем webhook
    reset_webhook = delete_and_set_webhook()
    
    if not reset_webhook:
        logger.error("❌ Не удалось перенастроить webhook")
        return False
    
    # Проверяем обновленные настройки webhook
    updated_webhook_info = check_webhook_info()
    
    if not updated_webhook_info:
        logger.error("❌ Не удалось получить обновленную информацию о webhook")
        return False
    
    # Тестируем webhook
    webhook_test = test_webhook()
    
    if not webhook_test:
        logger.error("❌ Тест webhook не пройден")
        logger.info("ℹ️ Рекомендуется проверить код обработки webhook в приложении")
        return False
    
    logger.info("✅ Все проверки успешно пройдены. Приложение должно работать корректно.")
    return True

if __name__ == "__main__":
    logger.info("🚀 Запуск скрипта исправления проблем с webhook на Railway")
    
    # Проверяем наличие необходимых переменных окружения
    if not os.environ.get("BOT_TOKEN"):
        logger.error("❌ Переменная BOT_TOKEN не найдена в .env файле")
        sys.exit(1)
    
    if not os.environ.get("WEBHOOK_URL") and not os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
        logger.error("❌ Не найдены переменные WEBHOOK_URL или RAILWAY_PUBLIC_DOMAIN")
        sys.exit(1)
    
    # Запускаем процедуру исправления
    success = fix_railway_application()
    
    if success:
        logger.info("🎉 Процедура исправления успешно завершена")
        sys.exit(0)
    else:
        logger.error("❌ Не удалось исправить проблемы с webhook на Railway")
        sys.exit(1) 