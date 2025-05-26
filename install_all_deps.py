#!/usr/bin/env python3
import subprocess
import sys
import os

def install_package(package_name, version=None):
    package_str = package_name if version is None else f"{package_name}=={version}"
    print(f"Установка {package_str}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", package_str])
        print(f"✅ Успешно установлен {package_str}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_str}: {e}")
        return False

def check_package(package_name):
    try:
        __import__(package_name)
        print(f"✅ {package_name} успешно импортирован")
        return True
    except ImportError:
        print(f"❌ {package_name} не удалось импортировать")
        return False

def main():
    print("=== Установка всех необходимых зависимостей для ONA Bot ===")
    
    # Основные зависимости
    dependencies = [
        ("pydantic", "1.10.12"),
        ("aiogram", "3.0.0"),
        "python-dotenv",
        "APScheduler",
        ("openai", "0.28.1"),
        ("httpx", "0.23.3"),
        ("elevenlabs", "0.2.24"),
        ("gTTS", "2.3.2"),
        ("ephem", "4.1.4"),
        ("PyYAML", "6.0.1"),
        # Supabase dependencies
        ("postgrest-py", "0.10.3"),
        ("realtime-py", "0.1.2"),
        ("storage3", "0.5.0"),
        ("supafunc", "0.2.2")
    ]
    
    # Установка всех зависимостей
    for dep in dependencies:
        if isinstance(dep, tuple):
            package_name, version = dep
            install_package(package_name, version)
        else:
            install_package(dep)
    
    # Проверка основных модулей
    print("\n=== Проверка основных модулей ===")
    critical_modules = ["openai", "httpx", "aiogram", "dotenv"]
    all_ok = True
    
    for module in critical_modules:
        if not check_package(module):
            all_ok = False
    
    if all_ok:
        print("\n✅ Все основные модули установлены успешно!")
    else:
        print("\n❌ Некоторые модули не удалось установить")
        
    # Вывод путей Python для отладки
    print("\nPython path:")
    for path in sys.path:
        print(f"  - {path}")
        
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 