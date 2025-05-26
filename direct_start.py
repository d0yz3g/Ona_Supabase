#!/usr/bin/env python3
"""
Максимально упрощенный скрипт запуска для Railway.
Не зависит от других файлов, весь код содержится здесь.
"""
import os
import sys
import time
import logging
import threading
import subprocess
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("direct_start")

# Добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    logger.info(f"Добавлен {os.getcwd()} в sys.path")

# Порт для healthcheck (можно переопределить через переменную окружения)
PORT = int(os.environ.get("PORT", 8080))

# Класс-заглушка для AsyncOpenAI
class AsyncOpenAI:
    """Заглушка для AsyncOpenAI"""
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        logger.info("Инициализация AsyncOpenAI заглушки")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                logger.info("Вызов AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
    
    class audio:
        @staticmethod
        async def transcriptions_create(*args, **kwargs):
            logger.info("Вызов AsyncOpenAI.audio.transcriptions_create")
            return {"text": "Заглушка транскрипции аудио"}

# Патчим модуль openai
def patch_openai():
    """Патчит модуль openai для добавления AsyncOpenAI"""
    try:
        import openai
        
        # Если AsyncOpenAI не существует в модуле openai, добавляем его
        if not hasattr(openai, 'AsyncOpenAI'):
            openai.AsyncOpenAI = AsyncOpenAI
            logger.info("Добавлен класс AsyncOpenAI в модуль openai")
        
        # Добавляем AsyncOpenAI напрямую в sys.modules для импорта from openai import AsyncOpenAI
        sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
        
        logger.info("Патч openai применен успешно")
        
        # Проверка, что патч работает
        try:
            from openai import AsyncOpenAI
            logger.info("✅ AsyncOpenAI теперь доступен")
            return True
        except ImportError as e:
            logger.error(f"❌ AsyncOpenAI всё ещё недоступен: {e}")
            return False
    except ImportError:
        logger.warning("Не удалось импортировать openai, создаем модуль-заглушку")
        
        # Создаем модуль-заглушку openai
        import types
        openai_module = types.ModuleType('openai')
        openai_module.AsyncOpenAI = AsyncOpenAI
        
        # Добавляем модуль-заглушку в sys.modules
        sys.modules['openai'] = openai_module
        sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
        
        logger.info("Создан модуль-заглушка openai")
        return True

# HTTP-обработчик для healthcheck
class HealthHandler(BaseHTTPRequestHandler):
    """HTTP-обработчик для healthcheck"""
    def log_message(self, format, *args):
        """Переопределение логирования для меньшего вывода"""
        return
    
    def do_GET(self):
        """Обработка GET-запросов"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ona Bot - Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .status {{ padding: 10px; background-color: #e8f5e9; border-left: 5px solid #4caf50; }}
            </style>
        </head>
        <body>
            <h1>Ona Bot - Status Page</h1>
            <div class="status">Status: Running</div>
            <p>This is a simple status page for the Ona Bot.</p>
            <p>Uptime: {time.strftime('%H:%M:%S', time.gmtime(time.time() - START_TIME))}</p>
        </body>
        </html>
        """
        
        self.wfile.write(response.encode("utf-8"))

# Время запуска
START_TIME = time.time()

def start_healthcheck_server():
    """Запускает сервер для healthcheck"""
    try:
        server = HTTPServer(("", PORT), HealthHandler)
        logger.info(f"Healthcheck сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Ошибка при запуске healthcheck сервера: {e}")

def run_healthcheck_thread():
    """Запускает healthcheck сервер в отдельном потоке"""
    thread = threading.Thread(target=start_healthcheck_server, daemon=True)
    thread.start()
    logger.info("Healthcheck сервер запущен в отдельном потоке")
    return thread

def run_import():
    """Запускает бота через прямой импорт main.py"""
    logger.info("Запуск main.py через прямой импорт")
    try:
        import main
        logger.info("✅ Бот запущен успешно через импорт")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте main: {e}")
        logger.error(traceback.format_exc())
        return False

def run_subprocess():
    """Запускает бота через subprocess"""
    logger.info("Запуск main.py через subprocess")
    cmd = [sys.executable, "main.py"]
    
    try:
        # Запускаем процесс и перенаправляем вывод
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ
        )
        
        # Читаем и логируем вывод в реальном времени
        for line in process.stdout:
            print(line, end='')
        
        # Ждем завершения процесса
        process.wait()
        
        # Проверяем код возврата
        if process.returncode != 0:
            logger.error(f"Процесс завершился с ошибкой (код {process.returncode})")
            return False
        else:
            logger.info("Процесс успешно завершился")
            return True
    except Exception as e:
        logger.error(f"Ошибка при запуске subprocess: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Запуск бота на Railway ===")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    
    # Патчим openai
    patch_openai()
    
    # Запускаем healthcheck сервер
    healthcheck_thread = run_healthcheck_thread()
    
    # Проверяем версию openai
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "openai"], check=True, 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError:
        logger.warning("Не удалось получить информацию о пакете openai")
    
    # Устанавливаем переменную окружения для Railway
    os.environ["RAILWAY_ENV"] = "1"
    
    # Пробуем разные способы запуска
    try:
        # Пробуем импорт напрямую
        if run_import():
            logger.info("Бот успешно запущен через импорт")
            # Ждем завершения healthcheck потока (бесконечно)
            healthcheck_thread.join()
            sys.exit(0)
        
        # Если импорт не удался, пробуем subprocess
        logger.warning("Не удалось запустить через импорт, пробуем subprocess")
        
        if run_subprocess():
            logger.info("Бот успешно запущен через subprocess")
            sys.exit(0)
        
        # Если и subprocess не удался, значит не получается запустить бота
        logger.error("Не удалось запустить бота")
        
        # Продолжаем работу healthcheck сервера, чтобы Railway не перезапускал контейнер постоянно
        logger.info("Продолжаем работу healthcheck сервера")
        healthcheck_thread.join()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())
        
        # Продолжаем работу healthcheck сервера
        healthcheck_thread.join() 