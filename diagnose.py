#!/usr/bin/env python
"""
Диагностический скрипт для проверки работоспособности бота
Выявляет распространенные проблемы и предлагает решения
"""

import os
import sys
import json
import time
import socket
import logging
import subprocess
import platform
import psutil
import asyncio
import argparse
import requests
from dotenv import load_dotenv
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [DIAGNOSE] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("diagnose.log")]
)
logger = logging.getLogger("diagnose")

# Загружаем переменные окружения
load_dotenv()

# Константы для проверки
REQUIRED_ENV_VARS = ["BOT_TOKEN"]
OPTIONAL_ENV_VARS = ["OPENAI_API_KEY", "ELEVEN_TOKEN", "WEBHOOK_URL", "DATABASE_URL"]
REQUIRED_FILES = ["main.py", "webhook_server.py", "health_check.py"]
REQUIRED_MODULES = ["aiogram", "openai", "dotenv", "psutil", "requests"]

def print_section(title):
    """Печатает заголовок секции в консоли"""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)

def check_env_variables():
    """Проверяет наличие и валидность переменных окружения"""
    print_section("Проверка переменных окружения")
    
    result = {
        "success": True,
        "missing_required": [],
        "missing_optional": [],
        "webhook_mode": os.getenv("WEBHOOK_MODE", "false").lower() in ("true", "1", "yes")
    }
    
    # Проверяем обязательные переменные
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            result["missing_required"].append(var)
            result["success"] = False
            logger.warning(f"Обязательная переменная {var} не найдена")
    
    # Проверяем опциональные переменные
    for var in OPTIONAL_ENV_VARS:
        if not os.getenv(var):
            result["missing_optional"].append(var)
            logger.info(f"Опциональная переменная {var} не найдена")
    
    # Проверяем согласованность webhook настроек
    if result["webhook_mode"]:
        webhook_url = os.getenv("WEBHOOK_URL")
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        
        if not webhook_url and not railway_domain:
            logger.warning("Режим webhook включен, но не указан ни WEBHOOK_URL, ни RAILWAY_PUBLIC_DOMAIN")
            result["webhook_config_issue"] = "missing_url"
            result["success"] = False
    
    # Вывод результатов
    if result["success"]:
        print("✅ Все обязательные переменные окружения настроены корректно")
    else:
        print("❌ Проблемы с переменными окружения:")
        if result["missing_required"]:
            print(f"  - Отсутствуют обязательные переменные: {', '.join(result['missing_required'])}")
    
    if result["missing_optional"]:
        print(f"⚠️ Отсутствуют опциональные переменные: {', '.join(result['missing_optional'])}")
        print("  Это может ограничить функциональность бота")
    
    if result["webhook_mode"]:
        print(f"ℹ️ Режим работы: webhook")
        if "webhook_config_issue" in result:
            print("❌ Проблема с настройками webhook: не указан URL")
    else:
        print(f"ℹ️ Режим работы: polling")
    
    return result

def check_files():
    """Проверяет наличие необходимых файлов"""
    print_section("Проверка файлов проекта")
    
    result = {
        "success": True,
        "missing_files": []
    }
    
    # Проверяем обязательные файлы
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            result["missing_files"].append(file)
            result["success"] = False
            logger.warning(f"Обязательный файл {file} не найден")
    
    # Выводим результаты
    if result["success"]:
        print("✅ Все обязательные файлы найдены")
    else:
        print("❌ Не найдены следующие файлы:")
        for file in result["missing_files"]:
            print(f"  - {file}")
    
    return result

def check_dependencies():
    """Проверяет наличие необходимых модулей Python"""
    print_section("Проверка зависимостей")
    
    result = {
        "success": True,
        "missing_modules": [],
        "versions": {}
    }
    
    # Проверяем наличие и версии модулей
    for module in REQUIRED_MODULES:
        try:
            # Пытаемся импортировать модуль
            module_obj = __import__(module)
            version = getattr(module_obj, "__version__", "Неизвестно")
            result["versions"][module] = version
            logger.info(f"Модуль {module} найден, версия: {version}")
        except ImportError:
            result["missing_modules"].append(module)
            result["success"] = False
            logger.warning(f"Модуль {module} не найден")
    
    # Проверяем версию Python
    python_version = platform.python_version()
    result["python_version"] = python_version
    
    if not python_version.startswith("3."):
        result["python_version_issue"] = True
        result["success"] = False
        logger.warning(f"Несовместимая версия Python: {python_version}, рекомендуется Python 3.x")
    
    # Выводим результаты
    if result["success"]:
        print(f"✅ Все необходимые зависимости установлены")
        print(f"  Python: {python_version}")
        for module, version in result["versions"].items():
            print(f"  {module}: {version}")
    else:
        print("❌ Проблемы с зависимостями:")
        if "python_version_issue" in result:
            print(f"  - Несовместимая версия Python: {python_version}")
        
        if result["missing_modules"]:
            print(f"  - Отсутствуют модули: {', '.join(result['missing_modules'])}")
            print("  Установите недостающие модули с помощью команды:")
            print(f"  pip install {' '.join(result['missing_modules'])}")
    
    return result

def check_network():
    """Проверяет сетевые соединения и доступность API"""
    print_section("Проверка сети")
    
    result = {
        "success": True,
        "telegram_api": False,
        "open_ports": [],
        "issues": []
    }
    
    # Проверяем доступность API Telegram
    try:
        response = requests.get("https://api.telegram.org", timeout=5)
        result["telegram_api"] = response.status_code == 200
        logger.info(f"API Telegram доступен: {result['telegram_api']}")
    except requests.RequestException as e:
        result["telegram_api"] = False
        result["issues"].append(f"Не удалось подключиться к API Telegram: {e}")
        result["success"] = False
        logger.warning(f"Не удалось подключиться к API Telegram: {e}")
    
    # Проверяем занятые порты
    for port in [8080, 8443, 5000]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result_code = sock.connect_ex(('localhost', port))
            if result_code == 0:
                result["open_ports"].append(port)
                logger.info(f"Порт {port} занят")
            sock.close()
        except:
            pass
    
    # Выводим результаты
    if result["telegram_api"]:
        print("✅ API Telegram доступен")
    else:
        print("❌ Не удалось подключиться к API Telegram")
        print("  Проверьте подключение к интернету")
    
    if result["open_ports"]:
        print(f"ℹ️ Занятые порты: {', '.join(map(str, result['open_ports']))}")
        
        # Проверяем, кто занимает порт 8080
        if 8080 in result["open_ports"]:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == 8080:
                            print(f"  Порт 8080 занят процессом: {proc.info['name']} (PID: {proc.info['pid']})")
                            break
            except:
                pass
    else:
        print("✅ Порты 8080, 8443, 5000 свободны")
    
    return result

async def check_bot_token():
    """Проверяет валидность токена бота"""
    print_section("Проверка токена бота")
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ Токен бота не указан")
        return {
            "success": False,
            "error": "Токен бота не указан"
        }
    
    result = {
        "success": False,
        "bot_info": None,
        "error": None
    }
    
    try:
        # Используем requests для простого запроса к API
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getMe",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                result["success"] = True
                result["bot_info"] = data.get("result")
                logger.info(f"Токен бота валиден, бот: @{result['bot_info'].get('username')}")
                
                # Выводим информацию о боте
                print(f"✅ Токен бота валиден")
                print(f"  Имя бота: {result['bot_info'].get('first_name')}")
                print(f"  Username: @{result['bot_info'].get('username')}")
                print(f"  ID бота: {result['bot_info'].get('id')}")
            else:
                result["error"] = data.get("description", "Неизвестная ошибка")
                logger.error(f"Токен бота не валиден: {result['error']}")
                print(f"❌ Токен бота не валиден: {result['error']}")
        else:
            result["error"] = f"Статус ответа: {response.status_code}"
            logger.error(f"Ошибка при проверке токена бота: {result['error']}")
            print(f"❌ Ошибка при проверке токена бота: {result['error']}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Исключение при проверке токена бота: {e}")
        print(f"❌ Ошибка при проверке токена бота: {e}")
    
    return result

def run_command(command, timeout=10):
    """Запускает команду и возвращает результат"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Таймаут {timeout}с превышен"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_system_resources():
    """Проверяет системные ресурсы"""
    print_section("Проверка системных ресурсов")
    
    result = {
        "success": True,
        "memory": {},
        "cpu": {},
        "disk": {},
        "issues": []
    }
    
    try:
        # Проверка памяти
        memory = psutil.virtual_memory()
        result["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
        
        # Проверка CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        result["cpu"] = {
            "cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(),
            "percent_used": cpu_percent
        }
        
        # Проверка диска
        disk = psutil.disk_usage('/')
        result["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": disk.percent
        }
        
        # Проверяем наличие проблем с ресурсами
        if memory.percent > 90:
            result["issues"].append("Высокая загрузка памяти (>90%)")
            result["success"] = False
        
        if cpu_percent > 90:
            result["issues"].append("Высокая загрузка CPU (>90%)")
            result["success"] = False
        
        if disk.percent > 95:
            result["issues"].append("Мало свободного места на диске (<5%)")
            result["success"] = False
        
        # Выводим результаты
        print(f"ℹ️ CPU: {result['cpu']['percent_used']}% использовано, {result['cpu']['logical_cores']} ядер")
        print(f"ℹ️ Память: {result['memory']['percent_used']}% использовано, {result['memory']['available_gb']} ГБ доступно из {result['memory']['total_gb']} ГБ")
        print(f"ℹ️ Диск: {result['disk']['percent_used']}% использовано, {result['disk']['free_gb']} ГБ свободно из {result['disk']['total_gb']} ГБ")
        
        if result["issues"]:
            print("⚠️ Обнаружены проблемы с ресурсами:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        else:
            print("✅ Системные ресурсы в норме")
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        logger.error(f"Ошибка при проверке системных ресурсов: {e}")
        print(f"❌ Ошибка при проверке системных ресурсов: {e}")
    
    return result

def generate_recommendations(results):
    """Генерирует рекомендации на основе результатов проверок"""
    print_section("Рекомендации")
    
    recommendations = []
    
    # Рекомендации по переменным окружения
    if not results["env_variables"]["success"]:
        if results["env_variables"]["missing_required"]:
            recommendations.append(
                "Добавьте обязательные переменные окружения в файл .env: " +
                ", ".join(results["env_variables"]["missing_required"])
            )
        
        if "webhook_config_issue" in results["env_variables"]:
            recommendations.append(
                "Для работы в режиме webhook укажите WEBHOOK_URL или RAILWAY_PUBLIC_DOMAIN в файле .env"
            )
    
    # Рекомендации по файлам
    if not results["files"]["success"]:
        recommendations.append(
            "Убедитесь, что все необходимые файлы присутствуют в проекте: " +
            ", ".join(results["files"]["missing_files"])
        )
    
    # Рекомендации по зависимостям
    if not results["dependencies"]["success"]:
        if "python_version_issue" in results["dependencies"]:
            recommendations.append(
                f"Используйте Python версии 3.x вместо {results['dependencies']['python_version']}"
            )
        
        if results["dependencies"]["missing_modules"]:
            recommendations.append(
                "Установите недостающие модули с помощью команды: pip install " +
                " ".join(results["dependencies"]["missing_modules"])
            )
    
    # Рекомендации по сети
    if not results["network"]["success"]:
        if not results["network"]["telegram_api"]:
            recommendations.append(
                "Проверьте подключение к интернету и доступность api.telegram.org"
            )
    
    # Рекомендации по токену бота
    if not results["bot_token"]["success"]:
        recommendations.append(
            "Проверьте правильность токена бота в файле .env"
        )
    
    # Рекомендации по системным ресурсам
    if not results["system_resources"]["success"]:
        for issue in results["system_resources"].get("issues", []):
            if "памяти" in issue:
                recommendations.append(
                    "Освободите оперативную память, закрыв ненужные приложения"
                )
            elif "CPU" in issue:
                recommendations.append(
                    "Снизьте нагрузку на процессор, закрыв ресурсоемкие приложения"
                )
            elif "диске" in issue:
                recommendations.append(
                    "Освободите место на диске, удалив ненужные файлы"
                )
    
    # Добавляем общие рекомендации
    if results["env_variables"]["webhook_mode"]:
        recommendations.append(
            "В режиме webhook запускайте бота с помощью команды: python webhook_server.py"
        )
    else:
        recommendations.append(
            "В режиме polling запускайте бота с помощью команды: python main.py"
        )
    
    if results["network"]["open_ports"] and 8080 in results["network"]["open_ports"]:
        recommendations.append(
            "Порт 8080 уже занят. Используйте другой порт или освободите этот порт."
        )
    
    # Выводим рекомендации
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ Все проверки пройдены успешно, рекомендаций нет")
    
    return recommendations

async def main():
    """Основная функция для запуска диагностики"""
    parser = argparse.ArgumentParser(description="Диагностика бота Telegram")
    parser.add_argument("--full", action="store_true", help="Выполнить полную диагностику")
    parser.add_argument("--no-color", action="store_true", help="Отключить цветной вывод")
    parser.add_argument("--output", help="Путь для сохранения результатов в JSON")
    
    args = parser.parse_args()
    
    # Отключаем цветной вывод, если указан флаг
    if args.no_color:
        os.environ["NO_COLOR"] = "1"
    
    print_section("Диагностика бота Telegram")
    print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Платформа: {platform.platform()}")
    print(f"Python: {platform.python_version()}")
    
    # Выполняем проверки
    results = {}
    
    try:
        # Обязательные проверки
        results["env_variables"] = check_env_variables()
        results["files"] = check_files()
        results["dependencies"] = check_dependencies()
        results["network"] = check_network()
        results["bot_token"] = await check_bot_token()
        
        # Дополнительные проверки для полной диагностики
        if args.full:
            results["system_resources"] = check_system_resources()
        else:
            # Упрощенная проверка системных ресурсов
            results["system_resources"] = {"success": True}
        
        # Генерируем рекомендации
        results["recommendations"] = generate_recommendations(results)
        
        # Общий результат
        results["success"] = all(results[key]["success"] for key in results if key != "recommendations")
        
        # Сохраняем результаты в JSON, если указан путь
        if args.output:
            # Преобразуем результаты в JSON-совместимый формат
            json_results = {}
            for key, value in results.items():
                if isinstance(value, dict):
                    # Удаляем несериализуемые объекты
                    json_results[key] = {k: v for k, v in value.items() if k != "result_obj"}
                else:
                    json_results[key] = value
            
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(json_results, f, ensure_ascii=False, indent=2)
            
            print(f"\nРезультаты сохранены в файл: {args.output}")
        
        # Выводим итоговый результат
        print_section("Итоговый результат")
        if results["success"]:
            print("✅ Все проверки пройдены успешно")
            print("Бот готов к запуску!")
        else:
            print("❌ Обнаружены проблемы, требующие внимания")
            print("Следуйте рекомендациям выше для решения проблем")
    
    except KeyboardInterrupt:
        print("\nДиагностика прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка при выполнении диагностики: {e}")
        print(f"\n❌ Ошибка при выполнении диагностики: {e}")
        return 1
    
    return 0 if results.get("success", False) else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nДиагностика прервана пользователем")
    except Exception as e:
        print(f"\nОшибка при выполнении диагностики: {e}")
        sys.exit(1) 