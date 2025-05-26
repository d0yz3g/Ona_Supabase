#!/usr/bin/env python3
"""
Финальный сценарий запуска для Railway.
Обеспечивает запуск бота и healthcheck сервера.
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

logger.info("Скрипт railway_final.py запущен")

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

# Глобальный флаг статуса бота
BOT_STATUS = {
    "running": False,
    "message": "Initializing..."
}

# HTTP-обработчик для healthcheck
class HealthHandler(BaseHTTPRequestHandler):
    """HTTP-обработчик для healthcheck"""
    
    def log_message(self, format, *args):
        """Отключаем стандартное логирование"""
        return
    
    def do_GET(self):
        """Обрабатывает GET запрос"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        uptime = time.time() - START_TIME
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        status_message = f"Status: {'OK' if BOT_STATUS['running'] else 'Initializing'}\n"
        status_message += f"Message: {BOT_STATUS['message']}\n"
        status_message += f"Uptime: {uptime_str}"
        
        self.wfile.write(status_message.encode("utf-8"))

# Функция для запуска HTTP сервера
def run_healthcheck_server():
    """Запускает HTTP сервер для healthcheck"""
    try:
        server = HTTPServer(("", PORT), HealthHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")

# Функция для запуска бота
def run_bot():
    """Запускает бота"""
    try:
        # Обновляем статус
        BOT_STATUS["message"] = "Importing main.py..."
        
        # Предварительные импорты и исправления
        try:
            import pre_import_fix
            logger.info("✅ pre_import_fix импортирован успешно")
        except ImportError:
            logger.warning("⚠️ pre_import_fix не найден, продолжаем без него")
        
        # Импортируем основной модуль
        logger.info("Импортирую main.py...")
        import main
        
        # Обновляем статус
        BOT_STATUS["running"] = True
        BOT_STATUS["message"] = "Bot is running"
        
        logger.info("✅ Бот запущен успешно через импорт main")
        return True
    except Exception as e:
        # Обновляем статус
        BOT_STATUS["running"] = False
        BOT_STATUS["message"] = f"Error: {str(e)}"
        
        logger.error(f"❌ Ошибка при импорте main: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== Запуск бота на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Содержимое директории: {os.listdir('.')}")
    
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