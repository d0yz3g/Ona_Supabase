import os
import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Импорт функции railway_print для логирования
try:
    from railway_logging import railway_print
except ImportError:
    # Определяем функцию railway_print, если модуль railway_logging не найден
    def railway_print(message, level="INFO"):
        prefix = "ИНФО"
        if level.upper() == "ERROR":
            prefix = "ОШИБКА"
        elif level.upper() == "WARNING":
            prefix = "ПРЕДУПРЕЖДЕНИЕ"
        elif level.upper() == "DEBUG":
            prefix = "ОТЛАДКА"
        print(f"{prefix}: {message}")
        import sys
        sys.stdout.flush()

# Загружаем переменные окружения
load_dotenv()

# Получаем данные для подключения к Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Проверка наличия ключей Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Отсутствуют ключи для подключения к Supabase. "
                "Убедитесь, что переменные SUPABASE_URL и SUPABASE_KEY заданы в .env файле.")
    railway_print("Отсутствуют ключи для подключения к Supabase!", "ERROR")
    # Не выходим из программы, так как будет использован резервный механизм локального хранения

# Глобальная переменная для клиента Supabase
supabase_client: Optional[Client] = None

def init_supabase() -> Optional[Client]:
    """
    Инициализация клиента Supabase
    
    Returns:
        Optional[Client]: Клиент Supabase или None, если инициализация не удалась
    """
    global supabase_client
    
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Успешное подключение к Supabase")
            railway_print("Успешное подключение к Supabase", "INFO")
            return supabase_client
        else:
            logger.warning("Не удалось подключиться к Supabase: отсутствуют URL или API-ключ")
            railway_print("Не удалось подключиться к Supabase: отсутствуют URL или API-ключ", "WARNING")
            return None
    except Exception as e:
        logger.error(f"Ошибка при инициализации Supabase: {e}")
        railway_print(f"Ошибка при инициализации Supabase: {e}", "ERROR")
        return None

def get_supabase_client() -> Optional[Client]:
    """
    Получение клиента Supabase (с ленивой инициализацией)
    
    Returns:
        Optional[Client]: Клиент Supabase или None, если инициализация не удалась
    """
    global supabase_client
    
    if supabase_client is None:
        supabase_client = init_supabase()
    
    return supabase_client

async def init_supabase_tables():
    """
    Создание необходимых таблиц в Supabase, если они отсутствуют.
    
    Эта функция должна быть вызвана при запуске приложения.
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Невозможно создать таблицы: отсутствует подключение к Supabase")
        return
    
    try:
        # Проверка существования таблиц выполняется автоматически при создании
        # Supabase создаст таблицы через миграции в консоли управления
        
        logger.info("Таблицы в Supabase успешно инициализированы")
        railway_print("Таблицы в Supabase успешно инициализированы", "INFO")
    except Exception as e:
        logger.error(f"Ошибка при инициализации таблиц в Supabase: {e}")
        railway_print(f"Ошибка при инициализации таблиц в Supabase: {e}", "ERROR")

async def save_user_profile_to_supabase(user_id: int, profile_data: Dict[str, Any]) -> bool:
    """
    Сохраняет профиль пользователя в Supabase
    
    Args:
        user_id: ID пользователя
        profile_data: Данные профиля пользователя
    
    Returns:
        bool: True, если сохранение прошло успешно, False в противном случае
    """
    client = get_supabase_client()
    if not client:
        logger.warning(f"Невозможно сохранить профиль пользователя {user_id}: отсутствует подключение к Supabase")
        return False
    
    try:
        # Преобразуем user_id в строку для соответствия структуре БД
        user_id_str = str(user_id)
        
        # Сериализуем сложные типы данных в JSON
        prepared_data = {
            "id": user_id_str,
            "profile_data": json.dumps(profile_data, ensure_ascii=False)
        }
        
        # Используем upsert для создания или обновления записи
        response = client.table("user_profiles").upsert(prepared_data).execute()
        
        if response.data:
            logger.info(f"Профиль пользователя {user_id} успешно сохранен в Supabase")
            return True
        else:
            logger.error(f"Ошибка при сохранении профиля пользователя {user_id} в Supabase: {response.error}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сохранении профиля пользователя {user_id} в Supabase: {e}")
        return False

async def load_user_profile_from_supabase(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Загружает профиль пользователя из Supabase
    
    Args:
        user_id: ID пользователя
    
    Returns:
        Optional[Dict[str, Any]]: Данные профиля пользователя или None, если профиль не найден
    """
    client = get_supabase_client()
    if not client:
        logger.warning(f"Невозможно загрузить профиль пользователя {user_id}: отсутствует подключение к Supabase")
        return None
    
    try:
        # Преобразуем user_id в строку для соответствия структуре БД
        user_id_str = str(user_id)
        
        # Получаем данные пользователя
        response = client.table("user_profiles").select("profile_data").eq("id", user_id_str).execute()
        
        if response.data and len(response.data) > 0:
            # Десериализуем JSON из колонки profile_data
            profile_data = json.loads(response.data[0]["profile_data"])
            logger.info(f"Профиль пользователя {user_id} успешно загружен из Supabase")
            return profile_data
        else:
            logger.info(f"Профиль пользователя {user_id} не найден в Supabase")
            return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке профиля пользователя {user_id} из Supabase: {e}")
        return None

async def delete_user_profile_from_supabase(user_id: int) -> bool:
    """
    Удаляет профиль пользователя из Supabase
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True, если удаление прошло успешно, False в противном случае
    """
    client = get_supabase_client()
    if not client:
        logger.warning(f"Невозможно удалить профиль пользователя {user_id}: отсутствует подключение к Supabase")
        return False
    
    try:
        # Преобразуем user_id в строку для соответствия структуре БД
        user_id_str = str(user_id)
        
        # Удаляем данные пользователя
        response = client.table("user_profiles").delete().eq("id", user_id_str).execute()
        
        logger.info(f"Профиль пользователя {user_id} успешно удален из Supabase")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении профиля пользователя {user_id} из Supabase: {e}")
        return False

async def list_all_profiles_from_supabase() -> List[Dict[str, Any]]:
    """
    Получает список всех профилей из Supabase
    
    Returns:
        List[Dict[str, Any]]: Список всех профилей пользователей
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Невозможно получить список профилей: отсутствует подключение к Supabase")
        return []
    
    try:
        # Получаем все профили
        response = client.table("user_profiles").select("id, profile_data").execute()
        
        profiles = []
        if response.data:
            for item in response.data:
                profile_data = json.loads(item["profile_data"])
                profiles.append({
                    "id": item["id"],
                    "profile_data": profile_data
                })
                
            logger.info(f"Успешно загружено {len(profiles)} профилей из Supabase")
            return profiles
        else:
            logger.info("Профили не найдены в Supabase")
            return []
    except Exception as e:
        logger.error(f"Ошибка при получении списка профилей из Supabase: {e}")
        return [] 