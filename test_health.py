#!/usr/bin/env python
"""
Тестирование доступности и работоспособности бота
Проверяет доступность health check эндпоинта и основные функции бота
"""

import os
import sys
import time
import json
import logging
import asyncio
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [TEST] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("health_test.log")]
)
logger = logging.getLogger("health_test")

# Загружаем переменные окружения
load_dotenv()

def check_health_endpoint(url=None, port=None, timeout=5):
    """
    Проверяет доступность health check эндпоинта
    
    Args:
        url (str, optional): URL для проверки. Если не указан, 
                            будет использоваться localhost с указанным портом.
        port (int, optional): Порт для проверки. По умолчанию 8080.
        timeout (int, optional): Таймаут запроса в секундах. По умолчанию 5.
    
    Returns:
        dict: Результат проверки
    """
    if not url:
        if not port:
            port = int(os.environ.get("PORT", 8080))
        url = f"http://localhost:{port}/health"
    
    logger.info(f"Проверка health check эндпоинта: {url}")
    
    result = {
        "success": False,
        "status_code": None,
        "response": None,
        "error": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Запрос с указанием формата ответа
        headers = {"Accept": "application/json"}
        response = requests.get(url, timeout=timeout, headers=headers)
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["success"] = True
            try:
                # Пытаемся распарсить JSON
                result["response"] = response.json()
            except json.JSONDecodeError:
                # Если не JSON, сохраняем как текст
                result["response"] = response.text
            
            logger.info(f"Health check успешно пройден: {response.status_code}")
        else:
            logger.error(f"Health check вернул статус {response.status_code}: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе health check: {e}")
        result["error"] = str(e)
    
    return result

async def check_bot_api(bot_token=None):
    """
    Проверяет доступность API Telegram для бота
    
    Args:
        bot_token (str, optional): Токен бота для проверки. 
                                 Если не указан, будет использоваться переменная окружения BOT_TOKEN.
    
    Returns:
        dict: Результат проверки
    """
    if not bot_token:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("Не указан BOT_TOKEN")
            return {
                "success": False,
                "error": "BOT_TOKEN не найден",
                "timestamp": datetime.now().isoformat()
            }
    
    logger.info("Проверка доступности API Telegram для бота")
    
    result = {
        "success": False,
        "bot_info": None,
        "error": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Используем aiohttp для запроса к API Telegram
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Проверяем доступность API через getMe
            async with session.get(
                f"https://api.telegram.org/bot{bot_token}/getMe", 
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        result["success"] = True
                        result["bot_info"] = data.get("result")
                        logger.info(f"API Telegram доступен, бот: @{result['bot_info'].get('username')}")
                    else:
                        result["error"] = data.get("description", "Неизвестная ошибка")
                        logger.error(f"Ошибка при запросе к API Telegram: {result['error']}")
                else:
                    result["error"] = f"Статус ответа: {response.status}"
                    logger.error(f"Ошибка при запросе к API Telegram: {result['error']}")
    except Exception as e:
        logger.error(f"Исключение при проверке API Telegram: {e}")
        result["error"] = str(e)
    
    return result

async def check_webhook_status(bot_token=None):
    """
    Проверяет статус webhook для бота
    
    Args:
        bot_token (str, optional): Токен бота для проверки. 
                                 Если не указан, будет использоваться переменная окружения BOT_TOKEN.
    
    Returns:
        dict: Результат проверки
    """
    if not bot_token:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("Не указан BOT_TOKEN")
            return {
                "success": False,
                "error": "BOT_TOKEN не найден",
                "timestamp": datetime.now().isoformat()
            }
    
    logger.info("Проверка статуса webhook для бота")
    
    result = {
        "success": False,
        "webhook_info": None,
        "error": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Используем aiohttp для запроса к API Telegram
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Получаем информацию о webhook
            async with session.get(
                f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", 
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        result["success"] = True
                        result["webhook_info"] = data.get("result")
                        
                        # Проверяем, установлен ли webhook
                        if result["webhook_info"].get("url"):
                            logger.info(f"Webhook установлен на URL: {result['webhook_info'].get('url')}")
                            
                            # Проверяем наличие ошибок
                            if result["webhook_info"].get("last_error_date"):
                                last_error = result["webhook_info"].get("last_error_message", "Неизвестная ошибка")
                                logger.warning(f"Последняя ошибка webhook: {last_error}")
                        else:
                            logger.warning("Webhook не установлен")
                    else:
                        result["error"] = data.get("description", "Неизвестная ошибка")
                        logger.error(f"Ошибка при запросе информации о webhook: {result['error']}")
                else:
                    result["error"] = f"Статус ответа: {response.status}"
                    logger.error(f"Ошибка при запросе информации о webhook: {result['error']}")
    except Exception as e:
        logger.error(f"Исключение при проверке статуса webhook: {e}")
        result["error"] = str(e)
    
    return result

async def main():
    """
    Основная функция для запуска проверок
    """
    parser = argparse.ArgumentParser(description="Тестирование доступности и работоспособности бота")
    parser.add_argument("--url", help="URL для проверки health check эндпоинта")
    parser.add_argument("--port", type=int, help="Порт для проверки health check эндпоинта (по умолчанию 8080)")
    parser.add_argument("--bot-token", help="Токен бота для проверки API Telegram")
    parser.add_argument("--timeout", type=int, default=5, help="Таймаут запросов в секундах (по умолчанию 5)")
    parser.add_argument("--repeat", type=int, default=1, help="Количество повторений проверок (по умолчанию 1)")
    parser.add_argument("--interval", type=int, default=5, help="Интервал между проверками в секундах (по умолчанию 5)")
    
    args = parser.parse_args()
    
    # Запуск проверок
    for i in range(args.repeat):
        if args.repeat > 1:
            logger.info(f"Проверка {i+1}/{args.repeat}")
        
        # Проверка health check эндпоинта
        health_result = check_health_endpoint(args.url, args.port, args.timeout)
        
        # Проверка API Telegram
        bot_api_result = await check_bot_api(args.bot_token)
        
        # Проверка статуса webhook
        webhook_result = await check_webhook_status(args.bot_token)
        
        # Общий результат
        overall_success = health_result["success"] and bot_api_result["success"] and webhook_result["success"]
        logger.info(f"Общий результат проверки: {'✅ Успешно' if overall_success else '❌ Ошибка'}")
        
        # Если нужно повторить проверки, ждем указанный интервал
        if i < args.repeat - 1:
            logger.info(f"Ожидание {args.interval} секунд перед следующей проверкой...")
            time.sleep(args.interval)
    
    # Если есть ошибки, выходим с ненулевым статусом
    if not overall_success:
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Проверка прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка при выполнении проверки: {e}")
        sys.exit(1) 