#!/usr/bin/env python3
"""
Скрипт для патча main.py, чтобы обойти импорт dotenv.
Запускается перед запуском основного скрипта в Railway.
"""
import os
import sys
import re

def patch_main_py():
    """Патчит main.py для обхода импорта dotenv."""
    main_py_path = 'main.py'
    
    if not os.path.exists(main_py_path):
        print(f"[ERROR] {main_py_path} не найден")
        return False
    
    # Читаем содержимое файла
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем импорт dotenv
    dotenv_import_pattern = r'from\s+dotenv\s+import\s+load_dotenv'
    
    if not re.search(dotenv_import_pattern, content):
        print("[INFO] Импорт dotenv не найден или уже обработан")
        return True
    
    # Заменяем импорт на try-except блок
    dotenv_patch = """
try:
    from dotenv import load_dotenv
    print("[INFO] Используем стандартный python-dotenv")
except ImportError:
    print("[INFO] python-dotenv не найден, используем встроенную замену")
    def load_dotenv(dotenv_path=None):
        print("[INFO] Используем встроенную замену для load_dotenv")
        return True
"""
    
    # Делаем замену
    patched_content = re.sub(dotenv_import_pattern, dotenv_patch, content)
    
    # Записываем изменения
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(patched_content)
    
    print("[INFO] main.py успешно обновлен для работы без python-dotenv")
    return True

def create_dotenv_module():
    """Создает простой модуль dotenv.py."""
    dotenv_py_path = 'dotenv.py'
    
    # Если файл уже существует, не трогаем его
    if os.path.exists(dotenv_py_path):
        print(f"[INFO] {dotenv_py_path} уже существует")
        return True
    
    # Создаем простую замену для dotenv
    dotenv_content = """
\"\"\"
Прямая замена для модуля python-dotenv.
\"\"\"
import os

def load_dotenv(dotenv_path=None, **kwargs):
    print("[INFO] Используем встроенную замену для python-dotenv")
    return True

def find_dotenv(filename='.env', **kwargs):
    if os.path.isfile(filename):
        return os.path.abspath(filename)
    return ""
"""
    
    # Записываем в файл
    with open(dotenv_py_path, 'w', encoding='utf-8') as f:
        f.write(dotenv_content)
    
    print(f"[INFO] Создан файл {dotenv_py_path}")
    return True

if __name__ == "__main__":
    print("=== Патчинг для работы без python-dotenv ===")
    
    # Проверяем наличие python-dotenv
    try:
        import dotenv
        print("[INFO] python-dotenv уже установлен, патч не требуется")
        sys.exit(0)
    except ImportError:
        print("[INFO] python-dotenv не найден, применяем патч")
    
    # Применяем патч
    success = patch_main_py() and create_dotenv_module()
    
    if success:
        print("[SUCCESS] Патч успешно применен")
        sys.exit(0)
    else:
        print("[ERROR] Ошибка при применении патча")
        sys.exit(1) 