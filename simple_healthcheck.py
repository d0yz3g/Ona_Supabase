#!/usr/bin/env python3
"""
Простой сервер для healthcheck в Railway.
Может использоваться как отдельный процесс для проверки работоспособности.
"""
import os
import sys
import time
import socket
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

# HTML страница для ответа
HTML_RESPONSE = """
<!DOCTYPE html>
<html>
<head>
    <title>Ona Bot - Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f7f9fc;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 4px;
            background-color: #e8f5e9;
            border-left: 5px solid #4caf50;
            font-weight: bold;
        }
        .info {
            margin-top: 30px;
        }
        .info p {
            margin: 5px 0;
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ona Bot - Status Page</h1>
        <div class="status">
            Status: Running
        </div>
        <div class="info">
            <p><strong>Host:</strong> {hostname}</p>
            <p><strong>Uptime:</strong> {uptime}</p>
            <p><strong>Python:</strong> {python_version}</p>
        </div>
    </div>
</body>
</html>
"""

# Время запуска
START_TIME = time.time()

class HealthHandler(BaseHTTPRequestHandler):
    """
    HTTP-обработчик для healthcheck
    """
    def log_message(self, format, *args):
        """Переопределение логирования для меньшего вывода"""
        logger.debug("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Обработка GET-запросов"""
        # Путь /health возвращает только статус 200
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        
        # Главная страница возвращает HTML
        hostname = socket.gethostname()
        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - START_TIME))
        python_version = sys.version
        
        # Формируем ответ с информацией
        response = HTML_RESPONSE.format(
            hostname=hostname,
            uptime=uptime,
            python_version=python_version
        )
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

def start_healthcheck_server():
    """Запускает сервер для healthcheck"""
    try:
        server = HTTPServer(("", PORT), HealthHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")

def run_as_thread():
    """Запускает healthcheck сервер в отдельном потоке"""
    thread = threading.Thread(target=start_healthcheck_server, daemon=True)
    thread.start()
    logger.info("Healthcheck сервер запущен в отдельном потоке")
    return thread

if __name__ == "__main__":
    # Если скрипт запускается напрямую, запускаем сервер
    logger.info("Запуск healthcheck сервера")
    start_healthcheck_server() 