#!/usr/bin/env python
"""
Скрипт для проверки состояния сервиса на Railway
Позволяет диагностировать проблемы с деплоем и webhook
"""

import os
import sys
import time
import json
import logging
import requests
from dotenv import load_dotenv
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [CHECK_RAILWAY] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("railway_check.log")
    ]
)
logger = logging.getLogger("check_railway")

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена. Укажите BOT_TOKEN в .env или переменных окружения")
    sys.exit(1)

def check_bot_api():
    """
    Проверяет доступность Bot API
    
    Returns:
        dict: Информация о боте или None в случае ошибки
    """
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('first_name', 'Unknown')
            bot_username = bot_info.get('username', 'Unknown')
            logger.info(f"✅ Bot API доступен. Имя бота: {bot_name}, username: @{bot_username}")
            return bot_info
        else:
            logger.error(f"❌ Ошибка при проверке Bot API: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при проверке Bot API: {e}")
        return None

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

def check_railway_env():
    """
    Проверяет наличие и корректность переменных окружения Railway
    
    Returns:
        dict: Переменные окружения Railway
    """
    railway_vars = {
        'RAILWAY_SERVICE_ID': os.environ.get('RAILWAY_SERVICE_ID'),
        'RAILWAY_PROJECT_ID': os.environ.get('RAILWAY_PROJECT_ID'),
        'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN'),
        'RAILWAY_SERVICE_NAME': os.environ.get('RAILWAY_SERVICE_NAME'),
        'WEBHOOK_URL': os.environ.get('WEBHOOK_URL'),
        'WEBHOOK_HOST': os.environ.get('WEBHOOK_HOST'),
        'PORT': os.environ.get('PORT', '8080')
    }
    
    logger.info("=== Переменные окружения Railway ===")
    for key, value in railway_vars.items():
        status = "✅" if value else "❌"
        masked_value = value if key not in ['WEBHOOK_URL', 'WEBHOOK_HOST'] else f"{value[:15]}..." if value else None
        logger.info(f"{status} {key}: {masked_value}")
    logger.info("===================================")
    
    return railway_vars

def check_railway_service():
    """
    Проверяет доступность сервиса на Railway
    
    Returns:
        dict: Результаты проверки или None в случае ошибки
    """
    # Получаем URL сервиса
    service_url = None
    
    # Проверяем WEBHOOK_URL
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        from urllib.parse import urlparse
        parsed_url = urlparse(webhook_url)
        if parsed_url.netloc and "healthcheck.railway.app" not in parsed_url.netloc:
            service_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Проверяем RAILWAY_PUBLIC_DOMAIN
    if not service_url:
        railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_public_domain and "healthcheck.railway.app" not in railway_public_domain:
            service_url = f"https://{railway_public_domain}"
    
    # Проверяем RAILWAY_SERVICE_ID
    if not service_url:
        railway_service_id = os.environ.get('RAILWAY_SERVICE_ID')
        if railway_service_id:
            service_url = f"https://{railway_service_id}.up.railway.app"
    
    # Проверяем информацию о webhook
    if not service_url:
        webhook_info = get_webhook_info()
        if webhook_info and webhook_info.get('url'):
            from urllib.parse import urlparse
            parsed_url = urlparse(webhook_info.get('url'))
            if parsed_url.netloc and "healthcheck.railway.app" not in parsed_url.netloc:
                service_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    if not service_url:
        logger.error("❌ Не удалось определить URL сервиса")
        return None
    
    logger.info(f"🔄 Проверяем доступность сервиса на URL: {service_url}")
    
    results = {}
    
    # Проверяем корневой URL
    try:
        root_url = service_url
        logger.info(f"🔄 Проверка корневого URL: {root_url}")
        response = requests.get(root_url, timeout=10)
        results['root'] = {
            'url': root_url,
            'status_code': response.status_code,
            'response': response.text[:200] + "..." if len(response.text) > 200 else response.text
        }
        
        if response.status_code == 200:
            logger.info(f"✅ Корневой URL доступен: {root_url}")
        else:
            logger.warning(f"⚠️ Корневой URL вернул код {response.status_code}: {root_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке корневого URL: {e}")
        results['root'] = {
            'url': root_url,
            'error': str(e)
        }
    
    # Проверяем /health URL
    try:
        health_url = f"{service_url}/health"
        logger.info(f"🔄 Проверка URL для health check: {health_url}")
        response = requests.get(health_url, timeout=10)
        results['health'] = {
            'url': health_url,
            'status_code': response.status_code,
            'response': response.text[:200] + "..." if len(response.text) > 200 else response.text
        }
        
        if response.status_code == 200:
            logger.info(f"✅ URL для health check доступен: {health_url}")
        else:
            logger.warning(f"⚠️ URL для health check вернул код {response.status_code}: {health_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке URL для health check: {e}")
        results['health'] = {
            'url': health_url,
            'error': str(e)
        }
    
    # Проверяем webhook URL
    webhook_path = f"{service_url}/webhook/{BOT_TOKEN}"
    try:
        logger.info(f"🔄 Проверка URL для webhook: {webhook_path}")
        # Для webhook используем POST, так как GET может не поддерживаться
        response = requests.post(webhook_path, json={'test': True}, timeout=10)
        results['webhook'] = {
            'url': webhook_path,
            'status_code': response.status_code,
            'response': response.text[:200] + "..." if len(response.text) > 200 else response.text
        }
        
        if response.status_code in [200, 400, 401, 403]:  # Приемлемые коды для webhook (400 может означать неверный формат сообщения)
            logger.info(f"✅ URL для webhook доступен: {webhook_path}")
        else:
            logger.warning(f"⚠️ URL для webhook вернул код {response.status_code}: {webhook_path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке URL для webhook: {e}")
        results['webhook'] = {
            'url': webhook_path,
            'error': str(e)
        }
    
    return results

def check_webhook_operation():
    """
    Проверяет работоспособность webhook
    
    Returns:
        bool: True если webhook работает корректно, False в противном случае
    """
    webhook_info = get_webhook_info()
    if not webhook_info:
        logger.error("❌ Не удалось получить информацию о webhook")
        return False
    
    webhook_url = webhook_info.get('url')
    if not webhook_url:
        logger.warning("⚠️ Webhook не установлен")
        return False
    
    last_error = webhook_info.get('last_error_message')
    if last_error:
        logger.warning(f"⚠️ Последняя ошибка webhook: {last_error}")
        return False
    
    pending_updates = webhook_info.get('pending_update_count', 0)
    logger.info(f"ℹ️ Ожидающие обновления: {pending_updates}")
    
    if "healthcheck.railway.app" in webhook_url:
        logger.error(f"❌ Webhook установлен на healthcheck.railway.app: {webhook_url}")
        return False
    
    logger.info(f"✅ Webhook настроен правильно: {webhook_url}")
    return True

def send_test_message(chat_id=None):
    """
    Отправляет тестовое сообщение от имени бота
    
    Args:
        chat_id (str, optional): ID чата для отправки сообщения. Если не указан, будет использован ADMIN_CHAT_ID.
        
    Returns:
        dict: Результат отправки сообщения или None в случае ошибки
    """
    if not chat_id:
        chat_id = os.environ.get('ADMIN_CHAT_ID')
        if not chat_id:
            logger.warning("⚠️ Не указан ADMIN_CHAT_ID для отправки тестового сообщения")
            return None
    
    logger.info(f"🔄 Отправляем тестовое сообщение в чат {chat_id}")
    
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': "🤖 Тестовое сообщение от скрипта проверки Railway. Проверка работоспособности бота."
        }
        
        response = requests.post(api_url, json=data, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            message_info = response.json().get('result', {})
            logger.info("✅ Тестовое сообщение успешно отправлено")
            return message_info
        else:
            logger.error(f"❌ Ошибка при отправке тестового сообщения: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при отправке тестового сообщения: {e}")
        return None

def generate_report(results):
    """
    Генерирует отчет о результатах проверки
    
    Args:
        results (dict): Результаты проверки
        
    Returns:
        str: Отчет в формате текста
    """
    report = "=== ОТЧЕТ О СОСТОЯНИИ БОТА И RAILWAY СЕРВИСА ===\n\n"
    
    # Информация о боте
    bot_info = results.get('bot_info')
    if bot_info:
        report += f"БОТ: {bot_info.get('first_name')} (@{bot_info.get('username')})\n"
        report += f"ID бота: {bot_info.get('id')}\n"
        report += f"Поддерживает Inline: {bot_info.get('supports_inline_queries', False)}\n\n"
    else:
        report += "БОТ: Информация не доступна\n\n"
    
    # Информация о webhook
    webhook_info = results.get('webhook_info')
    if webhook_info:
        report += f"WEBHOOK URL: {webhook_info.get('url')}\n"
        report += f"Ожидающие обновления: {webhook_info.get('pending_update_count', 0)}\n"
        report += f"Последняя ошибка: {webhook_info.get('last_error_message', 'нет')}\n"
        report += f"Максимальные соединения: {webhook_info.get('max_connections', 40)}\n\n"
    else:
        report += "WEBHOOK: Информация не доступна\n\n"
    
    # Информация о Railway
    railway_env = results.get('railway_env', {})
    report += "RAILWAY ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:\n"
    for key, value in railway_env.items():
        if key in ['WEBHOOK_URL', 'WEBHOOK_HOST']:
            masked_value = f"{value[:15]}..." if value else "не задано"
            report += f"- {key}: {masked_value}\n"
        else:
            report += f"- {key}: {value or 'не задано'}\n"
    report += "\n"
    
    # Результаты проверки сервиса
    service_results = results.get('service_results', {})
    if service_results:
        report += "ПРОВЕРКА СЕРВИСА:\n"
        
        # Корневой URL
        root_check = service_results.get('root', {})
        if 'error' in root_check:
            report += f"- Корневой URL ({root_check.get('url')}): ОШИБКА - {root_check.get('error')}\n"
        else:
            report += f"- Корневой URL ({root_check.get('url')}): код {root_check.get('status_code')}\n"
        
        # Health URL
        health_check = service_results.get('health', {})
        if 'error' in health_check:
            report += f"- Health URL ({health_check.get('url')}): ОШИБКА - {health_check.get('error')}\n"
        else:
            report += f"- Health URL ({health_check.get('url')}): код {health_check.get('status_code')}\n"
        
        # Webhook URL
        webhook_check = service_results.get('webhook', {})
        if 'error' in webhook_check:
            report += f"- Webhook URL ({webhook_check.get('url')}): ОШИБКА - {webhook_check.get('error')}\n"
        else:
            report += f"- Webhook URL ({webhook_check.get('url')}): код {webhook_check.get('status_code')}\n"
    else:
        report += "ПРОВЕРКА СЕРВИСА: Не выполнена\n"
    
    report += "\n"
    
    # Результаты тестового сообщения
    test_message = results.get('test_message')
    if test_message:
        report += "ТЕСТОВОЕ СООБЩЕНИЕ: Успешно отправлено\n"
        report += f"- Message ID: {test_message.get('message_id')}\n"
        report += f"- Дата отправки: {test_message.get('date')}\n"
    else:
        report += "ТЕСТОВОЕ СООБЩЕНИЕ: Не отправлено\n"
    
    report += "\n"
    
    # Заключение
    webhook_operation = results.get('webhook_operation', False)
    if webhook_operation:
        report += "✅ ЗАКЛЮЧЕНИЕ: Webhook настроен правильно и работает\n"
    else:
        report += "❌ ЗАКЛЮЧЕНИЕ: Webhook не работает или настроен неправильно\n"
    
    return report

def main():
    """
    Основная функция скрипта
    """
    parser = argparse.ArgumentParser(description='Скрипт для проверки состояния сервиса на Railway')
    parser.add_argument('--fix', action='store_true', help='Исправить проблемы с webhook')
    parser.add_argument('--test', action='store_true', help='Отправить тестовое сообщение')
    parser.add_argument('--chat-id', type=str, help='ID чата для отправки тестового сообщения')
    parser.add_argument('--report', action='store_true', help='Сгенерировать отчет')
    parser.add_argument('--output', type=str, help='Путь к файлу для сохранения отчета')
    args = parser.parse_args()
    
    logger.info("=== Начало проверки состояния Railway сервиса ===")
    
    # Сохраняем результаты всех проверок
    results = {}
    
    # Проверка Bot API
    results['bot_info'] = check_bot_api()
    
    # Проверка webhook
    results['webhook_info'] = get_webhook_info()
    
    # Проверка переменных окружения
    results['railway_env'] = check_railway_env()
    
    # Проверка сервиса
    results['service_results'] = check_railway_service()
    
    # Проверка работы webhook
    results['webhook_operation'] = check_webhook_operation()
    
    # Отправка тестового сообщения
    if args.test or args.chat_id:
        results['test_message'] = send_test_message(args.chat_id)
    
    # Генерация отчета
    if args.report or args.output:
        report = generate_report(results)
        logger.info(f"\n{report}")
        
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"✅ Отчет сохранен в файл: {args.output}")
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении отчета в файл: {e}")
    
    # Исправление проблем с webhook
    if args.fix and not results.get('webhook_operation', False):
        logger.info("🔄 Исправление проблем с webhook...")
        
        from railway_fix import setup_webhook
        setup_webhook()
        
        # Проверяем результат исправления
        results['webhook_info_after_fix'] = get_webhook_info()
        results['webhook_operation_after_fix'] = check_webhook_operation()
        
        if results.get('webhook_operation_after_fix', False):
            logger.info("✅ Проблемы с webhook успешно исправлены")
        else:
            logger.error("❌ Не удалось исправить проблемы с webhook")
    
    logger.info("=== Проверка состояния Railway сервиса завершена ===")

if __name__ == "__main__":
    main() 