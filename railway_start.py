#!/usr/bin/env python
"""
Скрипт запуска для Railway.
Запускает как health check сервер, так и webhook-сервер для бота.
"""

import os
import sys
import time
import logging
import subprocess
import threading
from health_check import run_health_server_in_thread

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [RAILWAY] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("railway_start")

def start_webhook_process():
    """Запускает процесс webhook-сервера"""
    logger.info("Запуск webhook-сервера...")
    
    try:
        # Запускаем процесс webhook-сервера
        process = subprocess.Popen(
            [sys.executable, "start_webhook.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Создаем потоки для вывода stdout и stderr
        def log_output(stream, prefix):
            for line in stream:
                logger.info(f"{prefix}: {line.strip()}")
                
        stdout_thread = threading.Thread(
            target=log_output,
            args=(process.stdout, "WEBHOOK"),
            daemon=True
        )
        
        stderr_thread = threading.Thread(
            target=log_output,
            args=(process.stderr, "WEBHOOK ERROR"),
            daemon=True
        )
        
        # Запускаем потоки
        stdout_thread.start()
        stderr_thread.start()
        
        logger.info("✅ Webhook-сервер запущен")
        return process
    
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске webhook-сервера: {e}")
        return None

def main():
    """Основная функция для запуска в Railway"""
    logger.info("Запуск Railway-сервера...")
    
    # Запускаем сервер проверки работоспособности
    logger.info("Запуск health check сервера...")
    health_thread = run_health_server_in_thread()
    logger.info("✅ Health check сервер запущен")
    
    # Запускаем webhook-сервер
    webhook_process = start_webhook_process()
    
    if not webhook_process:
        logger.error("❌ Не удалось запустить webhook-сервер")
        return 1
    
    # Основной цикл
    try:
        while True:
            # Проверяем, жив ли процесс webhook-сервера
            if webhook_process.poll() is not None:
                exit_code = webhook_process.poll()
                logger.error(f"❌ Webhook-сервер остановился с кодом: {exit_code}")
                
                # Перезапускаем webhook-сервер
                logger.info("Перезапуск webhook-сервера...")
                webhook_process = start_webhook_process()
                
                if not webhook_process:
                    logger.error("❌ Не удалось перезапустить webhook-сервер")
                    return 1
            
            # Ждем перед следующей проверкой
            time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
    except Exception as e:
        logger.error(f"❌ Ошибка в основном цикле: {e}")
    finally:
        # Завершаем процесс webhook-сервера
        if webhook_process and webhook_process.poll() is None:
            logger.info("Завершение webhook-сервера...")
            webhook_process.terminate()
            try:
                webhook_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Webhook-сервер не завершился за 5 секунд, принудительное завершение...")
                webhook_process.kill()
        
        logger.info("✅ Работа Railway-сервера завершена")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 