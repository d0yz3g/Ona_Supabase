#!/usr/bin/env python3
"""
Ультра-базовый Telegram бот для Railway
Не использует сложные зависимости, только базовый функционал
"""
import os
import sys
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ultrabasic_bot")

# Порт для healthcheck
PORT = int(os.environ.get("PORT", 8080))

# Простой HTTP обработчик для healthcheck
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

def main():
    """Основная функция, которая запускает бота"""
    logger.info("=== Запуск ультра-базового бота на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Переменные окружения: {list(os.environ.keys())}")
    
    # Запускаем healthcheck сервер в отдельном потоке
    health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
    health_thread.start()
    
    # Логируем успешный запуск
    logger.info("✅ Bot started")
    
    # Имитация работы бота в бесконечном цикле
    try:
        logger.info("Бот работает...")
        counter = 0
        while True:
            time.sleep(10)
            counter += 1
            logger.info(f"Бот продолжает работать... ({counter})")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    
    logger.info("Завершение работы...")

if __name__ == "__main__":
    main() 