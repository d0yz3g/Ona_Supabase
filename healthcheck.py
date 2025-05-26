#!/usr/bin/env python3
"""
Простой веб-сервер для health check на Railway.
Запускается параллельно с ботом и позволяет Railway проверять доступность сервиса.
"""
import os
import sys
import http.server
import socketserver
import threading
import logging
import json

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("healthcheck")

# Порт по умолчанию
PORT = int(os.environ.get("PORT", 8080))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик запросов для health check"""
    
    def do_GET(self):
        """Обрабатывает GET-запросы"""
        if self.path == "/" or self.path == "/health":
            # Отвечаем OK на health check
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            response = {
                "status": "ok",
                "message": "ONA Telegram Bot is running",
                "version": "1.0"
            }
            
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Health check выполнен успешно, запрос с {self.client_address}")
        else:
            # Для всех остальных путей отвечаем 404
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            response = {
                "status": "error",
                "message": "Not found"
            }
            
            self.wfile.write(json.dumps(response).encode())
            logger.warning(f"Запрос к неизвестному пути {self.path} с {self.client_address}")
    
    def log_message(self, format, *args):
        """Перенаправляем логи в наш logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def start_health_check_server():
    """Запускает сервер для health check в отдельном потоке"""
    handler = HealthCheckHandler
    
    # Отключаем логи от socketserver
    handler.log_message = lambda self, format, *args: None
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        logger.info(f"Health check сервер запущен на порту {PORT}")
        httpd.serve_forever()

def run_in_thread():
    """Запускает сервер в отдельном потоке"""
    thread = threading.Thread(target=start_health_check_server, daemon=True)
    thread.start()
    logger.info(f"Health check сервер запущен в отдельном потоке")
    return thread

if __name__ == "__main__":
    logger.info(f"Запуск health check сервера на порту {PORT}")
    try:
        start_health_check_server()
    except KeyboardInterrupt:
        logger.info("Health check сервер остановлен")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ошибка при запуске health check сервера: {e}")
        sys.exit(1) 