#!/usr/bin/env python
"""
Скрипт для исправления и перезапуска бота на Railway
Решает проблемы с webhook и обеспечивает работоспособность бота
"""

import os
import sys
import time
import json
import logging
import requests
from dotenv import load_dotenv
import asyncio
import aiohttp
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RAILWAY_FIX] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("railway_fix.log")
    ]
)
logger = logging.getLogger("railway_fix")

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена. Укажите BOT_TOKEN в .env или переменных окружения")
    sys.exit(1)

def get_webhook_info():
    """
    Получает информацию о текущем webhook
    
    Returns:
        dict: Информация о webhook или None в случае ошибки
    """
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            webhook_info = response.json().get('result', {})
            logger.info(f"✅ Получена информация о webhook: {webhook_info}")
            return webhook_info
        else:
            logger.error(f"❌ Ошибка при получении информации о webhook: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при получении информации о webhook: {e}")
        return None

def get_railway_service_url():
    """
    Определяет URL для сервиса на Railway, избегая healthcheck.railway.app
    
    Returns:
        str: URL сервиса или None если не удалось определить
    """
    # Проверяем наличие переменных окружения Railway
    railway_service_id = os.environ.get('RAILWAY_SERVICE_ID')
    railway_project_id = os.environ.get('RAILWAY_PROJECT_ID')
    railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    
    logger.info("=== Информация о Railway ===")
    logger.info(f"RAILWAY_SERVICE_ID: {railway_service_id}")
    logger.info(f"RAILWAY_PROJECT_ID: {railway_project_id}")
    logger.info(f"RAILWAY_PUBLIC_DOMAIN: {railway_public_domain}")
    logger.info("==========================")
    
    # Проверяем RAILWAY_PUBLIC_DOMAIN
    if railway_public_domain and "healthcheck.railway.app" not in railway_public_domain:
        logger.info(f"Используем RAILWAY_PUBLIC_DOMAIN: {railway_public_domain}")
        return f"https://{railway_public_domain}"
    
    # Если есть RAILWAY_SERVICE_ID, формируем URL на основе него
    if railway_service_id:
        service_url = f"https://{railway_service_id}.up.railway.app"
        logger.info(f"Используем URL на основе RAILWAY_SERVICE_ID: {service_url}")
        return service_url
    
    # Пытаемся получить URL из других источников
    webhook_host = os.environ.get('WEBHOOK_HOST')
    if webhook_host and "healthcheck.railway.app" not in webhook_host:
        logger.info(f"Используем WEBHOOK_HOST: {webhook_host}")
        return f"https://{webhook_host}"
    
    # Проверяем прямое указание WEBHOOK_URL
    webhook_url_env = os.environ.get('WEBHOOK_URL')
    if webhook_url_env:
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(webhook_url_env)
            if parsed_url.netloc and "healthcheck.railway.app" not in parsed_url.netloc:
                logger.info(f"Используем домен из WEBHOOK_URL: {parsed_url.netloc}")
                return f"{parsed_url.scheme}://{parsed_url.netloc}"
        except Exception as e:
            logger.error(f"Ошибка при извлечении домена из WEBHOOK_URL: {e}")
    
    # Проверяем текущий webhook (возможно, там уже установлен правильный URL)
    webhook_info = get_webhook_info()
    if webhook_info and webhook_info.get('url'):
        webhook_url = webhook_info.get('url')
        # Извлекаем домен из URL
        if webhook_url and "healthcheck.railway.app" not in webhook_url:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(webhook_url)
                domain = parsed_url.netloc
                if domain:
                    logger.info(f"Используем домен из текущего webhook URL: {domain}")
                    return f"{parsed_url.scheme}://{domain}"
            except Exception as e:
                logger.error(f"Ошибка при извлечении домена из webhook URL: {e}")
    
    # Если ничего не найдено
    logger.warning("⚠️ Не удалось определить URL сервиса Railway")
    return None

def setup_webhook(webhook_url=None, drop_pending_updates=True):
    """
    Настраивает webhook для бота
    
    Args:
        webhook_url (str, optional): URL для webhook. Если не указан, будет определен автоматически.
        drop_pending_updates (bool): Сбрасывать ли накопившиеся обновления
        
    Returns:
        bool: True если webhook успешно установлен, False в противном случае
    """
    if not webhook_url:
        # Пытаемся определить URL сервиса
        service_url = get_railway_service_url()
        if not service_url:
            logger.error("❌ Не удалось определить URL сервиса для webhook")
            return False
        
        webhook_url = f"{service_url}/webhook/{BOT_TOKEN}"
    
    logger.info(f"🔄 Настраиваем webhook на URL: {webhook_url}")
    
    # Сначала удаляем текущий webhook
    try:
        delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates={str(drop_pending_updates).lower()}"
        delete_response = requests.get(delete_url, timeout=10)
        
        if delete_response.status_code == 200 and delete_response.json().get('ok'):
            logger.info("✅ Текущий webhook успешно удален")
        else:
            logger.warning(f"⚠️ Не удалось удалить текущий webhook: {delete_response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении webhook: {e}")
    
    # Устанавливаем новый webhook
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query', 'inline_query'],
            'drop_pending_updates': drop_pending_updates,
            'secret_token': os.environ.get('WEBHOOK_SECRET', 'telegram_webhook_secret')
        }
        
        response = requests.post(api_url, json=data, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            logger.info(f"✅ Webhook успешно установлен: {response.json().get('description')}")
            
            # Проверяем, что webhook действительно установлен
            time.sleep(1)  # Даем время на применение изменений
            webhook_info = get_webhook_info()
            
            if webhook_info and webhook_info.get('url') == webhook_url:
                logger.info("✅ Webhook успешно проверен и настроен правильно")
                return True
            else:
                logger.warning(f"⚠️ Webhook установлен, но URL не соответствует ожидаемому: {webhook_info.get('url', 'None')}")
                return False
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при установке webhook: {e}")
        return False

def disable_webhook(drop_pending_updates=True):
    """
    Отключает webhook
    
    Args:
        drop_pending_updates (bool): Сбрасывать ли накопившиеся обновления
        
    Returns:
        bool: True если webhook успешно отключен, False в противном случае
    """
    logger.info(f"🔄 Отключаем webhook (сброс накопившихся обновлений: {drop_pending_updates})")
    
    try:
        delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates={str(drop_pending_updates).lower()}"
        delete_response = requests.get(delete_url, timeout=10)
        
        if delete_response.status_code == 200 and delete_response.json().get('ok'):
            logger.info("✅ Webhook успешно отключен")
            
            # Проверяем, что webhook действительно отключен
            time.sleep(1)  # Даем время на применение изменений
            webhook_info = get_webhook_info()
            
            if webhook_info and not webhook_info.get('url'):
                logger.info("✅ Проверка подтвердила, что webhook отключен")
                return True
            else:
                logger.warning(f"⚠️ Проверка показала, что webhook всё еще активен: {webhook_info.get('url', 'None')}")
                return False
        else:
            logger.error(f"❌ Ошибка при отключении webhook: {delete_response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при отключении webhook: {e}")
        return False

def test_bot_api():
    """
    Проверяет доступность Bot API
    
    Returns:
        bool: True если API доступен, False в противном случае
    """
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('first_name', 'Unknown')
            bot_username = bot_info.get('username', 'Unknown')
            logger.info(f"✅ Bot API доступен. Имя бота: {bot_name}, username: @{bot_username}")
            return True
        else:
            logger.error(f"❌ Ошибка при проверке Bot API: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при проверке Bot API: {e}")
        return False

def check_railway_service():
    """
    Проверяет доступность сервиса на Railway
    
    Returns:
        bool: True если сервис доступен, False в противном случае
    """
    service_url = get_railway_service_url()
    if not service_url:
        logger.error("❌ Не удалось определить URL сервиса для проверки")
        return False
    
    health_url = f"{service_url}/health"
    logger.info(f"🔄 Проверяем доступность сервиса на URL: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        logger.info(f"✅ Ответ от сервиса: код {response.status_code}, тело: {response.text[:200]}...")
        
        if response.status_code == 200:
            logger.info("✅ Сервис доступен и возвращает 200 OK")
            return True
        else:
            logger.warning(f"⚠️ Сервис вернул код {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке доступности сервиса: {e}")
        return False

def send_test_message(chat_id=None):
    """
    Отправляет тестовое сообщение от имени бота
    
    Args:
        chat_id (str, optional): ID чата для отправки сообщения. Если не указан, будет использован ADMIN_CHAT_ID.
        
    Returns:
        bool: True если сообщение успешно отправлено, False в противном случае
    """
    if not chat_id:
        chat_id = os.environ.get('ADMIN_CHAT_ID')
        if not chat_id:
            logger.warning("⚠️ Не указан ADMIN_CHAT_ID для отправки тестового сообщения")
            return False
    
    logger.info(f"🔄 Отправляем тестовое сообщение в чат {chat_id}")
    
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': "🤖 Тестовое сообщение от бота. Проверка работоспособности после настройки webhook."
        }
        
        response = requests.post(api_url, json=data, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Тестовое сообщение успешно отправлено")
            return True
        else:
            logger.error(f"❌ Ошибка при отправке тестового сообщения: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Исключение при отправке тестового сообщения: {e}")
        return False

async def webhook_test_loop():
    """
    Асинхронный цикл для тестирования работы webhook
    Отправляет сообщения и проверяет ответы на них
    """
    logger.info("🔄 Запуск асинхронного теста webhook...")
    
    # Отправляем тестовые команды и проверяем ответы
    commands = ['/start', '/help', '/about']
    admin_id = os.environ.get('ADMIN_CHAT_ID')
    
    if not admin_id:
        logger.warning("⚠️ Не указан ADMIN_CHAT_ID для тестирования команд")
        return
    
    for command in commands:
        logger.info(f"🔄 Тестирование команды: {command}")
        
        try:
            # Отправляем команду
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': admin_id,
                'text': command
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data, timeout=10) as response:
                    response_json = await response.json()
                    
                    if response.status == 200 and response_json.get('ok'):
                        logger.info(f"✅ Команда {command} успешно отправлена")
                    else:
                        logger.error(f"❌ Ошибка при отправке команды {command}: {await response.text()}")
            
            # Ждем немного, чтобы бот успел обработать команду
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Исключение при тестировании команды {command}: {e}")
    
    logger.info("✅ Тестирование webhook завершено")

def main():
    """
    Основная функция для исправления и проверки бота
    """
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Утилита для исправления и проверки Telegram бота на Railway')
    parser.add_argument('--disable-webhook', action='store_true', help='Отключить webhook для перехода в режим polling')
    parser.add_argument('--set-webhook', action='store_true', help='Установить webhook (используется по умолчанию)')
    parser.add_argument('--webhook-url', type=str, help='URL для webhook (если не указан, будет определен автоматически)')
    parser.add_argument('--drop-updates', action='store_true', help='Сбросить накопившиеся обновления')
    parser.add_argument('--test-message', action='store_true', help='Отправить тестовое сообщение')
    parser.add_argument('--chat-id', type=str, help='ID чата для отправки тестового сообщения')
    parser.add_argument('--check-service', action='store_true', help='Проверить доступность сервиса на Railway')
    args = parser.parse_args()
    
    logger.info("=== Начало проверки и исправления бота ===")
    
    # Шаг 1: Проверка Bot API
    if not test_bot_api():
        logger.error("❌ Bot API недоступен. Проверьте токен бота и доступ к Telegram API")
        return
    
    # Шаг 2: Отключение webhook (если запрошено)
    if args.disable_webhook:
        logger.info("🔄 Отключение webhook по запросу пользователя")
        if disable_webhook(drop_pending_updates=args.drop_updates):
            logger.info("✅ Webhook успешно отключен. Теперь вы можете запустить бота в режиме polling")
            
            # Отправка тестового сообщения
            if args.test_message or args.chat_id:
                send_test_message(args.chat_id)
            
            return
    
    # Шаг 3: Проверка текущего webhook
    webhook_info = get_webhook_info()
    if webhook_info:
        webhook_url = webhook_info.get('url')
        last_error = webhook_info.get('last_error_message')
        
        if args.set_webhook or not args.disable_webhook:
            if webhook_url and "healthcheck.railway.app" in webhook_url:
                logger.warning(f"⚠️ Обнаружен некорректный webhook URL: {webhook_url}")
                logger.info("🔄 Необходимо переустановить webhook")
                setup_webhook(args.webhook_url, drop_pending_updates=args.drop_updates)
            elif last_error:
                logger.warning(f"⚠️ Обнаружена ошибка в работе webhook: {last_error}")
                logger.info("🔄 Переустанавливаем webhook для устранения ошибки")
                setup_webhook(args.webhook_url, drop_pending_updates=args.drop_updates)
            elif not webhook_url:
                logger.warning("⚠️ Webhook не установлен")
                logger.info("🔄 Устанавливаем webhook")
                setup_webhook(args.webhook_url, drop_pending_updates=args.drop_updates)
            else:
                logger.info(f"✅ Webhook уже настроен на URL: {webhook_url}")
    else:
        logger.warning("⚠️ Не удалось получить информацию о webhook")
        if args.set_webhook or not args.disable_webhook:
            logger.info("🔄 Устанавливаем webhook")
            setup_webhook(args.webhook_url, drop_pending_updates=args.drop_updates)
    
    # Шаг 4: Проверка доступности сервиса на Railway
    if args.check_service:
        if not check_railway_service():
            logger.warning("⚠️ Сервис на Railway недоступен или возвращает ошибку")
            logger.info("🔄 Проверьте деплой на Railway и логи сервиса")
    
    # Шаг 5: Отправка тестового сообщения
    if args.test_message or args.chat_id:
        send_test_message(args.chat_id)
    
    # Шаг 6: Асинхронное тестирование webhook
    if args.set_webhook or not args.disable_webhook:
        asyncio.run(webhook_test_loop())
    
    logger.info("=== Проверка и исправление бота завершены ===")

if __name__ == "__main__":
    main() 