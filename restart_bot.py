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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("restart.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("restart_bot")

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
        logger.info(f"Получен сигнал {sig}, останавливаем бота...")
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        sys.exit(0)
    
    def run(self):
        """Запустить бота и перезапускать его при остановке."""
        logger.info("Запуск скрипта автоматического перезапуска")
        
        while True:
            # Проверка лимита перезапусков
            current_date = get_today()
            if current_date != self.last_restart_date:
                self.restart_count = 0
                self.last_restart_date = current_date
            
            if self.restart_count >= MAX_RESTARTS_PER_DAY:
                logger.error(f"Достигнут лимит перезапусков за день ({MAX_RESTARTS_PER_DAY}). Ожидание до следующего дня.")
                # Ждем до следующего дня
                tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                seconds_until_tomorrow = (tomorrow - datetime.datetime.now()).total_seconds()
                time.sleep(seconds_until_tomorrow)
                continue
            
            # Запуск процесса бота
            try:
                logger.info(f"Запуск бота (попытка {self.restart_count + 1})")
                self.process = subprocess.Popen(
                    [PYTHON_EXECUTABLE, BOT_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Увеличиваем счетчик перезапусков
                self.restart_count += 1
                
                # Ждем завершения процесса
                stdout, stderr = self.process.communicate()
                
                # Если процесс завершился с ошибкой, записываем ее в лог
                if self.process.returncode != 0:
                    logger.error(f"Бот завершился с кодом {self.process.returncode}")
                    if stderr:
                        logger.error(f"Ошибка: {stderr}")
                else:
                    logger.info("Бот завершился корректно")
                
                # Ждем перед перезапуском
                logger.info(f"Ожидание {RESTART_INTERVAL} секунд перед перезапуском...")
                time.sleep(RESTART_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ошибка при управлении процессом бота: {e}")
                time.sleep(RESTART_INTERVAL)

if __name__ == "__main__":
    runner = BotRunner()
    runner.run() 