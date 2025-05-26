#!/usr/bin/env python
"""
Скрипт для запуска бота в режиме поллинга для отладки
"""

import os
import sys
import json
import logging
import time
import asyncio
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POLLING_BOT] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("polling_bot")

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
    sys.exit(1)

# Последний полученный update_id
last_update_id = 0

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

def get_updates():
    """Получает обновления от Telegram API"""
    global last_update_id
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {
        'timeout': 30,
        'allowed_updates': ['message', 'callback_query', 'inline_query']
    }
    
    # Если есть последний update_id, добавляем его + 1
    if last_update_id > 0:
        params['offset'] = last_update_id + 1
    
    try:
        response = requests.get(api_url, params=params, timeout=35)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result.get('result'):
                updates = result['result']
                if updates:
                    # Обновляем last_update_id
                    last_update_id = max(update['update_id'] for update in updates)
                return updates
            return []
        else:
            logger.error(f"❌ Ошибка при получении обновлений: {response.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Исключение при получении обновлений: {e}")
        return []

async def handle_message(message):
    """Обрабатывает сообщение от пользователя"""
    chat_id = message['chat']['id']
    text = message.get('text', '')
    
    # Логируем сообщение от пользователя
    user_info = message['from']
    username = user_info.get('username', 'нет')
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    logger.info(f"📩 Получено сообщение от пользователя @{username} ({first_name} {last_name}): {text}")
    
    # Определяем ответ
    response_text = None
    
    if text and text.startswith('/'):
        # Обрабатываем команды
        command = text.split()[0].lower()
        logger.info(f"🔄 Обработка команды: {command}")
        
        if command == '/start':
            response_text = "👋 Привет! Я Она - твой бот-помощник.\n\nЯ могу помочь тебе разобраться в себе и своих эмоциях.\n\nНапиши /help чтобы узнать, что я умею."
            logger.info(f"🤖 Отправляем ответ на команду /start пользователю {chat_id}")
        elif command == '/help':
            response_text = "📋 Доступные команды:\n\n/start - Начать диалог\n/help - Показать эту справку\n/about - О боте\n/meditate - Получить медитацию"
            logger.info(f"🤖 Отправляем ответ на команду /help пользователю {chat_id}")
        elif command == '/about':
            response_text = "ℹ️ Я - Она, бот-помощник, созданный чтобы помогать тебе в трудные моменты. Я использую современные технологии искусственного интеллекта для анализа твоих сообщений и предоставления поддержки."
            logger.info(f"🤖 Отправляем ответ на команду /about пользователю {chat_id}")
        elif command == '/meditate':
            response_text = "🧘‍♀️ Медитация поможет тебе успокоиться и сосредоточиться. Глубоко вдохни и медленно выдохни. Повторяй этот процесс, концентрируясь на своем дыхании."
            logger.info(f"🤖 Отправляем ответ на команду /meditate пользователю {chat_id}")
        else:
            response_text = f"🤔 Команда {command} не распознана. Напиши /help чтобы увидеть список команд."
            logger.info(f"🤖 Отправляем ответ на неизвестную команду {command} пользователю {chat_id}")
    else:
        # Эхо-ответ на текстовое сообщение (в будущем здесь будет интеграция с OpenAI)
        response_text = f"🤖 Ты написал: {text}\n\nВ будущих версиях я смогу поддерживать полноценный диалог."
        logger.info(f"🤖 Отправляем эхо-ответ пользователю {chat_id}")
    
    # Отправляем ответ
    if response_text:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            'chat_id': chat_id,
            'text': response_text
        }
        
        try:
            response = requests.post(api_url, json=params, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Сообщение успешно отправлено пользователю {chat_id}")
            else:
                logger.error(f"❌ Ошибка при отправке сообщения: {response.text}")
        except Exception as e:
            logger.error(f"❌ Исключение при отправке сообщения: {e}")

async def handle_callback_query(callback_query):
    """Обрабатывает callback_query от inline-кнопок"""
    callback_id = callback_query['id']
    data = callback_query.get('data', '')
    
    logger.info(f"📩 Получен callback_query с данными: {data}")
    
    # Отвечаем на callback_query
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    params = {
        'callback_query_id': callback_id,
        'text': f"Выбрано: {data}"
    }
    
    try:
        response = requests.post(api_url, json=params, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Ответ на callback_query успешно отправлен")
        else:
            logger.error(f"❌ Ошибка при отправке ответа на callback_query: {response.text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке ответа на callback_query: {e}")

async def process_updates(updates):
    """Обрабатывает полученные обновления"""
    for update in updates:
        logger.info(f"🔄 Обработка update_id={update['update_id']}")
        
        if 'message' in update:
            await handle_message(update['message'])
        elif 'callback_query' in update:
            await handle_callback_query(update['callback_query'])
        else:
            logger.warning(f"⚠️ Неизвестный тип обновления: {update}")

async def main_loop():
    """Основной цикл бота"""
    logger.info("🚀 Запуск бота в режиме поллинга...")
    
    # Удаляем webhook, если он был настроен
    if not delete_webhook():
        logger.warning("⚠️ Не удалось удалить webhook, возможны проблемы с получением обновлений")
    
    # Запускаем цикл поллинга
    while True:
        try:
            updates = get_updates()
            if updates:
                logger.info(f"ℹ️ Получено {len(updates)} обновлений")
                await process_updates(updates)
            else:
                logger.info("ℹ️ Нет новых обновлений")
        except Exception as e:
            logger.error(f"❌ Ошибка в главном цикле: {e}")
        
        # Короткая пауза перед следующим запросом (не обязательно, но полезно для отладки)
        # await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 