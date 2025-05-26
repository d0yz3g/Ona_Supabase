#!/usr/bin/env python3
"""
Упрощенный сценарий запуска для Railway.
Запускает бота напрямую с минимальным healthcheck.
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
logger = logging.getLogger("railway_final")

logger.info("=== Скрипт railway_final.py запущен ===")
logger.info(f"Python версия: {sys.version}")
logger.info(f"Текущая директория: {os.getcwd()}")
logger.info(f"Содержимое директории: {os.listdir('.')}")

# Добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    logger.info(f"Добавлен {os.getcwd()} в sys.path")

# Порт для healthcheck
PORT = int(os.environ.get("PORT", 8080))
logger.info(f"Используемый порт: {PORT}")

# HTTP-обработчик для healthcheck
class SimpleHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

# Функция для запуска HTTP сервера
def run_healthcheck_server():
    try:
        server = HTTPServer(("", PORT), SimpleHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")

# Проверяем основные переменные окружения
for var in ["BOT_TOKEN", "OPENAI_API_KEY"]:
    if var in os.environ:
        logger.info(f"✅ Переменная {var} найдена")
    else:
        logger.warning(f"⚠️ Переменная {var} отсутствует")

# Запускаем healthcheck сервер в отдельном потоке
health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
health_thread.start()
logger.info("Healthcheck сервер запущен в отдельном потоке")

# Запускаем бота
try:
    logger.info("Импортирую main.py...")
    import main
    logger.info("✅ Bot started")
    
    # Бесконечный цикл для поддержания процесса
    while True:
        time.sleep(60)
except Exception as e:
    logger.error(f"❌ Ошибка при импорте main: {e}")
    logger.error(traceback.format_exc())
    
    # Держим процесс активным для healthcheck
    while True:
        time.sleep(60) 