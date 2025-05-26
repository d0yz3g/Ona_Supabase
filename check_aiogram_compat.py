#!/usr/bin/env python3
"""
Скрипт для проверки совместимости aiogram 3.0.0 и pydantic
Запускается в Docker для проверки правильной работы импорта модулей
"""
import sys
import importlib.metadata

def check_versions():
    """Проверяет установленные версии aiogram и pydantic"""
    try:
        aiogram_version = importlib.metadata.version('aiogram')
        pydantic_version = importlib.metadata.version('pydantic')
        
        print(f"Версия aiogram: {aiogram_version}")
        print(f"Версия pydantic: {pydantic_version}")
        
        # Проверяем совместимость версий
        major_pydantic = int(pydantic_version.split('.')[0])
        if major_pydantic < 2:
            print("⚠️ Внимание: aiogram 3.0.0 требует pydantic версии 2.x")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке версий: {e}")
        return False

def test_imports():
    """Тестирует импорт ключевых модулей aiogram"""
    try:
        print("Импорт базовых классов aiogram...")
        from aiogram import Bot, Dispatcher, F
        print("✅ Базовые классы aiogram импортированы успешно")
        
        print("Импорт модулей aiogram.types...")
        from aiogram.types import Message, Update
        print("✅ Базовые типы aiogram импортированы успешно")
        
        print("Импорт модуля TelegramObject (использует model_validator)...")
        from aiogram.types.base import TelegramObject
        print("✅ TelegramObject импортирован успешно")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

if __name__ == "__main__":
    print("=== Проверка совместимости aiogram 3.0.0 и pydantic ===")
    
    versions_ok = check_versions()
    imports_ok = test_imports()
    
    if versions_ok and imports_ok:
        print("\n✅ Все проверки пройдены успешно!")
        sys.exit(0)
    else:
        print("\n❌ Обнаружены проблемы совместимости")
        print("Рекомендация: выполните следующие команды:")
        print("pip uninstall -y pydantic")
        print("pip install pydantic==2.1.1")
        print("pip uninstall -y aiogram")
        print("pip install aiogram==3.0.0")
        sys.exit(1) 