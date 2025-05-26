#!/usr/bin/env python
"""
Dedicated health check server for Railway
This provides a simple HTTP server that responds to the health check path.
"""

import os
import sys
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [HEALTH] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("health_check")

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK - Bot is healthy and running")
            logger.info(f"Health check request from {self.client_address[0]} - returned 200 OK")
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
            if e.errno == 98:  # Address already in use
                current_retry += 1
                logger.warning(f"Port {port} already in use, trying alternate port {port + 10}")
                port += 10  # Try a different port
            else:
                logger.error(f"Error starting health server: {e}")
                raise
        except KeyboardInterrupt:
            logger.info("Health check server stopped")
            return
        except Exception as e:
            logger.error(f"Error in health check server: {e}")
            raise
    
    logger.error(f"Failed to start health server after {max_retries} attempts")
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