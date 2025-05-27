#!/usr/bin/env python
"""
Скрипт для создания файла .env из образца
Автоматически создает .env файл на основе sample.env, запрашивая необходимые значения
"""

import os
import sys
import shutil
from getpass import getpass

def create_env_file():
    """
    Создает файл .env на основе sample.env
    """
    print("===== Создание файла .env для бота =====")
    
    # Проверяем наличие sample.env
    if not os.path.exists("sample.env"):
        print("Ошибка: Файл sample.env не найден!")
        return False
    
    # Проверяем, существует ли уже файл .env
    if os.path.exists(".env"):
        overwrite = input("Файл .env уже существует. Перезаписать? (y/n): ").lower()
        if overwrite != 'y':
            print("Отменено. Файл .env оставлен без изменений.")
            return False
    
    # Создаем словарь для хранения значений переменных
    env_vars = {}
    
    # Запрашиваем обязательные значения
    env_vars["BOT_TOKEN"] = input("Введите токен бота (BOT_TOKEN): ").strip()
    if not env_vars["BOT_TOKEN"]:
        print("Ошибка: BOT_TOKEN обязателен для работы бота.")
        return False
    
    env_vars["OPENAI_API_KEY"] = input("Введите ключ API OpenAI (OPENAI_API_KEY) или оставьте пустым: ").strip()
    env_vars["ELEVEN_TOKEN"] = input("Введите токен ElevenLabs (ELEVEN_TOKEN) или оставьте пустым: ").strip()
    
    # Запрашиваем режим работы
    webhook_mode = input("Использовать webhook? (y/n, по умолчанию n): ").lower()
    env_vars["WEBHOOK_MODE"] = "true" if webhook_mode == 'y' else "false"
    
    # Если выбран режим webhook, запрашиваем дополнительные параметры
    if webhook_mode == 'y':
        env_vars["WEBHOOK_URL"] = input("Введите URL для webhook (пример: https://your-app.up.railway.app/webhook/{token}) или оставьте пустым для автоматической генерации: ").strip()
        if not env_vars["WEBHOOK_URL"]:
            env_vars["RAILWAY_PUBLIC_DOMAIN"] = input("Введите публичный домен Railway (пример: your-app.up.railway.app): ").strip()
    
    # Запрашиваем использование PostgreSQL
    use_postgres = input("Использовать PostgreSQL вместо SQLite? (y/n, по умолчанию n): ").lower()
    if use_postgres == 'y':
        env_vars["DATABASE_URL"] = input("Введите URL подключения к PostgreSQL: ").strip()
    
    # Запрашиваем дополнительные параметры
    admin_chat_id = input("Введите ID чата администратора для тестирования (ADMIN_CHAT_ID) или оставьте пустым: ").strip()
    if admin_chat_id:
        env_vars["ADMIN_CHAT_ID"] = admin_chat_id
    
    # Создаем файл .env
    with open("sample.env", "r", encoding="utf-8") as sample_file:
        sample_content = sample_file.read()
    
    # Заменяем значения в sample.env
    env_content = sample_content
    for key, value in env_vars.items():
        if value:  # Заменяем только если значение не пустое
            env_content = env_content.replace(f"{key}=", f"{key}={value}")
    
    # Записываем в .env
    with open(".env", "w", encoding="utf-8") as env_file:
        env_file.write(env_content)
    
    print("\nФайл .env успешно создан!")
    print("Обратите внимание, что некоторые переменные могут требовать дополнительной настройки.")
    print("Проверьте файл .env и при необходимости отредактируйте его вручную.")
    
    return True

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\nОтменено пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nОшибка при создании файла .env: {e}")
        sys.exit(1) 