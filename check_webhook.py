#!/usr/bin/env python
"""
Скрипт для проверки настроек webhook бота
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK_CHECK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("webhook_check")

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
    sys.exit(1)

def check_webhook():
    """Проверяет текущие настройки webhook"""
    logger.info("🔍 Проверка текущих настроек webhook...")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            webhook_info = response.json().get('result', {})
            logger.info(f"ℹ️ Текущий webhook URL: {webhook_info.get('url')}")
            logger.info(f"ℹ️ Последняя ошибка: {webhook_info.get('last_error_message', 'нет')}")
            logger.info(f"ℹ️ Ожидающие обновления: {webhook_info.get('pending_update_count', 0)}")
            logger.info(f"ℹ️ IP-адрес: {webhook_info.get('ip_address', 'нет')}")
            logger.info(f"ℹ️ Максимальные соединения: {webhook_info.get('max_connections', 'нет')}")
            logger.info(f"ℹ️ Последний код ошибки: {webhook_info.get('last_error_date', 'нет')}")
            logger.info(f"ℹ️ Последнее обновление: {webhook_info.get('last_synchronization_error_date', 'нет')}")
            
            return webhook_info
        else:
            logger.error(f"❌ Ошибка при проверке webhook: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при проверке webhook: {e}")
        return None

def delete_webhook():
    """Удаляет текущий webhook"""
    logger.info("🗑️ Удаление текущего webhook...")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Webhook успешно удален")
            return True
        else:
            logger.error(f"❌ Ошибка при удалении webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при удалении webhook: {e}")
        return False

def setup_webhook(webhook_url=None):
    """Настраивает webhook с указанным URL"""
    if not webhook_url:
        # Используем URL на основе сервиса Railway
        railway_service_id = os.environ.get('RAILWAY_SERVICE_ID')
        if railway_service_id:
            webhook_url = f"https://{railway_service_id}.up.railway.app/webhook/{BOT_TOKEN}"
        else:
            logger.error("❌ Не указан URL для webhook и не найден RAILWAY_SERVICE_ID")
            return False
    
    logger.info(f"🔄 Настройка webhook на URL: {webhook_url}")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        response = requests.post(
            api_url,
            json={
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query', 'inline_query'],
                'drop_pending_updates': True,
                'secret_token': os.environ.get('WEBHOOK_SECRET', 'telegram_webhook_secret')
            },
            timeout=30
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            description = response.json().get('description', 'Нет описания')
            logger.info(f"✅ Webhook успешно установлен: {description}")
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при настройке webhook: {e}")
        return False

def send_test_message():
    """Отправляет тестовое сообщение через Telegram API"""
    logger.info("📨 Отправка тестового сообщения...")
    
    # Получаем свой чат ID
    my_chat_id = input("Введите ваш Telegram ID для отправки тестового сообщения: ")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(
            api_url,
            json={
                'chat_id': my_chat_id,
                'text': "🤖 Тестовое сообщение от бота. Если вы видите это сообщение, API работает правильно."
            },
            timeout=10
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Тестовое сообщение успешно отправлено")
            return True
        else:
            logger.error(f"❌ Ошибка при отправке тестового сообщения: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при отправке тестового сообщения: {e}")
        return False

def test_polling_mode():
    """Запускает бота в режиме polling для проверки работоспособности"""
    logger.info("🔄 Запуск бота в режиме polling для тестирования...")
    
    # Сначала удаляем webhook
    if not delete_webhook():
        logger.warning("⚠️ Не удалось удалить webhook, но продолжаем тестирование")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            updates = response.json().get('result', [])
            logger.info(f"ℹ️ Получено {len(updates)} обновлений")
            for update in updates:
                logger.info(f"ℹ️ Update ID: {update.get('update_id')}")
                if 'message' in update:
                    message = update['message']
                    logger.info(f"📩 Сообщение от {message['from'].get('username', 'Unknown')}: {message.get('text', 'No text')}")
            return True
        else:
            logger.error(f"❌ Ошибка при получении обновлений: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при получении обновлений: {e}")
        return False

def check_bot_info():
    """Проверяет информацию о боте"""
    logger.info("🔍 Проверка информации о боте...")
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            bot_info = response.json().get('result', {})
            logger.info(f"ℹ️ Имя бота: {bot_info.get('first_name')}")
            logger.info(f"ℹ️ Username: @{bot_info.get('username')}")
            logger.info(f"ℹ️ ID бота: {bot_info.get('id')}")
            logger.info(f"ℹ️ Поддерживает inline запросы: {bot_info.get('supports_inline_queries', False)}")
            return bot_info
        else:
            logger.error(f"❌ Ошибка при получении информации о боте: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при получении информации о боте: {e}")
        return None

def main():
    """Основная функция"""
    logger.info("🚀 Запуск проверки webhook бота...")
    
    # Проверяем информацию о боте
    bot_info = check_bot_info()
    if not bot_info:
        logger.error("❌ Не удалось получить информацию о боте. Проверьте BOT_TOKEN")
        return
    
    # Проверяем текущие настройки webhook
    webhook_info = check_webhook()
    
    # Меню действий
    while True:
        print("\n🔧 Выберите действие:")
        print("1. Проверить настройки webhook")
        print("2. Удалить webhook")
        print("3. Настроить webhook")
        print("4. Отправить тестовое сообщение")
        print("5. Тестировать в режиме polling")
        print("6. Проверить информацию о боте")
        print("0. Выход")
        
        choice = input("Введите номер действия: ")
        
        if choice == "1":
            check_webhook()
        elif choice == "2":
            delete_webhook()
        elif choice == "3":
            webhook_url = input("Введите URL для webhook (оставьте пустым для автоматического определения): ")
            if not webhook_url:
                webhook_url = None
            setup_webhook(webhook_url)
        elif choice == "4":
            send_test_message()
        elif choice == "5":
            test_polling_mode()
        elif choice == "6":
            check_bot_info()
        elif choice == "0":
            logger.info("👋 Завершение работы")
            break
        else:
            logger.warning("⚠️ Неверный выбор. Попробуйте снова")

if __name__ == "__main__":
    main() 