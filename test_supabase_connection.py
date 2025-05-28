#!/usr/bin/env python
"""
Тестирование подключения к Supabase.
Этот скрипт проверяет, что библиотека Supabase успешно импортируется
и может установить соединение с сервером Supabase.
"""

import os
import sys
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


def test_supabase_import():
    """Проверка импорта библиотеки Supabase и ее зависимостей."""
    try:
        import supabase
        print("✅ Библиотека supabase успешно импортирована.")
        
        # Выводим версию библиотеки
        print(f"Версия supabase: {supabase.__version__}")
        
        # Проверяем зависимости
        try:
            from supabase import create_client, Client
            print("✅ Импортирован create_client и Client из supabase")
        except ImportError as e:
            print(f"❌ Ошибка импорта из supabase: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта supabase: {e}")
        return False


def test_supabase_connection():
    """Тестирование подключения к Supabase."""
    try:
        from supabase import create_client, Client
        
        # Получаем URL и ключ из переменных окружения
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
        
        # Вывод для отладки
        print(f"SUPABASE_URL в окружении: {'Да' if supabase_url else 'Нет'}")
        print(f"SUPABASE_KEY в окружении: {'Да' if supabase_key else 'Нет'}")
        
        if not supabase_url or not supabase_key:
            print("⚠️ Переменные окружения SUPABASE_URL и/или SUPABASE_KEY не установлены.")
            print("⚠️ Тест подключения пропущен.")
            return None
        
        # Создаем клиент Supabase
        print(f"Подключение к Supabase URL: {supabase_url[:20]}...")
        supabase_client = create_client(supabase_url, supabase_key)
        
        # Выполняем простой запрос для проверки подключения
        try:
            # Проверка аутентификации - получение текущего пользователя
            # Может вернуть None, если пользователь не аутентифицирован, но не должен вызывать ошибку
            auth_response = supabase_client.auth.get_user()
            print("✅ Проверка аутентификации прошла успешно.")
            
            # Попытка выполнить простой запрос к БД
            # Заменить "users" на реальную таблицу в вашей базе данных
            try:
                # Просто получаем количество записей
                query_response = supabase_client.table("users").select("count", count="exact").execute()
                print(f"✅ Запрос к БД выполнен успешно. Получено записей: {query_response.count if hasattr(query_response, 'count') else 'N/A'}")
            except Exception as e:
                print(f"⚠️ Запрос к БД не удался: {e}")
                print("⚠️ Это может быть нормально, если таблица не существует или нет доступа.")
            
            print("✅ Соединение с Supabase установлено успешно.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при тестировании Supabase: {e}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при создании клиента Supabase: {e}")
        return False


if __name__ == "__main__":
    print("\n=== Тестирование Supabase ===\n")
    
    # Проверка импорта
    import_success = test_supabase_import()
    if not import_success:
        print("\n❌ Тест импорта Supabase не пройден. Выход.")
        sys.exit(1)
    
    # Проверка переменных окружения
    print("\nПеременные окружения:")
    for var in ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY"]:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: установлена")
        else:
            print(f"❌ {var}: не установлена")
    
    # Проверка подключения
    print("\n--- Тестирование подключения ---\n")
    connection_success = test_supabase_connection()
    
    if connection_success is None:
        print("\n⚠️ Тест подключения пропущен из-за отсутствия переменных окружения.")
        print("⚠️ Установите SUPABASE_URL и SUPABASE_KEY для полного тестирования.")
        sys.exit(0)
    elif connection_success:
        print("\n✅ Все тесты Supabase пройдены успешно!")
        sys.exit(0)
    else:
        print("\n❌ Тесты Supabase не пройдены. Проверьте настройки и соединение.")
        sys.exit(1) 