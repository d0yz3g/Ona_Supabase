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
import time

# Отслеживаем время запуска
start_time = time.time()

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
    
    # Проверяем если WEBHOOK_HOST установлен отдельно
    webhook_host = os.environ.get('WEBHOOK_HOST')
    
    # Формируем URL для webhook
    if webhook_url:
        # Если напрямую указан WEBHOOK_URL, используем его
        logger.info(f"Используется предоставленный WEBHOOK_URL: {webhook_url}")
    elif webhook_host:
        # Формируем из WEBHOOK_HOST
        webhook_url = f"https://{webhook_host}/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе WEBHOOK_HOST: {webhook_url}")
    elif railway_public_domain:
        # Формируем из RAILWAY_PUBLIC_DOMAIN
        webhook_url = f"https://{railway_public_domain}/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе Railway-домена: {webhook_url}")
    elif railway_service_id:
        # Формируем из ID сервиса Railway
        webhook_url = f"https://{railway_service_id}.up.railway.app/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе ID сервиса Railway: {webhook_url}")
    else:
        # Если нет информации для формирования URL, пропускаем настройку webhook
        logger.warning("⚠️ Не удалось определить URL для webhook, работаем без него")
        logger.warning("⚠️ Установите переменную WEBHOOK_URL для правильной работы webhook")
        return False
    
    # Сначала удаляем текущий webhook, чтобы избежать конфликтов
    logger.info("🔄 Удаляем текущий webhook...")
    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
    try:
        delete_response = requests.get(delete_url, timeout=30)
        if delete_response.status_code == 200 and delete_response.json().get('ok'):
            logger.info("✅ Текущий webhook успешно удален")
        else:
            logger.warning(f"⚠️ Не удалось удалить текущий webhook: {delete_response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении webhook: {e}")
    
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
                'drop_pending_updates': True,
                'secret_token': os.environ.get('WEBHOOK_SECRET', 'telegram_webhook_secret')
            },
            timeout=30
        )
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get('ok'):
            description = response.json().get('description', 'Нет описания')
            logger.info(f"✅ Webhook успешно установлен: {description}")
            
            # Проверяем текущие настройки webhook для подтверждения
            check_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            try:
                check_response = requests.get(check_url, timeout=30)
                if check_response.status_code == 200:
                    webhook_info = check_response.json().get('result', {})
                    logger.info(f"ℹ️ Текущий webhook URL: {webhook_info.get('url')}")
                    logger.info(f"ℹ️ Последняя ошибка: {webhook_info.get('last_error_message', 'нет')}")
                    logger.info(f"ℹ️ Ожидающие обновления: {webhook_info.get('pending_update_count', 0)}")
                else:
                    logger.error(f"❌ Ошибка при проверке webhook: {check_response.text}")
            except Exception as e:
                logger.error(f"❌ Исключение при проверке webhook: {e}")
            
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при настройке webhook: {e}")
        return False

def test_webhook():
    """
    Отправляет тестовое сообщение в Telegram API для проверки работы webhook
    """
    logger.info("🧪 Отправляем тестовое сообщение для проверки webhook...")
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        # Получаем ID админа из переменных окружения
        admin_id = os.environ.get('ADMIN_CHAT_ID')
        if not admin_id:
            logger.warning("⚠️ ADMIN_CHAT_ID не указан, тестовое сообщение не будет отправлено")
            return
        
        # Отправляем тестовое сообщение
        response = requests.post(
            api_url,
            json={
                'chat_id': admin_id,
                'text': f"🤖 Бот перезапущен и готов к работе! Webhook настроен на {os.environ.get('WEBHOOK_URL', 'неизвестный URL')}."
            },
            timeout=10
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("✅ Тестовое сообщение успешно отправлено")
        else:
            logger.error(f"❌ Ошибка при отправке тестового сообщения: {response.text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке тестового сообщения: {e}")

async def forward_to_telegram(update_data):
    """
    Пересылает данные от webhook к API Telegram для обработки
    
    Args:
        update_data (dict): Данные от Telegram webhook
        
    Returns:
        bool: True если успешно, False в противном случае
    """
    try:
        # Логируем всё сообщение целиком для отладки
        logger.info(f"⚙️ Обработка обновления: {json.dumps(update_data, ensure_ascii=False)}")
        
        # Получаем метод для вызова на основе типа обновления
        method = None
        
        if 'message' in update_data:
            chat_id = update_data['message']['chat']['id']
            text = update_data['message'].get('text', '')
            
            # Логируем сообщение от пользователя
            user_info = update_data['message']['from']
            username = user_info.get('username', 'нет')
            first_name = user_info.get('first_name', '')
            last_name = user_info.get('last_name', '')
            logger.info(f"📩 Получено сообщение от пользователя @{username} ({first_name} {last_name}): {text}")
            
            if text and text.startswith('/'):
                # Обрабатываем команды
                command = text.split()[0].lower()
                logger.info(f"🔄 Обработка команды: {command}")
                
                if command == '/start':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "👋 Привет! Я Она - твой бот-помощник.\n\nЯ могу помочь тебе разобраться в себе и своих эмоциях.\n\nНапиши /help чтобы узнать, что я умею."
                    }
                    logger.info(f"🤖 Отправляем ответ на команду /start пользователю {chat_id}")
                elif command == '/help':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "📋 Доступные команды:\n\n/start - Начать диалог\n/help - Показать эту справку\n/about - О боте\n/meditate - Получить медитацию"
                    }
                    logger.info(f"🤖 Отправляем ответ на команду /help пользователю {chat_id}")
                elif command == '/about':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "ℹ️ Я - Она, бот-помощник, созданный чтобы помогать тебе в трудные моменты. Я использую современные технологии искусственного интеллекта для анализа твоих сообщений и предоставления поддержки."
                    }
                    logger.info(f"🤖 Отправляем ответ на команду /about пользователю {chat_id}")
                elif command == '/meditate':
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': "🧘‍♀️ Медитация поможет тебе успокоиться и сосредоточиться. Глубоко вдохни и медленно выдохни. Повторяй этот процесс, концентрируясь на своем дыхании."
                    }
                    logger.info(f"🤖 Отправляем ответ на команду /meditate пользователю {chat_id}")
                else:
                    method = "sendMessage"
                    params = {
                        'chat_id': chat_id,
                        'text': f"🤔 Команда {command} не распознана. Напиши /help чтобы увидеть список команд."
                    }
                    logger.info(f"🤖 Отправляем ответ на неизвестную команду {command} пользователю {chat_id}")
            else:
                # Эхо-ответ на текстовое сообщение (в будущем здесь будет интеграция с OpenAI)
                method = "sendMessage"
                params = {
                    'chat_id': chat_id,
                    'text': f"🤖 Ты написал: {text}\n\nВ будущих версиях я смогу поддерживать полноценный диалог."
                }
                logger.info(f"🤖 Отправляем эхо-ответ пользователю {chat_id}")
        elif 'callback_query' in update_data:
            # Обрабатываем callback_query от inline-кнопок
            logger.info("📩 Получен callback_query")
            callback_id = update_data['callback_query']['id']
            chat_id = update_data['callback_query']['message']['chat']['id']
            data = update_data['callback_query'].get('data', '')
            
            # Отвечаем на callback_query
            method = "answerCallbackQuery"
            params = {
                'callback_query_id': callback_id,
                'text': f"Выбрано: {data}"
            }
            logger.info(f"🤖 Отвечаем на callback_query с данными: {data}")
        
        # Если метод был определен, вызываем API
        if method:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
            logger.info(f"📤 Вызываем метод API: {method}")
            
            # Повторяем запрос до трех раз в случае ошибки
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(api_url, json=params, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ API вызов успешен: {method}")
                        return True
                    else:
                        logger.error(f"❌ Ошибка при вызове API {method} (попытка {attempt+1}/{max_retries}): {response.text}")
                        if attempt == max_retries - 1:  # Последняя попытка
                            return False
                        # Пауза перед повторной попыткой
                        await asyncio.sleep(1)
                except (requests.RequestException, asyncio.TimeoutError) as e:
                    logger.error(f"❌ Исключение при вызове API {method} (попытка {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:  # Последняя попытка
                        return False
                    # Пауза перед повторной попыткой
                    await asyncio.sleep(1)
        else:
            logger.warning("⚠️ Не удалось определить метод API для ответа")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при пересылке данных в Telegram: {e}")
        # Печатаем полный traceback для отладки
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        # Собираем информацию о состоянии приложения
        status = {
            "status": "ok",
            "timestamp": time.time(),
            "service": os.environ.get('RAILWAY_SERVICE_NAME', 'Ona Bot'),
            "bot_info": None,
            "webhook_info": None,
            "uptime": time.time() - start_time
        }
        
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
                
                # Отправляем тестовое сообщение
                test_webhook()
        
        # Получаем информацию о боте
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                status["bot_info"] = response.json().get('result')
        except Exception as e:
            logger.error(f"Ошибка при получении информации о боте: {e}")
            status["bot_info_error"] = str(e)
        
        # Получаем информацию о webhook
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                status["webhook_info"] = response.json().get('result')
        except Exception as e:
            logger.error(f"Ошибка при получении информации о webhook: {e}")
            status["webhook_info_error"] = str(e)
        
        # Логируем информацию о запросе для отладки
        client_ip = request.headers.get('X-Forwarded-For') or request.remote
        user_agent = request.headers.get('User-Agent', 'Unknown')
        logger.info(f"{client_ip} [{time.strftime('%d/%b/%Y:%H:%M:%S +0000')}] \"{request.method} {request.path} {request.version}\" 200 {len(str(status))} \"-\" \"{user_agent}\"")
        
        return web.json_response(status)
    
    # Обработчик для webhook
    async def webhook_handler(request):
        if request.match_info.get('token') != BOT_TOKEN:
            logger.warning(f"Получен запрос с неверным токеном: {request.match_info.get('token')}")
            return web.Response(status=403, text="Forbidden")
        
        try:
            # Получаем данные запроса
            webhook_data = await request.text()
            logger.info(f"📥 ПОЛУЧЕНЫ ДАННЫЕ WEBHOOK: {webhook_data}")
            
            # Парсим JSON
            try:
                update_data = json.loads(webhook_data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка декодирования JSON: {e}")
                logger.error(f"❌ Неверный JSON: {webhook_data}")
                return web.Response(status=400, text="Bad Request - Invalid JSON")
            
            # Логируем все заголовки для отладки
            headers_str = '\n'.join([f"{k}: {v}" for k, v in request.headers.items()])
            logger.info(f"🔍 WEBHOOK HEADERS:\n{headers_str}")
            
            # Более подробное логирование тела запроса
            logger.info(f"📦 ПОЛУЧЕН WEBHOOK-ЗАПРОС: {json.dumps(update_data, ensure_ascii=False)}")
            
            # Логируем IP-адрес отправителя
            peer_name = request.transport.get_extra_info('peername')
            if peer_name:
                logger.info(f"🌐 ЗАПРОС ПОЛУЧЕН С IP: {peer_name[0]}:{peer_name[1]}")
            
            # Проверяем структуру данных
            if not update_data:
                logger.error("❌ Получен пустой JSON")
                return web.Response(status=400, text="Bad Request - Empty JSON")
            
            # Проверяем наличие нужных полей
            if 'update_id' not in update_data:
                logger.error("❌ В JSON отсутствует поле update_id")
                logger.error(f"❌ Содержимое JSON: {webhook_data}")
                return web.Response(status=400, text="Bad Request - Missing update_id")
            
            logger.info(f"✨ НАЧИНАЕМ ОБРАБОТКУ UPDATE_ID={update_data['update_id']}")
            
            # Пересылаем данные в Telegram API и ждем результата
            success = await forward_to_telegram(update_data)
            if success:
                logger.info(f"✅ WEBHOOK ОБРАБОТАН УСПЕШНО ДЛЯ UPDATE_ID={update_data['update_id']}")
            else:
                logger.error(f"❌ ОШИБКА ПРИ ОБРАБОТКЕ WEBHOOK ДЛЯ UPDATE_ID={update_data['update_id']}")
            
            # Возвращаем успешный ответ
            return web.Response(status=200, text="OK")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка декодирования JSON в webhook-запросе: {e}")
            logger.error(f"❌ Тело запроса: {await request.text()}")
            return web.Response(status=400, text="Bad Request - Invalid JSON")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке webhook-запроса: {e}")
            # Печатаем полный traceback для отладки
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
    else:
        # Если webhook настроен успешно, отправляем тестовое сообщение
        test_webhook()
    
    # Запускаем веб-сервер
    logger.info(f"Запуск сервера на порту {port}...")
    await site.start()
    logger.info(f"✅ Сервер успешно запущен на порту {port}")
    
    # Функция для периодического пинга, чтобы поддерживать сервер активным
    async def keep_alive():
        """Периодически отправляет запрос к API Telegram для поддержания активности"""
        last_webhook_check = 0
        while True:
            try:
                # Текущее время
                current_time = time.time()
                
                # Запрашиваем информацию о боте
                api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    bot_info = response.json().get('result', {})
                    bot_name = bot_info.get('first_name', 'Unknown')
                    bot_username = bot_info.get('username', 'Unknown')
                    logger.info(f"🤖 Бот активен: {bot_name} (@{bot_username})")
                else:
                    logger.warning(f"⚠️ Пинг API вернул статус {response.status_code}: {response.text}")
                
                # Проверяем webhook каждые 30 минут
                if current_time - last_webhook_check > 1800:  # 30 минут в секундах
                    check_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
                    check_response = requests.get(check_url, timeout=10)
                    if check_response.status_code == 200:
                        webhook_info = check_response.json().get('result', {})
                        webhook_url = webhook_info.get('url', '')
                        last_error = webhook_info.get('last_error_message')
                        pending_updates = webhook_info.get('pending_update_count', 0)
                        
                        logger.info(f"🔄 Проверка webhook: URL = {webhook_url}")
                        logger.info(f"🔄 Последняя ошибка webhook: {last_error or 'нет'}")
                        logger.info(f"🔄 Ожидающие обновления: {pending_updates}")
                        
                        # Если последняя ошибка указывает на проблемы с webhook или нет URL,
                        # перенастраиваем webhook
                        if last_error or not webhook_url:
                            logger.warning("⚠️ Обнаружены проблемы с webhook, переустанавливаем...")
                            setup_webhook()
                    else:
                        logger.error(f"❌ Ошибка при проверке webhook: {check_response.text}")
                    
                    # Обновляем время последней проверки
                    last_webhook_check = current_time
            except Exception as e:
                logger.error(f"❌ Ошибка в задаче keep_alive: {e}")
            
            # Ждем 5 минут перед следующим пингом
            await asyncio.sleep(300)
    
    # Запускаем задачу поддержания активности
    asyncio.create_task(keep_alive())
    
    # Ждем завершения
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logger.info("Запуск простого сервера для Railway...")
    
    # Проверяем наличие ADMIN_CHAT_ID
    admin_id = os.environ.get('ADMIN_CHAT_ID')
    if not admin_id:
        logger.warning("⚠️ Переменная ADMIN_CHAT_ID не установлена. Для отладки рекомендуется указать ID администратора.")
        # Используем значение по умолчанию, если оно не указано
        os.environ['ADMIN_CHAT_ID'] = "123456789"  # Замените на ваш ID
    
    try:
        # Запускаем сервер
        asyncio.run(start_simple_server())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске сервера: {e}")
        sys.exit(1) 