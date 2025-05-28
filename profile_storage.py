import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Tuple

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

# Импортируем интерфейс для работы с Supabase
try:
    from db_supabase import (
        init_supabase, 
        get_supabase_client, 
        init_supabase_tables,
        save_user_profile_to_supabase,
        load_user_profile_from_supabase,
        delete_user_profile_from_supabase,
        list_all_profiles_from_supabase
    )
    SUPABASE_AVAILABLE = True
    logger.info("Модуль Supabase успешно импортирован")
    railway_print("Модуль Supabase успешно импортирован", "INFO")
except ImportError as e:
    SUPABASE_AVAILABLE = False
    logger.warning(f"Не удалось импортировать модуль Supabase: {e}")
    railway_print(f"Не удалось импортировать модуль Supabase: {e}", "WARNING")

# Определяем путь к файлу локального сохранения профилей
LOCAL_PROFILES_FILE = "user_profiles.json"

# Словарь для хранения профилей пользователей в памяти
user_profiles = {}

# Функция для инициализации хранилища данных
async def init_storage():
    """
    Инициализирует хранилище данных - Supabase или локальное.
    """
    global SUPABASE_AVAILABLE
    
    if SUPABASE_AVAILABLE:
        try:
            # Инициализируем Supabase
            client = init_supabase()
            if client is not None:
                await init_supabase_tables()
                logger.info("Хранилище Supabase успешно инициализировано")
                railway_print("Хранилище Supabase успешно инициализировано", "INFO")
            else:
                SUPABASE_AVAILABLE = False
                logger.warning("Не удалось инициализировать Supabase. Используем локальное хранилище.")
                railway_print("Не удалось инициализировать Supabase. Используем локальное хранилище.", "WARNING")
                await load_profiles_from_file()
        except Exception as e:
            SUPABASE_AVAILABLE = False
            logger.error(f"Ошибка при инициализации Supabase: {e}. Используем локальное хранилище.")
            railway_print(f"Ошибка при инициализации Supabase: {e}. Используем локальное хранилище.", "ERROR")
            await load_profiles_from_file()
    else:
        # Если Supabase недоступен, загружаем профили из локального файла
        logger.info("Supabase недоступен. Используем локальное хранилище.")
        railway_print("Supabase недоступен. Используем локальное хранилище.", "INFO")
        await load_profiles_from_file()

# Функция для сохранения профилей в локальный файл
async def save_profiles_to_file():
    """
    Сохраняет профили пользователей в локальный файл.
    """
    try:
        # Сначала пишем во временный файл
        temp_file = f"{LOCAL_PROFILES_FILE}.temp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(user_profiles, f, ensure_ascii=False, indent=4)
        
        # Создаем резервную копию существующего файла, если он существует
        if os.path.exists(LOCAL_PROFILES_FILE):
            backup_file = f"{LOCAL_PROFILES_FILE}.backup"
            try:
                import shutil
                shutil.copy2(LOCAL_PROFILES_FILE, backup_file)
            except Exception as backup_error:
                logger.warning(f"Не удалось создать резервную копию файла профилей: {backup_error}")
        
        # Переименовываем временный файл в основной
        import shutil
        shutil.move(temp_file, LOCAL_PROFILES_FILE)
        
        logger.info(f"Профили сохранены в локальный файл {LOCAL_PROFILES_FILE}")
        railway_print(f"Профили сохранены в локальный файл {LOCAL_PROFILES_FILE}", "INFO")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении профилей в локальный файл: {e}")
        railway_print(f"Ошибка при сохранении профилей в локальный файл: {e}", "ERROR")
        return False

# Функция для загрузки профилей из локального файла
async def load_profiles_from_file():
    """
    Загружает профили пользователей из локального файла.
    """
    global user_profiles
    try:
        if os.path.exists(LOCAL_PROFILES_FILE):
            # Проверяем размер файла
            file_size = os.path.getsize(LOCAL_PROFILES_FILE)
            if file_size == 0:
                logger.warning(f"Локальный файл профилей {LOCAL_PROFILES_FILE} пуст. Инициализируем пустой словарь профилей.")
                user_profiles = {}
                # Записываем пустой словарь в файл
                await save_profiles_to_file()
                return
                
            # Загружаем данные из файла
            with open(LOCAL_PROFILES_FILE, 'r', encoding='utf-8') as f:
                loaded_data = f.read().strip()
                if not loaded_data:  # Если файл пустой или содержит только пробелы
                    logger.warning(f"Локальный файл профилей {LOCAL_PROFILES_FILE} содержит только пробелы. Инициализируем пустой словарь профилей.")
                    user_profiles = {}
                    await save_profiles_to_file()
                    return
                    
                # Парсим JSON
                user_profiles = json.loads(loaded_data)
                logger.info(f"Загружено {len(user_profiles)} профилей из локального файла {LOCAL_PROFILES_FILE}")
                railway_print(f"Загружено {len(user_profiles)} профилей из локального файла {LOCAL_PROFILES_FILE}", "INFO")
        else:
            logger.info(f"Локальный файл профилей {LOCAL_PROFILES_FILE} не найден. Будет создан новый.")
            railway_print(f"Локальный файл профилей {LOCAL_PROFILES_FILE} не найден. Будет создан новый.", "INFO")
            user_profiles = {}
            # Создаем файл с пустым словарем
            await save_profiles_to_file()
    except json.JSONDecodeError as json_error:
        logger.error(f"Ошибка декодирования JSON при загрузке профилей из локального файла: {json_error}")
        railway_print(f"Ошибка декодирования JSON при загрузке профилей из локального файла: {json_error}", "ERROR")
        # Создаем резервную копию поврежденного файла
        if os.path.exists(LOCAL_PROFILES_FILE):
            import asyncio
            backup_file = f"{LOCAL_PROFILES_FILE}.backup.{int(asyncio.get_event_loop().time())}"
            try:
                import shutil
                shutil.copy2(LOCAL_PROFILES_FILE, backup_file)
                logger.info(f"Создана резервная копия поврежденного файла профилей: {backup_file}")
                railway_print(f"Создана резервная копия поврежденного файла профилей: {backup_file}", "INFO")
            except Exception as backup_error:
                logger.error(f"Не удалось создать резервную копию файла профилей: {backup_error}")
        
        # Инициализируем пустой словарь
        user_profiles = {}
        await save_profiles_to_file()
    except Exception as e:
        logger.error(f"Ошибка при загрузке профилей из локального файла: {e}")
        railway_print(f"Ошибка при загрузке профилей из локального файла: {e}", "ERROR")
        user_profiles = {}
        await save_profiles_to_file()

# Функция для сохранения профиля пользователя
async def save_user_profile(user_id: int, profile_data: Dict[str, Any]) -> bool:
    """
    Сохраняет профиль пользователя в хранилище (Supabase или локальный файл).
    
    Args:
        user_id: ID пользователя
        profile_data: Данные профиля пользователя
    
    Returns:
        bool: True, если сохранение прошло успешно, False в противном случае
    """
    try:
        # Преобразуем user_id в строку для соответствия структуре хранилища
        user_id_str = str(user_id)
        logger.info(f"Сохраняем профиль для пользователя с ID: {user_id_str}")
        
        # Сначала пытаемся сохранить в Supabase, если доступен
        if SUPABASE_AVAILABLE:
            try:
                success = await save_user_profile_to_supabase(user_id, profile_data)
                if success:
                    logger.info(f"Профиль пользователя {user_id} успешно сохранен в Supabase")
                    # Также сохраняем в локальную память для быстрого доступа
                    user_profiles[user_id_str] = profile_data
                    return True
                else:
                    logger.warning(f"Не удалось сохранить профиль в Supabase. Используем локальное хранилище.")
                    railway_print(f"Не удалось сохранить профиль в Supabase. Используем локальное хранилище.", "WARNING")
            except Exception as e:
                logger.error(f"Ошибка при сохранении профиля в Supabase: {e}. Используем локальное хранилище.")
                railway_print(f"Ошибка при сохранении профиля в Supabase: {e}. Используем локальное хранилище.", "ERROR")
        
        # Если Supabase недоступен или произошла ошибка, сохраняем локально
        user_profiles[user_id_str] = profile_data
        
        # Сохраняем обновленные профили в локальный файл
        saved = await save_profiles_to_file()
        if saved:
            logger.info(f"Профиль пользователя {user_id} сохранен успешно в локальное хранилище")
            return True
        else:
            logger.error(f"Ошибка при сохранении профиля пользователя {user_id} в локальный файл")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сохранении профиля пользователя {user_id}: {e}")
        return False

# Функция для загрузки профиля пользователя
async def load_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Загружает профиль пользователя из хранилища (Supabase или локальный файл).
    
    Args:
        user_id: ID пользователя
    
    Returns:
        Optional[Dict[str, Any]]: Данные профиля пользователя или None, если профиль не найден
    """
    try:
        # Преобразуем user_id в строку для соответствия структуре хранилища
        user_id_str = str(user_id)
        logger.info(f"Пытаемся загрузить профиль для user_id: {user_id_str}")
        
        # Сначала проверяем локальную память
        if user_id_str in user_profiles:
            logger.info(f"Профиль пользователя {user_id} найден в локальной памяти")
            return user_profiles[user_id_str]
        
        # Если не найден в памяти и доступен Supabase, загружаем оттуда
        if SUPABASE_AVAILABLE:
            try:
                profile_data = await load_user_profile_from_supabase(user_id)
                if profile_data:
                    logger.info(f"Профиль пользователя {user_id} загружен из Supabase")
                    # Сохраняем в локальную память для быстрого доступа
                    user_profiles[user_id_str] = profile_data
                    return profile_data
                else:
                    logger.info(f"Профиль пользователя {user_id} не найден в Supabase")
            except Exception as e:
                logger.error(f"Ошибка при загрузке профиля из Supabase: {e}")
                railway_print(f"Ошибка при загрузке профиля из Supabase: {e}", "ERROR")
        
        # Если профиль не найден нигде
        logger.info(f"Профиль пользователя {user_id} не найден")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке профиля пользователя {user_id}: {e}")
        return None

# Функция для удаления профиля пользователя
async def delete_user_profile(user_id: int) -> bool:
    """
    Удаляет профиль пользователя из хранилища (Supabase и локальный файл).
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True, если удаление прошло успешно, False в противном случае
    """
    try:
        # Преобразуем user_id в строку для соответствия структуре хранилища
        user_id_str = str(user_id)
        logger.info(f"Удаляем профиль для пользователя с ID: {user_id_str}")
        
        # Если доступен Supabase, удаляем оттуда
        if SUPABASE_AVAILABLE:
            try:
                success = await delete_user_profile_from_supabase(user_id)
                if not success:
                    logger.warning(f"Не удалось удалить профиль из Supabase")
                    railway_print(f"Не удалось удалить профиль из Supabase", "WARNING")
            except Exception as e:
                logger.error(f"Ошибка при удалении профиля из Supabase: {e}")
                railway_print(f"Ошибка при удалении профиля из Supabase: {e}", "ERROR")
        
        # Удаляем из локальной памяти
        if user_id_str in user_profiles:
            del user_profiles[user_id_str]
        
        # Сохраняем обновленные профили в локальный файл
        saved = await save_profiles_to_file()
        if saved:
            logger.info(f"Профиль пользователя {user_id} удален успешно")
            return True
        else:
            logger.error(f"Ошибка при сохранении обновленных профилей после удаления")
            return False
    except Exception as e:
        logger.error(f"Ошибка при удалении профиля пользователя {user_id}: {e}")
        return False

# Функция для получения списка всех профилей
async def list_all_profiles() -> List[Dict[str, Any]]:
    """
    Получает список всех профилей из хранилища.
    
    Returns:
        List[Dict[str, Any]]: Список всех профилей пользователей
    """
    try:
        # Если доступен Supabase, получаем список оттуда
        if SUPABASE_AVAILABLE:
            try:
                profiles = await list_all_profiles_from_supabase()
                if profiles:
                    logger.info(f"Получено {len(profiles)} профилей из Supabase")
                    # Обновляем локальную память
                    for profile in profiles:
                        user_profiles[profile["id"]] = profile["profile_data"]
                    return profiles
                else:
                    logger.info("Профили не найдены в Supabase")
            except Exception as e:
                logger.error(f"Ошибка при получении списка профилей из Supabase: {e}")
                railway_print(f"Ошибка при получении списка профилей из Supabase: {e}", "ERROR")
        
        # Возвращаем профили из локальной памяти
        profiles = []
        for user_id, profile_data in user_profiles.items():
            profiles.append({
                "id": user_id,
                "profile_data": profile_data
            })
        
        logger.info(f"Получено {len(profiles)} профилей из локального хранилища")
        return profiles
    except Exception as e:
        logger.error(f"Ошибка при получении списка профилей: {e}")
        return [] 