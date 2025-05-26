#!/usr/bin/env python
"""
Скрипт для запуска бота Telegram в режиме webhook
Решает проблему с ошибкой "TelegramConflictError: Conflict: terminated by other getUpdates request"
"""

import os
import sys
import logging
import asyncio
import subprocess
import requests
from aiohttp import web
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WEBHOOK] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("webhook.log")]
)
logger = logging.getLogger("webhook")

# Загружаем переменные окружения
load_dotenv()

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
    
    # Если нет WEBHOOK_URL, но есть Railway-специфичные переменные, формируем URL
    if not webhook_url and railway_public_domain:
        webhook_url = f"https://{railway_public_domain}/webhook/{BOT_TOKEN}"
        logger.info(f"Сформирован WEBHOOK_URL на основе Railway-домена: {webhook_url}")
    
    # Проверяем наличие необходимых переменных
    if not webhook_url:
        logger.error("❌ Переменная WEBHOOK_URL не найдена в .env или переменных окружения")
        logger.error("Укажите WEBHOOK_URL в формате: https://your-domain.com/webhook/{bot_token}")
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
            result = response.json().get('result', {})
            description = response.json().get('description', 'Нет описания')
            
            logger.info(f"✅ Webhook успешно установлен: {description}")
            
            # Получаем информацию о текущем webhook
            info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
            if info_response.status_code == 200:
                webhook_info = info_response.json().get('result', {})
                url = webhook_info.get('url', 'Не установлен')
                pending_update_count = webhook_info.get('pending_update_count', 0)
                last_error_date = webhook_info.get('last_error_date')
                last_error_message = webhook_info.get('last_error_message')
                
                logger.info(f"Текущий webhook URL: {url}")
                logger.info(f"Ожидающих обновлений: {pending_update_count}")
                
                if last_error_date:
                    logger.warning(f"Последняя ошибка webhook: {last_error_message}")
            
            return True
        else:
            logger.error(f"❌ Ошибка при установке webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при настройке webhook: {e}")
        return False

def check_postgres():
    """
    Проверяет и инициализирует базу данных PostgreSQL, если она используется
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.info("Переменная DATABASE_URL не найдена, будет использоваться SQLite")
        return True
    
    logger.info(f"Обнаружена переменная DATABASE_URL, проверка базы данных PostgreSQL...")
    
    # Проверяем наличие psycopg2-binary
    try:
        import psycopg2
        logger.info("Модуль psycopg2 успешно импортирован")
    except ImportError:
        logger.error("Не найден модуль psycopg2, требуется для работы с PostgreSQL")
        logger.error("Установка psycopg2-binary...")
        
        try:
            # Пытаемся установить psycopg2-binary
            subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
            logger.info("psycopg2-binary успешно установлен")
            
            # Пытаемся снова импортировать psycopg2
            import psycopg2
            logger.info("Модуль psycopg2 успешно импортирован после установки")
        except Exception as e:
            logger.error(f"Ошибка при установке psycopg2-binary: {e}")
            logger.warning("Продолжаем запуск бота с использованием SQLite вместо PostgreSQL")
            # Устанавливаем временную переменную, чтобы бот использовал SQLite
            os.environ.pop("DATABASE_URL", None)
            return True
    
    # Инициализируем базу данных PostgreSQL
    try:
        # Пытаемся подключиться к PostgreSQL
        conn = psycopg2.connect(database_url)
        logger.info("✅ Подключение к PostgreSQL успешно установлено")
        
        # SQL для создания таблиц в PostgreSQL
        POSTGRES_CREATE_TABLES_SQL = """
        -- Таблица пользователей
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            tg_id BIGINT UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Таблица ответов на вопросы
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER,
            q_code TEXT,
            value TEXT,
            PRIMARY KEY(id, q_code),
            FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Таблица профилей
        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Таблица напоминаний
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            cron TEXT NOT NULL,
            message TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Индексы для ускорения запросов
        CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
        CREATE INDEX IF NOT EXISTS idx_answers_id ON answers(id);
        CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
        """
        
        # Создаем таблицы
        with conn.cursor() as cursor:
            logger.info("Создаем таблицы в PostgreSQL...")
            cursor.execute(POSTGRES_CREATE_TABLES_SQL)
            conn.commit()
            logger.info("✅ Таблицы успешно созданы или уже существуют")
        
        # Проверяем созданные таблицы
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]
            
            logger.info(f"Таблицы в базе данных: {', '.join(table_names)}")
            
            # Проверяем наличие необходимых таблиц
            required_tables = ['users', 'answers', 'profiles', 'reminders']
            missing_tables = [t for t in required_tables if t not in table_names]
            
            if missing_tables:
                logger.error(f"❌ Отсутствуют таблицы: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("✅ Все необходимые таблицы присутствуют")
        
        # Закрываем соединение
        conn.close()
        logger.info("✅ PostgreSQL настроен и готов к использованию")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке PostgreSQL: {e}")
        return False

def start_webhook_server():
    """
    Запускает бота в режиме webhook
    """
    # Устанавливаем флаг режима webhook
    os.environ['WEBHOOK_MODE'] = 'true'
    
    # Проверяем и инициализируем PostgreSQL
    if not check_postgres():
        logger.error("❌ Не удалось настроить PostgreSQL")
        return 1
    
    # Настраиваем webhook
    if not setup_webhook():
        logger.error("❌ Не удалось настроить webhook")
        return 1
    
    # Запускаем основной скрипт
    logger.info("Запуск основного скрипта в режиме webhook...")
    
    # Запускаем скрипт
    try:
        # Подготавливаем команду для запуска скрипта
        command = [sys.executable, "main.py"]
        
        # Запускаем скрипт в новом процессе
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Запускаем веб-сервер для обработки webhook-запросов
        port = int(os.environ.get("PORT", 8080))
        
        # Создаем простое веб-приложение для обработки webhook-запросов
        app = web.Application()
        
        # Обработчик для корневого пути (для проверки доступности)
        async def health_check(request):
            return web.Response(text="Бот работает в режиме webhook", status=200)
        
        # Обработчик для webhook-запросов
        async def webhook_handler(request):
            if request.match_info.get('token') != BOT_TOKEN:
                return web.Response(status=403)
            
            # Получаем данные запроса
            try:
                data = await request.json()
                logger.info(f"Получен webhook-запрос: {data}")
                return web.Response(status=200)
            except Exception as e:
                logger.error(f"Ошибка при обработке webhook-запроса: {e}")
                return web.Response(status=500)
        
        # Регистрируем обработчики
        app.router.add_get("/", health_check)
        app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)
        
        # Запускаем веб-сервер
        web.run_app(app, host='0.0.0.0', port=port)
        
        return 0
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота в режиме webhook: {e}")
        return 1

if __name__ == "__main__":
    logger.info("Запуск бота в режиме webhook...")
    
    # Проверяем наличие необходимых переменных окружения
    if not BOT_TOKEN:
        logger.error("❌ Переменная BOT_TOKEN не найдена в .env или переменных окружения")
        sys.exit(1)
    
    # Запускаем бота в режиме webhook
    sys.exit(start_webhook_server()) 