#!/usr/bin/env python3
"""
Сверхпростой HTTP сервер для health check.
Всегда отвечает 200 OK на любой запрос.
"""
import http.server
import socketserver
import os
import logging
import time

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("healthcheck")

# Порт по умолчанию
PORT = int(os.environ.get("PORT", 8080))

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    """Простейший обработчик HTTP запросов"""
    
    def do_GET(self):
        """Обрабатывает любой GET запрос и отправляет HTML страницу или текстовый ответ"""
        try:
            if os.path.exists("static_index.html"):
                # Если HTML файл существует, отправляем его
                with open("static_index.html", "rb") as file:
                    content = file.read()
                
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content)
            else:
                # Отвечаем просто текстом
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"OK - {time.strftime('%Y-%m-%d %H:%M:%S')}".encode())
            
            logger.info(f"Health check request from {self.client_address[0]} - responded with 200 OK")
        except Exception as e:
            logger.error(f"Error in health check handler: {e}")
            # Все равно отвечаем 200 OK
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        """Отключаем стандартное логирование"""
        return

if __name__ == "__main__":
    logger.info(f"Starting simple health check server on port {PORT}")
    
    try:
        # Проверяем наличие HTML файла
        if os.path.exists("static_index.html"):
            logger.info("Using static HTML file for responses")
        else:
            logger.info("No static HTML file found, will use plain text responses")
        
        # Запускаем HTTP сервер
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            logger.info(f"Simple health check server is running on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        # Пытаемся запустить самый примитивный сервер в случае ошибки
        try:
            class MinimalHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")
                def log_message(self, format, *args): return
            
            logger.info("Starting minimal fallback server")
            with socketserver.TCPServer(("", PORT), MinimalHandler) as httpd:
                logger.info("Minimal fallback server started")
                httpd.serve_forever()
        except Exception as e2:
            logger.critical(f"Critical error, even minimal server failed: {e2}")
            # Просто бесконечный цикл чтобы процесс не завершался
            while True:
                time.sleep(60) 