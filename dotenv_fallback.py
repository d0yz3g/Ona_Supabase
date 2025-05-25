"""
Fallback модуль для python-dotenv.
Используется в случае, если не удалось установить python-dotenv.
"""
import os
import sys
import logging

# Настраиваем логирование
logger = logging.getLogger(__name__)

def load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False, **kwargs):
    """
    Загружает переменные из .env файла в os.environ.
    В production среде (Railway) все переменные уже заданы через UI,
    поэтому этот метод просто возвращает True.
    
    Args:
        dotenv_path: Путь к .env файлу
        stream: Объект с методом read() для чтения .env (не используется в fallback)
        verbose: Выводить ли отладочную информацию
        override: Перезаписывать ли существующие переменные
        
    Returns:
        bool: True, если загрузка успешна (в fallback всегда True)
    """
    if verbose:
        print("[dotenv_fallback] Using fallback implementation of load_dotenv")
    
    # Если находимся в production среде (Railway), ничего не делаем
    # т.к. переменные уже заданы через UI
    if is_production_environment():
        if verbose:
            print("[dotenv_fallback] Running in production environment, skipping .env loading")
        return True
    
    # Если файл не указан, пытаемся найти его
    if dotenv_path is None:
        dotenv_path = find_dotenv()
        if not dotenv_path:
            if verbose:
                print("[dotenv_fallback] No .env file found")
            return True
    
    # Загружаем переменные из файла
    try:
        with open(dotenv_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                
                # Разбираем строку формата KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Удаляем кавычки, если они есть
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Устанавливаем переменную окружения
                    if key and (override or key not in os.environ):
                        os.environ[key] = value
                        if verbose:
                            print(f"[dotenv_fallback] Set environment variable: {key}")
        
        if verbose:
            print(f"[dotenv_fallback] Loaded environment variables from {dotenv_path}")
        return True
    except Exception as e:
        if verbose:
            print(f"[dotenv_fallback] Error loading .env file: {e}")
        return False

def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False):
    """
    Ищет .env файл в текущей директории и вверх по иерархии.
    
    Args:
        filename: Имя .env файла для поиска
        raise_error_if_not_found: Вызывать ли ошибку, если файл не найден
        usecwd: Использовать ли текущую рабочую директорию вместо директории скрипта
        
    Returns:
        str: Путь к найденному .env файлу или пустая строка
    """
    # Сначала проверяем текущую директорию
    if os.path.isfile(filename):
        return os.path.abspath(filename)
    
    # Определяем начальную директорию для поиска
    if usecwd:
        start_dir = os.getcwd()
    else:
        start_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Ищем файл, поднимаясь по дереву директорий
    current_dir = start_dir
    while True:
        dotenv_path = os.path.join(current_dir, filename)
        if os.path.isfile(dotenv_path):
            return dotenv_path
        
        # Поднимаемся на уровень выше
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Достигли корня файловой системы
            break
        current_dir = parent_dir
    
    # Файл не найден
    if raise_error_if_not_found:
        raise IOError(f"File {filename} not found")
    return ""

def is_production_environment():
    """
    Проверяет, запущен ли скрипт в production среде (Railway).
    
    Returns:
        bool: True, если запущен в production среде
    """
    return os.environ.get("RAILWAY_ENVIRONMENT") == "production" or \
           os.environ.get("RAILWAY_STATIC_URL") is not None or \
           os.environ.get("RAILWAY") is not None

# Эта функция нужна для совместимости с python-dotenv
def set_key(dotenv_path, key_to_set, value_to_set, quote_mode="always"):
    """
    Устанавливает значение переменной в .env файле.
    В fallback версии просто выводит предупреждение.
    
    Args:
        dotenv_path: Путь к .env файлу
        key_to_set: Ключ для установки
        value_to_set: Значение для установки
        quote_mode: Режим кавычек ("always", "auto" или "never")
        
    Returns:
        bool: True, если установка успешна (в fallback всегда False)
    """
    print("[dotenv_fallback] set_key() is not implemented in fallback version")
    return False

# Для совместимости с python-dotenv
get_key = set_key
unset_key = set_key

# Выводим предупреждение при импорте
print("[WARNING] Using dotenv_fallback.py instead of python-dotenv. Some functionality may be limited.") 