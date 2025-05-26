#!/usr/bin/env python
"""
Простой единый сервер для Railway
Обрабатывает и health check, и webhook запросы от Telegram
"""

import os
import sys
import json
import logging
import asyncio
import requests
from aiohttp import web
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [SERVER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("simple_server")

# Загружаем переменные окружения
load_dotenv()

# Логируем информацию о Railway для отладки
logger.info("=== Информация о Railway ===")
logger.info(f"RAILWAY_PUBLIC_DOMAIN: {os.environ.get('RAILWAY_PUBLIC_DOMAIN')}")
logger.info(f"RAILWAY_SERVICE_ID: {os.environ.get('RAILWAY_SERVICE_ID')}")
logger.info(f"RAILWAY_PROJECT_ID: {os.environ.get('RAILWAY_PROJECT_ID')}")
logger.info(f"RAILWAY_SERVICE_NAME: {os.environ.get('RAILWAY_SERVICE_NAME')}")
logger.info("==========================")

# Получаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
    sys.exit(1)

def setup_webhook():
    """
    Настраивает webhook для Telegram-бота
    
    Returns:
        bool: True если webhook успешно настроен, False в противном случае
    """
    # Получаем необходимые переменные
    webhook_url = os.environ.get('WEBHOOK_URL')
    railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    railway_service_id = os.environ.get('RAILWAY_SERVICE_ID')
    railway_project_id = os.environ.get('RAILWAY_PROJECT_ID')
    
    # Формируем URL для webhook
    if webhook_url:
        # Если напрямую указан WEBHOOK_URL, используем его
        logger.info(f"Используется предоставленный WEBHOOK_URL: {webhook_url}")
    elif railway_public_domain:
        # Формируем из RAILWAY_PUBLIC_DOMAIN
        webhook_url = f"https://{railway_public_domain}/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе Railway-домена: {webhook_url}")
    elif railway_service_id and railway_project_id:
        # Формируем из ID сервиса и проекта Railway
        webhook_url = f"https://{railway_service_id}.up.railway.app/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе ID сервиса Railway: {webhook_url}")
    else:
        # Если нет информации для формирования URL, пропускаем настройку webhook
        logger.warning("⚠️ Не удалось определить URL для webhook, работаем без него")
        logger.warning("⚠️ Установите переменную WEBHOOK_URL для правильной работы webhook")
        return False
    
    logger.info(f"Настройка webhook для бота с токеном: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
    logger.info(f"Webhook URL: {webhook_url}")
    
    # Формируем URL для API Telegram
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
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
            description = response.json().get('description', 'Нет описания')
            logger.info(f"✅ Webhook успешно установлен: {description}")
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при настройке webhook: {e}")
        return False

async def forward_to_telegram(update_data):
    """
    Пересылает данные от webhook к API Telegram для обработки
    
    Args:
        update_data (dict): Данные от Telegram webhook
        
    Returns:
        bool: True если успешно, False в противном случае
    """
    try:
        # Получаем метод для вызова на основе типа обновления
        method = None
        
        if 'message' in update_data:
            chat_id = update_data['message']['chat']['id']
            text = update_data['message'].get('text', '')
            
            if text.startswith('/'):
                # Обрабатываем команды
                command = text.split()[0].lower()
                
                if command == '/start':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "Привет! Я бот Она. Чем могу помочь?"
                    }
                elif command == '/help':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "Доступные команды:\n/start - Начать диалог\n/help - Помощь"
                    }
                else:
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': f"Команда {command} не распознана."
                    }
            else:
                # Простой ответ на текстовое сообщение
                method = "sendMessage"
                params = {
                    'chat_id': chat_id,
                    'text': f"Вы написали: {text}"
                }
        
        # Если метод был определен, вызываем API
        if method:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
            response = requests.post(api_url, json=params)
            
            if response.status_code == 200:
                logger.info(f"✅ API вызов успешен: {method}")
                return True
            else:
                logger.error(f"❌ Ошибка при вызове API {method}: {response.text}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при пересылке данных в Telegram: {e}")
        return False

async def start_simple_server():
    """
    Запускает простой веб-сервер для обработки запросов
    """
    # Создаем веб-приложение
    app = web.Application()
    
    # Для хранения информации о хосте из запросов health check
    host_info = {'detected_host': None}
    
    # Обработчик для корневого пути (для проверки доступности)
    async def health_check(request):
        # Сохраняем информацию о хосте для определения webhook URL
        if not host_info['detected_host'] and 'Host' in request.headers:
            host = request.headers.get('Host')
            host_info['detected_host'] = host
            logger.info(f"Обнаружен хост из заголовка запроса: {host}")
            
            # Пробуем настроить webhook с обнаруженным хостом
            if BOT_TOKEN and not os.environ.get('WEBHOOK_URL'):
                webhook_url = f"https://{host}/webhook/{BOT_TOKEN}"
                logger.info(f"Попытка настройки webhook с обнаруженным хостом: {webhook_url}")
                
                # Устанавливаем WEBHOOK_URL для последующих вызовов setup_webhook
                os.environ['WEBHOOK_URL'] = webhook_url
                
                # Вызываем настройку webhook
                setup_webhook()
        
        return web.Response(
            text="OK - Bot is healthy and running",
            status=200,
            content_type="text/plain"
        )
    
    # Обработчик для webhook
    async def webhook_handler(request):
        if request.match_info.get('token') != BOT_TOKEN:
            return web.Response(status=403, text="Forbidden")
        
        try:
            # Получаем данные запроса
            update_data = await request.json()
            logger.info(f"Получен webhook-запрос: {json.dumps(update_data, ensure_ascii=False)}")
            
            # Пересылаем данные в Telegram API
            asyncio.create_task(forward_to_telegram(update_data))
            
            # Возвращаем успешный ответ
            return web.Response(status=200, text="OK")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке webhook-запроса: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    # Регистрируем обработчики
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)
    
    # Получаем порт из переменных окружения
    port = int(os.environ.get("PORT", 8080))
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    # Настраиваем webhook
    if not setup_webhook():
        logger.warning("⚠️ Не удалось настроить webhook, но сервер будет запущен")
    
    # Запускаем веб-сервер
    logger.info(f"Запуск сервера на порту {port}...")
    await site.start()
    logger.info(f"✅ Сервер успешно запущен на порту {port}")
    
    # Ждем завершения
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logger.info("Запуск простого сервера для Railway...")
    
    try:
        # Запускаем сервер
        asyncio.run(start_simple_server())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске сервера: {e}")
        sys.exit(1) 