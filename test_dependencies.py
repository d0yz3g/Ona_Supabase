#!/usr/bin/env python
"""
Тест для проверки совместимости всех основных библиотек в проекте.
"""

import sys
import importlib

def check_import(module_name, expected_version=None):
    """Проверка импорта модуля и его версии"""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "неизвестно")
        print(f"✅ {module_name}: успешно импортирован (версия: {version})")
        
        if expected_version and version != expected_version:
            print(f"⚠️ Ожидалась версия {expected_version}, но установлена {version}")
            
        return True
    except ImportError as e:
        print(f"❌ {module_name}: ошибка импорта - {e}")
        return False
    except Exception as e:
        print(f"❌ {module_name}: неожиданная ошибка - {e}")
        return False

def main():
    """Основная функция проверки зависимостей"""
    print("🔍 Начинаем проверку зависимостей...")
    
    dependencies = [
        # Телеграм-бот
        "aiogram",
        "magic_filter",
        
        # Supabase
        "supabase",
        "postgrest",
        "gotrue",
        "storage3",
        
        # HTTP клиенты
        "httpx",
        "aiohttp",
        
        # Генерация текста и голоса
        "openai",
        "elevenlabs",
        "gtts",
        
        # Планировщик
        "apscheduler",
        
        # Прочие утилиты
        "pydantic",
        "dotenv",
        "ephem"
    ]
    
    success_count = 0
    for dep in dependencies:
        if check_import(dep):
            success_count += 1
    
    total = len(dependencies)
    print(f"\n✅ Итоги: {success_count}/{total} зависимостей импортировано успешно")
    
    if success_count == total:
        print("🎉 Все зависимости совместимы!")
        return 0
    else:
        print(f"⚠️ {total - success_count} зависимостей не удалось импортировать")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 