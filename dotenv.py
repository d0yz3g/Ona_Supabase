"""
Прямая замена для модуля python-dotenv.
Этот файл будет импортирован, если модуль python-dotenv не установлен.
"""
import os
import sys

def load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False, **kwargs):
    """
    Загружает переменные из .env файла в os.environ.
    В production среде (Railway) все переменные уже заданы через UI,
    поэтому этот метод просто возвращает True.
    """
    print("[dotenv.py] Using built-in replacement for python-dotenv")
    # В production среде (Railway) ничего не делаем
    return True

def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False):
    """
    Ищет .env файл в текущей директории.
    """
    if os.path.isfile(filename):
        return os.path.abspath(filename)
    return ""

# Выводим сообщение при импорте
print("[INFO] Using built-in replacement for python-dotenv module") 