#!/usr/bin/env python3
import subprocess
import sys
import importlib.metadata

def check_pydantic_version():
    """Проверяет версию pydantic и исправляет её, если нужно"""
    try:
        pydantic_version = importlib.metadata.version('pydantic')
        print(f"Текущая версия pydantic: {pydantic_version}")
        
        major_version = int(pydantic_version.split('.')[0])
        if major_version < 2:
            print("Версия pydantic несовместима с aiogram 3.0.0. Требуется версия 2.x")
            print("Установка pydantic 2.1.1...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", "pydantic==2.1.1"])
            print("✅ Pydantic 2.1.1 установлен")
        else:
            print("✅ Установлена совместимая версия pydantic")
    except Exception as e:
        print(f"❌ Ошибка при проверке/установке pydantic: {e}")
        print("Принудительная установка pydantic 2.1.1...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", "pydantic==2.1.1"])

def check_aiogram_compatibility():
    """Проверяет совместимость aiogram и pydantic"""
    try:
        # Проверяем импорт базовых классов aiogram
        print("Проверка импорта aiogram...")
        from aiogram import Bot, Dispatcher
        print("✅ Базовые классы aiogram импортированы успешно")
        
        # Проверяем импорт типов, где используется model_validator
        print("Проверка импорта типов aiogram...")
        from aiogram.types.base import TelegramObject
        print("✅ Типы aiogram импортированы успешно")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

if __name__ == "__main__":
    print("=== Проверка и исправление совместимости pydantic и aiogram ===")
    
    # Сначала проверяем и исправляем версию pydantic
    check_pydantic_version()
    
    # Проверяем совместимость
    if check_aiogram_compatibility():
        print("\n✅ Pydantic и aiogram совместимы!")
        sys.exit(0)
    else:
        print("\n❌ Проблемы совместимости не устранены. Попробуйте переустановить aiogram:")
        print("pip install --no-cache-dir --force-reinstall aiogram==3.0.0")
        sys.exit(1) 