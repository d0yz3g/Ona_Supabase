#!/usr/bin/env python
"""
Веб-сервер для обработки webhook-запросов от Telegram API
Рекомендуется для продакшн-окружения на Railway и других хостингах
"""

import os
import sys
import logging
import asyncio
import socket
import time
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("webhook_server.log")]
)
logger = logging.getLogger("webhook_server")

# Определим переменную для Railway
RAILWAY_ENV = os.getenv("RAILWAY", "false").lower() in ("true", "1", "yes") or os.getenv("RAILWAY_STATIC_URL") is not None

# Настройка порта по умолчанию - важно использовать PORT переменную от Railway
DEFAULT_PORT = int(os.environ.get("PORT", 8080))

# Вывод важных переменных для отладки
print(f"WEBHOOK SERVER: Запуск на порту {DEFAULT_PORT}")
print(f"WEBHOOK SERVER: Railway окружение: {RAILWAY_ENV}")
print(f"WEBHOOK SERVER: Рабочая директория: {os.getcwd()}")
print(f"WEBHOOK SERVER: Доступные переменные окружения для webhook:")
print(f"   - WEBHOOK_URL: {os.environ.get('WEBHOOK_URL', 'не установлено')}")
print(f"   - RAILWAY_PUBLIC_DOMAIN: {os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'не установлено')}")
print(f"   - PORT: {os.environ.get('PORT', 'не установлено, используется значение по умолчанию')}")

# Проверка доступности порта
def is_port_available(port):
    """Проверяет, доступен ли указанный порт"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0  # Если result != 0, порт свободен
    except Exception as e:
        logger.error(f"Ошибка при проверке порта {port}: {e}")
        return False

# Переменная для отслеживания времени запуска
start_time = time.time()

async def on_startup(bot: Bot):
    """
    Функция, вызываемая при запуске сервера
    Здесь можно выполнить дополнительные действия, например, настроить webhook
    """
    # Извлекаем основной токен из переменных окружения
    webhook_url = os.environ.get("WEBHOOK_URL")
    railway_public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    # Если нет WEBHOOK_URL, но есть Railway-специфичные переменные, формируем URL
    if not webhook_url and railway_public_domain:
        webhook_path = f"/webhook/{bot.token}"
        webhook_url = f"https://{railway_public_domain}{webhook_path}"
        logger.info(f"Сформирован WEBHOOK_URL на основе Railway-домена: {webhook_url}")
        print(f"WEBHOOK SERVER: Сформирован URL webhook: {webhook_url}")
    
    if webhook_url:
        # Устанавливаем webhook
        try:
            # Сначала удаляем старый webhook, чтобы избежать конфликтов
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Старый webhook удален")
            
            # Устанавливаем новый webhook
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query", "inline_query", "edited_message", "chosen_inline_result"],
                drop_pending_updates=True
            )
            logger.info(f"✅ Webhook установлен на URL: {webhook_url}")
            print(f"WEBHOOK SERVER: Webhook успешно установлен на URL: {webhook_url}")
            
            # Проверяем, что webhook действительно установлен
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Проверка webhook: URL={webhook_info.url}, pending_updates={webhook_info.pending_update_count}")
            
            if webhook_info.last_error_date:
                logger.warning(f"⚠️ Последняя ошибка webhook: {webhook_info.last_error_message}")
                print(f"WEBHOOK SERVER ПРЕДУПРЕЖДЕНИЕ: Последняя ошибка webhook: {webhook_info.last_error_message}")
                
            # Проверяем, работает ли webhook
            if not webhook_info.url:
                logger.error("❌ Webhook не установлен! Проверьте доступность URL и права бота.")
                print("WEBHOOK SERVER ОШИБКА: Webhook не установлен! Проверьте URL и настройки бота.")
        except Exception as e:
            logger.error(f"❌ Ошибка при установке webhook: {e}")
            print(f"WEBHOOK SERVER ОШИБКА: Не удалось установить webhook: {e}")
    else:
        logger.warning("⚠️ WEBHOOK_URL не установлен в переменных окружения")
        logger.warning("⚠️ Бот будет работать без webhook")
        print("WEBHOOK SERVER ПРЕДУПРЕЖДЕНИЕ: WEBHOOK_URL не установлен, бот не сможет получать обновления!")

async def on_shutdown(bot: Bot):
    """
    Функция, вызываемая при остановке сервера
    Здесь можно выполнить дополнительные действия, например, удалить webhook
    """
    # Удаляем webhook
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удален")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении webhook: {e}")

def setup_webhook_app(dp: Dispatcher, bot: Bot):
    """
    Настраивает и возвращает веб-приложение для обработки webhook-запросов
    
    Args:
        dp (Dispatcher): Диспетчер aiogram
        bot (Bot): Экземпляр бота aiogram
        
    Returns:
        web.Application: Приложение aiohttp для обработки webhook-запросов
    """
    # Создаем приложение aiohttp
    app = web.Application()
    
    # Регистрируем обработчики для запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Определяем путь для webhook
    webhook_path = f"/webhook/{bot.token}"
    
    # Настраиваем обработчик webhook
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    
    # Настраиваем пути веб-приложения
    webhook_handler.register(app, path=webhook_path)
    
    # Функция для проверки здоровья приложения
    async def health_check(request):
        try:
            # Проверяем, что бот доступен, отправив запрос getMe
            me = await bot.get_me()
            bot_info = f"@{me.username} (ID: {me.id})"
            
            # Формируем ответ
            health_data = {
                "status": "OK",
                "bot": bot_info,
                "uptime": int(time.time() - start_time),
                "webhook_mode": True,
                "railway": RAILWAY_ENV,
                "timestamp": datetime.now().isoformat()
            }
            
            # Определяем формат ответа
            accept_header = request.headers.get('Accept', '')
            if 'application/json' in accept_header:
                return web.json_response(health_data)
            else:
                response_text = (
                    f"Status: OK\n"
                    f"Bot: {bot_info}\n"
                    f"Uptime: {health_data['uptime']} seconds\n"
                    f"Mode: webhook\n"
                    f"Railway: {'yes' if RAILWAY_ENV else 'no'}\n"
                    f"Timestamp: {health_data['timestamp']}\n"
                )
                return web.Response(text=response_text, status=200, content_type="text/plain")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            print(f"WEBHOOK SERVER ОШИБКА: Проверка health check не удалась: {e}")
            # Railway ожидает статус 200 для успешного health check, 
            # поэтому возвращаем 200 даже при ошибке, чтобы приложение не перезапускалось
            return web.Response(text=f"OK (with warnings)", status=200, content_type="text/plain")
    
    # Добавляем обработчики для проверки здоровья приложения
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)  # Добавляем для Railway health check
    
    # Выводим информацию о настроенных путях
    logger.info(f"Настроен webhook-обработчик на пути: {webhook_path}")
    logger.info(f"Доступен health-check эндпоинт на путях: / и /health")
    
    return app

async def start_webhook_server(dp: Dispatcher, bot: Bot, host='0.0.0.0', port=None):
    """
    Запускает веб-сервер для обработки webhook-запросов
    
    Args:
        dp (Dispatcher): Диспетчер aiogram
        bot (Bot): Экземпляр бота aiogram
        host (str, optional): Хост для запуска сервера. По умолчанию '0.0.0.0'.
        port (int, optional): Порт для запуска сервера. Если не указан, будет использоваться
                              переменная окружения PORT или порт 8080 по умолчанию.
    """
    global start_time
    start_time = time.time()
    
    # Если порт не указан, берем из переменных окружения или используем 8080
    if port is None:
        port = DEFAULT_PORT
    
    # Проверяем доступность порта, если занят - пробуем другой
    max_port_retries = 3
    original_port = port
    
    for retry in range(max_port_retries):
        if is_port_available(port):
            break
        logger.warning(f"Порт {port} занят, пробуем порт {port + 10}")
        port += 10
    
    if port != original_port:
        logger.info(f"Используем порт {port} вместо {original_port}")
    
    # Настраиваем приложение
    app = setup_webhook_app(dp, bot)
    
    # Запускаем сервер
    logger.info(f"Запуск webhook-сервера на {host}:{port}...")
    print(f"WEBHOOK SERVER: Запуск на {host}:{port}")
    
    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    
    try:
        await site.start()
        logger.info(f"✅ Webhook-сервер запущен на {host}:{port}")
        print(f"WEBHOOK SERVER: Сервер успешно запущен на {host}:{port}")
        
        # Если мы на Railway, добавляем переменную окружения WEBHOOK_MODE=true
        if RAILWAY_ENV and not os.environ.get("WEBHOOK_MODE"):
            os.environ["WEBHOOK_MODE"] = "true"
            logger.info("Установлена переменная WEBHOOK_MODE=true для Railway")
        
        # Ждем до завершения приложения
        while True:
            await asyncio.sleep(60)  # Проверка каждую минуту
            # Периодическая проверка здоровья бота
            try:
                me = await bot.get_me()
                logger.info(f"Health check passed: бот @{me.username} активен")
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                print(f"WEBHOOK SERVER ОШИБКА: Внутренняя проверка здоровья не удалась: {e}")
    except KeyboardInterrupt:
        logger.info("Завершение работы webhook-сервера...")
    except Exception as e:
        logger.error(f"Ошибка в webhook-сервере: {e}")
        print(f"WEBHOOK SERVER КРИТИЧЕСКАЯ ОШИБКА: {e}")
    finally:
        await runner.cleanup()
        logger.info("✅ Webhook-сервер остановлен")

def run_webhook_server():
    """
    Точка входа для запуска webhook-сервера
    """
    # Импортируем необходимые модули
    try:
        # Проверяем наличие main.py перед импортом
        if not os.path.exists("main.py"):
            logger.error("❌ Файл main.py не найден")
            return 1
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Проверяем наличие токена бота
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
            return 1
            
        # Импортируем необходимые компоненты
        from main import setup_bot, setup_dispatcher
        
        # Настраиваем бота и диспетчер
        bot = setup_bot()
        dp = setup_dispatcher(bot)
        
        # Если мы на Railway, устанавливаем переменную WEBHOOK_MODE
        if RAILWAY_ENV:
            os.environ["WEBHOOK_MODE"] = "true"
            logger.info("На Railway: установлена переменная WEBHOOK_MODE=true")
        
        # Запускаем веб-сервер
        asyncio.run(start_webhook_server(dp, bot))
        
        return 0
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Убедитесь, что main.py содержит функции setup_bot и setup_dispatcher")
        return 1
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске webhook-сервера: {e}")
        return 1

if __name__ == "__main__":
    logger.info("Запуск webhook-сервера...")
    print("WEBHOOK SERVER: Начало запуска сервера webhook")
    sys.exit(run_webhook_server()) 