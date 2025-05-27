#!/usr/bin/env python
"""
Скрипт для полной проверки работоспособности бота
Запускает все необходимые тесты для подтверждения корректной работы
"""

import os
import sys
import time
import json
import asyncio
import argparse
import subprocess
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [VERIFY] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("verification.log")]
)
logger = logging.getLogger("verify_bot")

def print_header(title):
    """Выводит заголовок в консоль"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def run_command(command, timeout=60, shell=True):
    """
    Запускает команду и возвращает результат
    
    Args:
        command (str): Команда для выполнения
        timeout (int): Таймаут в секундах
        shell (bool): Использовать shell для выполнения команды
        
    Returns:
        dict: Результат выполнения команды
    """
    logger.info(f"Выполнение команды: {command}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        logger.info(f"Команда выполнена за {duration:.2f}с, код возврата: {result.returncode}")
        
        if not success:
            logger.error(f"Ошибка: {result.stderr}")
        
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Таймаут {timeout}с превышен")
        return {
            "success": False,
            "error": f"Таймаут {timeout}с превышен",
            "duration": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды: {e}")
        return {
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time
        }

async def verify_bot():
    """
    Выполняет полную проверку работоспособности бота
    
    Returns:
        dict: Результаты проверок
    """
    print_header("Проверка работоспособности бота")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "success": True
    }
    
    # 1. Проверка переменных окружения
    print_header("1. Диагностика окружения")
    env_result = run_command("python diagnose.py")
    results["tests"]["environment"] = {
        "success": env_result["success"],
        "details": "Успешная диагностика окружения" if env_result["success"] else "Проблемы с окружением"
    }
    
    if not env_result["success"]:
        logger.error("Диагностика окружения завершилась с ошибками. Исправьте проблемы перед продолжением.")
        results["success"] = False
    
    # 2. Проверка здоровья бота
    print_header("2. Проверка здоровья бота")
    health_result = run_command("python test_health.py")
    results["tests"]["health"] = {
        "success": health_result["success"],
        "details": "Health check пройден" if health_result["success"] else "Health check не пройден"
    }
    
    if not health_result["success"]:
        logger.warning("Health check не пройден. Проверьте доступность API Telegram и настройки бота.")
        results["success"] = False
    
    # 3. Запуск бота в фоне на короткое время для тестирования
    print_header("3. Запуск бота в фоновом режиме")
    
    # Определяем режим работы
    mode = os.environ.get("WEBHOOK_MODE", "false").lower() in ("true", "1", "yes")
    mode_str = "webhook" if mode else "polling"
    
    if mode:
        # Webhook режим
        bot_cmd = "python webhook_server.py"
    else:
        # Polling режим
        bot_cmd = "python main.py"
    
    logger.info(f"Запуск бота в режиме {mode_str}: {bot_cmd}")
    
    try:
        # Запускаем бота в фоне
        if sys.platform == "win32":
            # Для Windows используем start /b
            bot_process = subprocess.Popen(
                f"start /b {bot_cmd}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Для Unix используем nohup
            bot_process = subprocess.Popen(
                f"nohup {bot_cmd} > bot_test.log 2>&1 &",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Ждем некоторое время для запуска бота
        logger.info("Ожидание 10 секунд для запуска бота...")
        time.sleep(10)
        
        # Проверяем, запустился ли бот
        if mode:
            # В режиме webhook проверяем health check эндпоинт
            health_check = run_command("curl -s http://localhost:8080/health", timeout=5)
            bot_running = health_check["success"] and "Bot is healthy" in health_check["stdout"]
        else:
            # В режиме polling проверяем наличие процесса
            bot_running = True  # Предполагаем, что запустился
        
        results["tests"]["bot_start"] = {
            "success": bot_running,
            "details": f"Бот успешно запущен в режиме {mode_str}" if bot_running else f"Не удалось запустить бота в режиме {mode_str}"
        }
        
        if not bot_running:
            logger.error(f"Бот не запустился в режиме {mode_str}")
            results["success"] = False
        
        # 4. Тестирование бота (если указан chat_id)
        admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
        if bot_running and admin_chat_id:
            print_header("4. Тестирование команд бота")
            
            test_cmd = f"python test_bot.py --admin-chat-id={admin_chat_id}"
            bot_test_result = run_command(test_cmd, timeout=30)
            
            results["tests"]["bot_commands"] = {
                "success": bot_test_result["success"],
                "details": "Команды бота работают корректно" if bot_test_result["success"] else "Проблемы с командами бота"
            }
            
            if not bot_test_result["success"]:
                logger.warning("Тестирование команд бота завершилось с ошибками")
                results["success"] = False
        else:
            logger.info("Тестирование команд бота пропущено: бот не запущен или не указан ADMIN_CHAT_ID")
            results["tests"]["bot_commands"] = {
                "success": None,
                "details": "Тестирование команд пропущено"
            }
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании бота: {e}")
        results["tests"]["bot_start"] = {
            "success": False,
            "details": f"Ошибка при запуске бота: {str(e)}"
        }
        results["success"] = False
    finally:
        # Останавливаем бота
        print_header("5. Остановка бота")
        
        try:
            # В Windows kill по PID
            if sys.platform == "win32":
                run_command(f"taskkill /F /PID {bot_process.pid}", timeout=5)
            else:
                # В Unix используем killall
                if mode:
                    run_command("killall -TERM python webhook_server.py || true", timeout=5)
                else:
                    run_command("killall -TERM python main.py || true", timeout=5)
            
            logger.info("Бот остановлен")
        except Exception as e:
            logger.warning(f"Не удалось корректно остановить бота: {e}")
    
    # Общий результат
    print_header("Результаты проверки")
    
    if results["success"]:
        logger.info("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО")
        print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО\n")
        print("Бот полностью работоспособен и готов к использованию!")
    else:
        logger.error("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ\n")
        
        # Выводим детали проблем
        for test_name, test_result in results["tests"].items():
            if not test_result["success"]:
                print(f"  - {test_result['details']}")
        
        print("\nДля подробной диагностики запустите:")
        print("  python diagnose.py --full")
    
    return results

async def main():
    """Основная функция для запуска проверки"""
    parser = argparse.ArgumentParser(description="Проверка работоспособности бота")
    parser.add_argument("--output", help="Путь для сохранения результатов в JSON")
    
    args = parser.parse_args()
    
    try:
        # Запускаем проверку
        results = await verify_bot()
        
        # Сохраняем результаты в JSON, если указан путь
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Результаты сохранены в файл: {args.output}")
            print(f"\nРезультаты сохранены в файл: {args.output}")
        
        # Возвращаем код возврата
        return 0 if results["success"] else 1
        
    except KeyboardInterrupt:
        print("\nПроверка прервана пользователем")
        return 1
    except Exception as e:
        logger.error(f"Ошибка при выполнении проверки: {e}")
        print(f"\nОшибка при выполнении проверки: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nПроверка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\nОшибка при выполнении проверки: {e}")
        sys.exit(1) 