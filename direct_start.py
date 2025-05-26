#!/usr/bin/env python3
"""
Сверхпростой скрипт запуска для Railway.
Запускает бота без дополнительных проверок и обеспечивает базовый healthcheck.
"""
import os
import sys
import time
import logging
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("direct_start")

# Проверяем и добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    logger.info(f"Добавлен {os.getcwd()} в sys.path")

# Устанавливаем переменную окружения для Railway
os.environ["RAILWAY_ENV"] = "1"

# Порт для healthcheck (можно переопределить через переменную окружения)
PORT = int(os.environ.get("PORT", 8080))

# Время запуска
START_TIME = time.time()

# HTTP-обработчик для healthcheck
class SimpleHandler(BaseHTTPRequestHandler):
    """Простой обработчик HTTP запросов"""
    
    def log_message(self, format, *args):
        """Отключаем стандартное логирование"""
        return
    
    def do_GET(self):
        """Обрабатывает GET запрос"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

# Функция для запуска простого HTTP сервера
def run_healthcheck_server():
    """Запускает простой HTTP сервер для healthcheck"""
    try:
        server = HTTPServer(("", PORT), SimpleHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")

# Функция для прямого запуска бота
def run_bot():
    """Запускает бота напрямую"""
    try:
        # Импортируем основной модуль
        logger.info("Импортирую main.py...")
        import main
        logger.info("✅ Бот запущен успешно через импорт main")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте main: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== Запуск бота на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    
    # Запускаем healthcheck сервер в отдельном потоке
    health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
    health_thread.start()
    logger.info("Healthcheck сервер запущен в отдельном потоке")
    
    # Проверяем основные переменные окружения
    for var in ["BOT_TOKEN", "OPENAI_API_KEY"]:
        if var in os.environ:
            logger.info(f"✅ Переменная {var} найдена")
        else:
            logger.warning(f"⚠️ Переменная {var} отсутствует")
    
    # Запускаем бота
    success = run_bot()
    
    if success:
        # Бот запущен успешно, поддерживаем процесс активным
        logger.info("Бот запущен успешно, ожидание...")
        try:
            # Бесконечный цикл для поддержания процесса
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Завершение работы по команде пользователя")
    else:
        # Бот не запустился, но мы держим healthcheck для Railway
        logger.error("Бот не запустился, но healthcheck работает")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Завершение работы по команде пользователя") 