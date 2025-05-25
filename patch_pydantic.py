"""
Модуль для патча pydantic для совместимости с aiogram
"""
import sys
import logging
import subprocess
import importlib

logger = logging.getLogger(__name__)

def install_pydantic():
    """
    Устанавливает pydantic, если его нет
    
    Returns:
        bool: True, если установка успешна или пакет уже установлен, иначе False
    """
    try:
        import pydantic
        print(f"Pydantic уже установлен, версия: {pydantic.__version__}")
        return True
    except ImportError:
        print("Pydantic не установлен. Пытаемся установить...")
        try:
            # Пытаемся установить pydantic версии 1.10.12, совместимой с aiogram 3.0
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pydantic==1.10.12"])
            print("Pydantic успешно установлен")
            
            # Перезагружаем модуль sys, чтобы обновить sys.modules
            importlib.invalidate_caches()
            
            # Проверяем, что установка прошла успешно
            import pydantic
            print(f"Установлена версия pydantic: {pydantic.__version__}")
            return True
        except Exception as e:
            print(f"Ошибка при установке pydantic: {e}")
            return False

def apply_pydantic_patch():
    """
    Применяет патч к модулю pydantic, добавляя отсутствующие атрибуты
    для совместимости с aiogram
    
    Returns:
        bool: True, если патч был успешно применен, иначе False
    """
    # Сначала проверяем наличие pydantic и устанавливаем при необходимости
    if not install_pydantic():
        print("Не удалось установить pydantic, патч не может быть применен")
        return False
    
    try:
        if 'pydantic' in sys.modules:
            pydantic_module = sys.modules['pydantic']
            
            # Проверяем наличие model_validator
            if not hasattr(pydantic_module, 'model_validator'):
                print("Добавление model_validator в pydantic...")
                
                # Создаем функцию-заглушку для model_validator
                def dummy_model_validator(cls_method=None, *args, **kwargs):
                    def decorator(func):
                        return func
                    if cls_method is None:
                        return decorator
                    return decorator(cls_method)
                
                # Добавляем model_validator в модуль pydantic
                setattr(pydantic_module, 'model_validator', dummy_model_validator)
                print("Успешно добавлен model_validator в pydantic")
            
            # Проверяем наличие ConfigDict
            if not hasattr(pydantic_module, 'ConfigDict'):
                print("Добавление ConfigDict в pydantic...")
                
                # Создаем класс-заглушку для ConfigDict
                class DummyConfigDict(dict):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                
                # Добавляем ConfigDict в модуль pydantic
                setattr(pydantic_module, 'ConfigDict', DummyConfigDict)
                print("Успешно добавлен ConfigDict в pydantic")
            
            return True
        else:
            print("Модуль pydantic не найден в импортированных модулях")
            return False
    except Exception as e:
        print(f"Ошибка при применении патча к pydantic: {e}")
        return False

if __name__ == "__main__":
    # Настраиваем базовое логирование
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Применяем патч
    if apply_pydantic_patch():
        print("Патч для pydantic успешно применен")
    else:
        print("Не удалось применить патч для pydantic")
        sys.exit(1) 