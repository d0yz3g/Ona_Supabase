#!/usr/bin/env python3
"""
Минимальный скрипт для Railway без внешних зависимостей
"""
import os
import sys
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bare_minimal")

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

def main():
    """Основная функция"""
    logger.info("=== Запуск минимального сервиса на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    
    try:
        # Запускаем HTTP сервер для healthcheck
        server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        logger.info("✅ Bot started")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 