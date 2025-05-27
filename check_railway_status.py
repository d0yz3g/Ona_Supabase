#!/usr/bin/env python
"""
Скрипт для проверки статуса приложения на Railway
"""

import os
import sys
import json
import requests
import argparse
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_bot_info(bot_token):
    """Получает информацию о боте"""
    try:
        print(f"🔍 Получение информации о боте...")
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        
        if response.status_code == 200 and response.json().get("ok"):
            bot_info = response.json().get("result", {})
            print(f"✅ Бот найден: {bot_info.get('first_name')} (@{bot_info.get('username')})")
            return bot_info
        else:
            print(f"❌ Ошибка при получении информации о боте: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение при получении информации о боте: {e}")
        return None

def get_webhook_info(bot_token):
    """Получает информацию о настройках webhook"""
    try:
        print(f"🔍 Получение информации о webhook...")
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10)
        
        if response.status_code == 200 and response.json().get("ok"):
            webhook_info = response.json().get("result", {})
            webhook_url = webhook_info.get("url", "")
            last_error = webhook_info.get("last_error_message", "нет")
            pending_updates = webhook_info.get("pending_update_count", 0)
            
            print(f"ℹ️ Текущий webhook URL: {webhook_url}")
            print(f"ℹ️ Последняя ошибка: {last_error}")
            print(f"ℹ️ Ожидающие обновления: {pending_updates}")
            
            return webhook_info
        else:
            print(f"❌ Ошибка при получении информации о webhook: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение при получении информации о webhook: {e}")
        return None

def check_railway_app(webhook_url=None):
    """Проверяет статус приложения на Railway"""
    if not webhook_url:
        webhook_url = os.environ.get("WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ URL webhook не найден")
        return False
    
    # Извлекаем базовый URL (без /webhook/...)
    if "/webhook/" in webhook_url:
        railway_url = webhook_url.split("/webhook/")[0]
    else:
        railway_url = webhook_url
    
    try:
        print(f"🔍 Проверка статуса приложения на Railway: {railway_url}")
        
        # Проверяем endpoint /health
        health_url = f"{railway_url}/health"
        health_response = requests.get(health_url, timeout=10)
        
        if health_response.status_code == 200:
            print(f"✅ Health endpoint доступен: {health_response.text}")
        else:
            print(f"❌ Health endpoint недоступен: {health_response.status_code} - {health_response.text}")
        
        # Проверяем корневой endpoint
        root_response = requests.get(railway_url, timeout=10)
        
        if root_response.status_code == 200:
            print(f"✅ Корневой endpoint доступен")
        else:
            print(f"❌ Корневой endpoint недоступен: {root_response.status_code}")
        
        # Возвращаем True, если хотя бы один из эндпоинтов доступен
        return health_response.status_code == 200 or root_response.status_code == 200
    
    except Exception as e:
        print(f"❌ Исключение при проверке приложения на Railway: {e}")
        return False

def check_webhook_connection(webhook_url, bot_token):
    """Проверяет соединение с webhook отправкой тестового запроса"""
    if not webhook_url:
        print("❌ URL webhook не найден")
        return False
    
    try:
        print(f"🔍 Проверка соединения с webhook: {webhook_url}")
        
        # Формируем тестовый запрос
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
        
        # Отправляем запрос
        response = requests.post(webhook_url, json=test_data, timeout=10)
        
        print(f"ℹ️ Код ответа: {response.status_code}")
        print(f"ℹ️ Текст ответа: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook обрабатывает запросы корректно")
            return True
        else:
            print(f"❌ Webhook не обрабатывает запросы: {response.status_code} - {response.text}")
            
            # Проверяем, является ли ошибка 404 (Not Found)
            if response.status_code == 404:
                print("⚠️ Ошибка 404 указывает на проблему с маршрутизацией в приложении")
                print("⚠️ Рекомендуется проверить, корректно ли настроен обработчик webhook в webhook_server.py")
            
            return False
    except Exception as e:
        print(f"❌ Исключение при проверке соединения с webhook: {e}")
        return False

def generate_report(bot_token, webhook_url=None):
    """Генерирует полный отчет о состоянии бота и приложения"""
    print("🚀 Запуск диагностики бота и приложения на Railway")
    print("=" * 80)
    
    # Получаем информацию о боте
    bot_info = get_bot_info(bot_token)
    if not bot_info:
        print("❌ Не удалось получить информацию о боте. Проверьте BOT_TOKEN.")
        return False
    
    print("=" * 80)
    
    # Получаем информацию о webhook
    webhook_info = get_webhook_info(bot_token)
    if not webhook_info:
        print("❌ Не удалось получить информацию о webhook.")
        return False
    
    # Используем URL из webhook_info, если не указан явно
    if not webhook_url and webhook_info:
        webhook_url = webhook_info.get("url", "")
    
    print("=" * 80)
    
    # Проверяем приложение на Railway
    railway_status = check_railway_app(webhook_url)
    if not railway_status:
        print("❌ Приложение на Railway недоступно.")
        print("⚠️ Рекомендуется проверить настройки на Railway и перезапустить приложение")
        return False
    
    print("=" * 80)
    
    # Проверяем соединение с webhook
    webhook_connection = check_webhook_connection(webhook_url, bot_token)
    if not webhook_connection:
        print("❌ Соединение с webhook не работает.")
        print("⚠️ Рекомендуется проверить код обработки webhook в приложении")
        return False
    
    print("=" * 80)
    print("✅ Все проверки успешно пройдены!")
    print("🎉 Бот и приложение на Railway должны работать корректно.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Проверка статуса приложения на Railway")
    parser.add_argument("--token", help="Токен бота Telegram")
    parser.add_argument("--webhook", help="URL webhook для проверки")
    parser.add_argument("--report", action="store_true", help="Сгенерировать полный отчет")
    args = parser.parse_args()
    
    # Получаем токен бота из аргументов или из .env
    bot_token = args.token or os.environ.get("BOT_TOKEN")
    if not bot_token:
        print("❌ Не указан токен бота. Используйте --token или добавьте BOT_TOKEN в .env")
        sys.exit(1)
    
    # Получаем URL webhook из аргументов или из .env
    webhook_url = args.webhook or os.environ.get("WEBHOOK_URL")
    
    # Генерируем полный отчет, если указан флаг --report
    if args.report:
        success = generate_report(bot_token, webhook_url)
        sys.exit(0 if success else 1)
    
    # Иначе проверяем только статус приложения
    railway_status = check_railway_app(webhook_url)
    sys.exit(0 if railway_status else 1) 