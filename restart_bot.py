#!/usr/bin/env python
"""
Скрипт для автоматического перезапуска бота в случае его остановки.
Запускайте этот скрипт вместо main.py для обеспечения постоянной работы бота.
"""

import subprocess
import time
import sys
import os
import logging
import signal
import datetime
import threading

# Настройка логирования с приоритетом на вывод в консоль для Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RESTART] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Вывод в stdout для Railway
        logging.FileHandler("restart.log")  # Файл для локальной отладки
    ]
)
logger = logging.getLogger("restart_bot")

# Явный вывод для Railway
print("=" * 50)
print("RESTART MONITOR: Запуск монитора перезапуска Telegram бота")
print(f"Текущее время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# Проверка наличия psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("Библиотека psutil успешно импортирована")
    print("psutil импортирован успешно")
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("Библиотека psutil не установлена, возможности мониторинга процессов ограничены")
    print("ВНИМАНИЕ: psutil не доступен, некоторые функции отключены")

# Путь к Python интерпретатору
PYTHON_EXECUTABLE = sys.executable
# Путь к основному скрипту бота
BOT_SCRIPT = "main.py"
# Максимальное количество перезапусков за день
MAX_RESTARTS_PER_DAY = 50
# Интервал между перезапусками (в секундах)
RESTART_INTERVAL = 5

def get_today():
    """Получить текущую дату в формате строки."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def stream_output(stream, prefix):
    """Функция для чтения и вывода потока в реальном времени."""
    for line in iter(stream.readline, b''):
        if line:
            decoded_line = line.decode('utf-8', errors='replace').strip()
            if decoded_line:  # Проверка на пустую строку
                print(f"{prefix}: {decoded_line}")
                sys.stdout.flush()  # Принудительный сброс буфера для Railway

class BotRunner:
    def __init__(self):
        self.restart_count = 0
        self.last_restart_date = get_today()
        self.process = None
        # Обработчик сигнала для корректной остановки
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, sig, frame):
        """Обработчик сигналов для корректной остановки."""
        signal_name = "SIGINT" if sig == signal.SIGINT else "SIGTERM"
        logger.info(f"Получен сигнал {signal_name}, останавливаем бота...")
        print(f"СИГНАЛ: Получен {signal_name}, завершение работы монитора...")
        
        if self.process:
            try:
                print(f"Отправляем сигнал остановки процессу бота (PID: {self.process.pid})...")
                self.process.terminate()
                self.process.wait(timeout=5)
                print("Процесс бота успешно завершен")
            except subprocess.TimeoutExpired:
                print("Процесс не завершился вовремя, принудительное завершение...")
                self.process.kill()
                print("Процесс бота принудительно завершен")
        
        print("Монитор перезапуска завершает работу")
        sys.exit(0)
    
    def check_environment(self):
        """Проверка окружения перед запуском бота."""
        print(f"Система: {sys.platform}")
        print(f"Python: {sys.version}")
        print(f"Рабочая директория: {os.getcwd()}")
        print(f"Скрипт бота: {BOT_SCRIPT}")
        
        # Проверка наличия зависимостей
        try:
            import aiogram
            print(f"aiogram версия: {aiogram.__version__}")
        except ImportError:
            logger.error("aiogram не установлен!")
            print("КРИТИЧЕСКАЯ ОШИБКА: aiogram не установлен")
        
        # Проверка наличия файла бота
        if not os.path.exists(BOT_SCRIPT):
            logger.error(f"Файл бота {BOT_SCRIPT} не найден!")
            print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл {BOT_SCRIPT} не существует")
            return False
            
        return True
    
    def run(self):
        """Запустить бота и перезапускать его при остановке."""
        logger.info("Запуск скрипта автоматического перезапуска")
        print("МОНИТОР: Начало работы монитора автоматического перезапуска")
        
        # Проверка окружения
        if not self.check_environment():
            logger.error("Проверка окружения не пройдена, монитор завершает работу")
            print("КРИТИЧЕСКАЯ ОШИБКА: Невозможно запустить бота из-за проблем с окружением")
            return
        
        while True:
            # Проверка лимита перезапусков
            current_date = get_today()
            if current_date != self.last_restart_date:
                self.restart_count = 0
                self.last_restart_date = current_date
                print(f"МОНИТОР: Сброс счетчика перезапусков. Новая дата: {current_date}")
            
            if self.restart_count >= MAX_RESTARTS_PER_DAY:
                error_msg = f"Достигнут лимит перезапусков за день ({MAX_RESTARTS_PER_DAY}). Ожидание до следующего дня."
                logger.error(error_msg)
                print(f"ОШИБКА: {error_msg}")
                
                # Ждем до следующего дня
                tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                seconds_until_tomorrow = (tomorrow - datetime.datetime.now()).total_seconds()
                print(f"МОНИТОР: Ожидание {seconds_until_tomorrow} секунд до сброса счетчика...")
                time.sleep(seconds_until_tomorrow)
                continue
            
            # Запуск процесса бота
            try:
                logger.info(f"Запуск бота (попытка {self.restart_count + 1})")
                print(f"МОНИТОР: Запуск бота (попытка {self.restart_count + 1} из {MAX_RESTARTS_PER_DAY})")
                
                # Запуск процесса с перенаправлением вывода для чтения в реальном времени
                self.process = subprocess.Popen(
                    [PYTHON_EXECUTABLE, BOT_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,  # Отключаем буферизацию для бинарного режима
                    universal_newlines=False  # Бинарный режим для совместимости
                )
                
                print(f"МОНИТОР: Бот запущен с PID {self.process.pid}")
                
                # Запуск потоков для чтения вывода в реальном времени
                stdout_thread = threading.Thread(
                    target=stream_output, 
                    args=(self.process.stdout, "БОТ"),
                    daemon=True
                )
                stderr_thread = threading.Thread(
                    target=stream_output, 
                    args=(self.process.stderr, "ОШИБКА"),
                    daemon=True
                )
                
                stdout_thread.start()
                stderr_thread.start()
                
                # Увеличиваем счетчик перезапусков
                self.restart_count += 1
                
                # Ждем завершения процесса
                return_code = self.process.wait()
                
                # Ждем завершения потоков вывода
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)
                
                # Если процесс завершился с ошибкой, записываем ее в лог
                if return_code != 0:
                    logger.error(f"Бот завершился с кодом {return_code}")
                    print(f"МОНИТОР: Бот завершился с кодом ошибки {return_code}")
                else:
                    logger.info("Бот завершился корректно")
                    print("МОНИТОР: Бот завершился штатно")
                
                # Ждем перед перезапуском
                logger.info(f"Ожидание {RESTART_INTERVAL} секунд перед перезапуском...")
                print(f"МОНИТОР: Пауза {RESTART_INTERVAL} секунд перед следующим запуском...")
                time.sleep(RESTART_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ошибка при управлении процессом бота: {e}")
                print(f"МОНИТОР ОШИБКА: {e}")
                time.sleep(RESTART_INTERVAL)

if __name__ == "__main__":
    # Обработка аргументов командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        print("МОНИТОР: Запуск в режиме отладки")
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Запуск монитора
    runner = BotRunner()
    runner.run() 