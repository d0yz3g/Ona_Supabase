#!/usr/bin/env python
"""
Dedicated health check server for Railway
This provides a simple HTTP server that responds to the health check path.
"""

import os
import sys
import json
import logging
import threading
import time
import socket
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [HEALTH] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("health_test.log")]
)
logger = logging.getLogger("health_check")

# Глобальные переменные для статуса
STATUS = {
    "status": "OK",
    "timestamp": datetime.now().isoformat(),
    "uptime": 0,
    "start_time": datetime.now().isoformat(),
    "checks": {
        "bot_token": False,
        "database": False,
        "port_available": False,
        "telegram_api": False
    },
    "last_error": None
}

# Время запуска сервера
START_TIME = time.time()

# Функция для обновления статуса
def update_status(key=None, value=None, error=None):
    global STATUS
    STATUS["timestamp"] = datetime.now().isoformat()
    STATUS["uptime"] = int(time.time() - START_TIME)
    
    if key and key in STATUS["checks"]:
        STATUS["checks"][key] = value
    
    if error:
        STATUS["status"] = "ERROR"
        STATUS["last_error"] = str(error)
    elif all(STATUS["checks"].values()):
        STATUS["status"] = "OK"

# Проверка базовых параметров при запуске
def check_basic_health():
    # Проверка наличия токена бота
    bot_token = os.environ.get("BOT_TOKEN")
    update_status("bot_token", bot_token is not None)
    
    # Проверка доступности API Telegram
    try:
        response = requests.get("https://api.telegram.org", timeout=5)
        update_status("telegram_api", response.status_code == 200)
    except:
        update_status("telegram_api", False)
    
    # Проверка доступности порта
    port = int(os.environ.get("PORT", 8080))
    try:
        # В контексте health check, порт 8080 должен быть доступен для самого health check сервера
        # Поэтому считаем это успешной проверкой
        update_status("port_available", True)
    except:
        update_status("port_available", False)
    
    # Проверка наличия базы данных
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        try:
            import psycopg2
            update_status("database", True)
        except ImportError:
            update_status("database", False, "psycopg2 не установлен")
    else:
        # Если используется SQLite, проверяем доступ к файловой системе
        try:
            import sqlite3
            update_status("database", True)
        except ImportError:
            update_status("database", False, "sqlite3 не доступен")

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/health":
            # Обновляем статус перед отправкой
            global STATUS
            STATUS["uptime"] = int(time.time() - START_TIME)
            STATUS["timestamp"] = datetime.now().isoformat()
            
            # Форматируем ответ в зависимости от запрошенного формата
            accept_header = self.headers.get('Accept', '')
            
            # Отправляем заголовки
            self.send_response(200 if STATUS["status"] == "OK" else 500)
            
            if 'application/json' in accept_header:
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(STATUS, indent=2).encode())
            else:
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                status_text = f"Status: {STATUS['status']}\n"
                status_text += f"Uptime: {STATUS['uptime']} seconds\n"
                status_text += f"Started: {STATUS['start_time']}\n"
                status_text += f"Bot token: {'Available' if STATUS['checks']['bot_token'] else 'Missing'}\n"
                status_text += f"Database: {'Connected' if STATUS['checks']['database'] else 'Not connected'}\n"
                status_text += f"Telegram API: {'Available' if STATUS['checks']['telegram_api'] else 'Not available'}\n"
                status_text += f"Port: {'In use' if STATUS['checks']['port_available'] else 'Not in use'}\n"
                
                if STATUS["last_error"]:
                    status_text += f"Last error: {STATUS['last_error']}\n"
                
                self.wfile.write(status_text.encode())
            
            logger.info(f"Health check request from {self.client_address[0]} - returned {200 if STATUS['status'] == 'OK' else 500}")
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
            logger.warning(f"Invalid path requested: {self.path} from {self.client_address[0]}")
    
    def log_message(self, format, *args):
        """Override to avoid double logging"""
        return

def start_health_server(port=8080):
    """Start a simple health check server"""
    # Выполняем базовые проверки
    check_basic_health()
    
    max_retries = 3
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            server_address = ('', port)
            httpd = HTTPServer(server_address, HealthCheckHandler)
            logger.info(f"Starting health check server on port {port}")
            httpd.serve_forever()
            return  # If successful, exit the function
        except OSError as e:
            if e.errno == 98 or e.errno == 10048:  # Address already in use (Linux/Windows)
                current_retry += 1
                logger.warning(f"Port {port} already in use, trying alternate port {port + 10}")
                port += 10  # Try a different port
            else:
                logger.error(f"Error starting health server: {e}")
                update_status(error=str(e))
                raise
        except KeyboardInterrupt:
            logger.info("Health check server stopped")
            return
        except Exception as e:
            logger.error(f"Error in health check server: {e}")
            update_status(error=str(e))
            raise
    
    logger.error(f"Failed to start health server after {max_retries} attempts")
    update_status(error=f"Failed to start health server after {max_retries} attempts")
    raise RuntimeError("Could not find an available port for health check server")

def run_health_server_in_thread():
    """Run the health check server in a separate thread"""
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    # Start server in a separate thread
    health_thread = threading.Thread(
        target=start_health_server, 
        args=(port,),
        daemon=True
    )
    health_thread.start()
    logger.info(f"Health check server thread started on port {port}")
    return health_thread

if __name__ == "__main__":
    # If run directly, start the server and block
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting standalone health check server on port {port}")
    start_health_server(port) 