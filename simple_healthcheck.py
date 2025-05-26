#!/usr/bin/env python3
"""
Простой HTTP сервер для проверки здоровья (health check) на Railway.
Запускает HTTP сервер на порту, указанном в переменной окружения PORT (по умолчанию 8080).
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
logger = logging.getLogger("healthcheck")

# Порт для healthcheck (можно переопределить через переменную окружения)
PORT = int(os.environ.get("PORT", 8080))

# Время запуска сервера
START_TIME = time.time()

class SimpleHandler(BaseHTTPRequestHandler):
    """Простой обработчик HTTP запросов для healthcheck"""
    
    def log_message(self, format, *args):
        """Отключаем стандартное логирование запросов"""
        return
    
    def do_GET(self):
        """Обрабатывает GET запрос и отвечает статусом 200 OK"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        uptime = time.time() - START_TIME
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        self.wfile.write(f"OK - Uptime: {uptime_str}".encode("utf-8"))

def run_server():
    """Запускает HTTP сервер"""
    try:
        server = HTTPServer(("", PORT), SimpleHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("=== Запуск healthcheck сервера ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Порт: {PORT}")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Healthcheck сервер остановлен")
        sys.exit(0) 