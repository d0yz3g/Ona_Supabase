#!/usr/bin/env python
"""
Веб-сервер для обработки webhook-запросов от Telegram API
Рекомендуется для продакшн-окружения на Railway и других хостингах
"""

import os
import sys
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("webhook_server")

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
    
    if webhook_url:
        # Устанавливаем webhook
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True
        )
        logger.info(f"✅ Webhook установлен на URL: {webhook_url}")
    else:
        logger.warning("⚠️ WEBHOOK_URL не установлен в переменных окружения")
        logger.warning("⚠️ Бот будет работать без webhook")

async def on_shutdown(bot: Bot):
    """
    Функция, вызываемая при остановке сервера
    Здесь можно выполнить дополнительные действия, например, удалить webhook
    """
    # Удаляем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook удален")

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
        return web.Response(
            text="OK - Bot is healthy and running in webhook mode",
            status=200,
            content_type="text/plain"
        )
    
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
    # Если порт не указан, берем из переменных окружения или используем 8080
    if port is None:
        port = int(os.environ.get("PORT", 8080))
    
    # Настраиваем приложение
    app = setup_webhook_app(dp, bot)
    
    # Запускаем сервер
    logger.info(f"Запуск webhook-сервера на {host}:{port}...")
    
    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    
    logger.info(f"✅ Webhook-сервер запущен на {host}:{port}")
    
    # Ждем до завершения приложения
    try:
        while True:
            await asyncio.sleep(3600)  # Проверка каждый час
    except (KeyboardInterrupt, SystemExit):
        logger.info("Завершение работы webhook-сервера...")
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
        
        # Импортируем необходимые компоненты
        from main import setup_bot, setup_dispatcher
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Проверяем наличие токена бота
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
            return 1
        
        # Настраиваем бота и диспетчер
        bot = setup_bot()
        dp = setup_dispatcher(bot)
        
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
    sys.exit(run_webhook_server()) 