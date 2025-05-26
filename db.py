import os
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)

# Путь к директории с базой данных
DB_DIR = os.path.join(os.getcwd(), "data")
DB_PATH = os.path.join(DB_DIR, "database.db")

# Создаем директорию для БД, если она не существует
os.makedirs(DB_DIR, exist_ok=True)

# SQL для создания таблиц
CREATE_TABLES_SQL = """
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    tg_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ответов на вопросы
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER,
    q_code TEXT,
    value TEXT,
    PRIMARY KEY(id, q_code),
    FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица профилей
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица напоминаний
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    cron TEXT NOT NULL,
    message TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

class Database:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance
    
    def _initialize_db(self):
        """Инициализация БД и создание таблиц, если они не существуют"""
        self._db_path = DB_PATH
        logger.info(f"Инициализация базы данных по пути: {self._db_path}")
        
        try:
            # Проверяем, существует ли директория для БД
            if not os.path.exists(DB_DIR):
                os.makedirs(DB_DIR)
                logger.info(f"Создана директория для базы данных: {DB_DIR}")
            
            # Создаем соединение и таблицы
            with self._get_connection() as conn:
                conn.executescript(CREATE_TABLES_SQL)
            
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
    
    def _get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self._db_path)
    
    async def execute(self, query: str, params: tuple = ()) -> None:
        """
        Асинхронное выполнение SQL-запроса без возврата результатов.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(query, params)
                    conn.commit()
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL-запроса: {e}\nЗапрос: {query}\nПараметры: {params}")
                raise
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Асинхронное выполнение SQL-запроса с множеством наборов параметров.
        
        Args:
            query: SQL-запрос
            params_list: Список наборов параметров
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.executemany(query, params_list)
                    conn.commit()
            except Exception as e:
                logger.error(f"Ошибка при выполнении множественного SQL-запроса: {e}\nЗапрос: {query}")
                raise
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """
        Асинхронное получение одной записи по SQL-запросу.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Optional[tuple]: Результат запроса или None, если запись не найдена
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return cursor.fetchone()
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL-запроса fetch_one: {e}\nЗапрос: {query}\nПараметры: {params}")
                raise
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """
        Асинхронное получение всех записей по SQL-запросу.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            List[tuple]: Список результатов запроса
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return cursor.fetchall()
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL-запроса fetch_all: {e}\nЗапрос: {query}\nПараметры: {params}")
                raise
    
    async def fetch_dict(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Асинхронное получение одной записи в виде словаря.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Optional[Dict[str, Any]]: Результат запроса в виде словаря или None
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    return None
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL-запроса fetch_dict: {e}\nЗапрос: {query}\nПараметры: {params}")
                raise
    
    async def fetch_dict_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Асинхронное получение всех записей в виде списка словарей.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            List[Dict[str, Any]]: Список результатов запроса в виде словарей
        """
        async with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL-запроса fetch_dict_all: {e}\nЗапрос: {query}\nПараметры: {params}")
                raise
    
    async def get_or_create_user(self, tg_id: int, username: str = None, first_name: str = None, last_name: str = None) -> int:
        """
        Получение или создание пользователя по Telegram ID.
        
        Args:
            tg_id: Telegram ID пользователя
            username: Имя пользователя (опционально)
            first_name: Имя (опционально)
            last_name: Фамилия (опционально)
            
        Returns:
            int: ID пользователя в базе данных
        """
        # Проверяем, существует ли пользователь
        user = await self.fetch_one("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        
        if user:
            # Обновляем данные пользователя, если он существует
            if username or first_name or last_name:
                update_query = "UPDATE users SET "
                update_params = []
                
                if username:
                    update_query += "username = ?, "
                    update_params.append(username)
                
                if first_name:
                    update_query += "first_name = ?, "
                    update_params.append(first_name)
                
                if last_name:
                    update_query += "last_name = ?, "
                    update_params.append(last_name)
                
                # Удаляем последнюю запятую и пробел
                update_query = update_query.rstrip(", ")
                
                # Добавляем условие WHERE
                update_query += " WHERE tg_id = ?"
                update_params.append(tg_id)
                
                await self.execute(update_query, tuple(update_params))
            
            return user[0]
        else:
            # Создаем нового пользователя
            await self.execute(
                "INSERT INTO users (tg_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (tg_id, username, first_name, last_name)
            )
            
            # Получаем ID созданного пользователя
            user = await self.fetch_one("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
            return user[0]
    
    async def save_answer(self, user_id: int, q_code: str, value: str) -> None:
        """
        Сохранение ответа пользователя на вопрос.
        
        Args:
            user_id: ID пользователя
            q_code: Код вопроса
            value: Ответ пользователя
        """
        # Проверяем, существует ли ответ
        existing = await self.fetch_one(
            "SELECT 1 FROM answers WHERE id = ? AND q_code = ?",
            (user_id, q_code)
        )
        
        if existing:
            # Обновляем существующий ответ
            await self.execute(
                "UPDATE answers SET value = ? WHERE id = ? AND q_code = ?",
                (value, user_id, q_code)
            )
        else:
            # Создаем новый ответ
            await self.execute(
                "INSERT INTO answers (id, q_code, value) VALUES (?, ?, ?)",
                (user_id, q_code, value)
            )
    
    async def get_answers(self, user_id: int) -> Dict[str, str]:
        """
        Получение всех ответов пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, str]: Словарь с ответами пользователя (ключ - код вопроса, значение - ответ)
        """
        rows = await self.fetch_all(
            "SELECT q_code, value FROM answers WHERE id = ?",
            (user_id,)
        )
        
        return {row[0]: row[1] for row in rows}
    
    async def save_profile(self, user_id: int, profile_data: Dict[str, Any]) -> int:
        """
        Сохранение профиля пользователя.
        
        Args:
            user_id: ID пользователя
            profile_data: Данные профиля
            
        Returns:
            int: ID созданного профиля
        """
        # Преобразуем данные в JSON
        profile_json = json.dumps(profile_data, ensure_ascii=False)
        
        # Сохраняем профиль
        await self.execute(
            "INSERT INTO profiles (user_id, data) VALUES (?, ?)",
            (user_id, profile_json)
        )
        
        # Получаем ID созданного профиля
        profile = await self.fetch_one(
            "SELECT id FROM profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        
        return profile[0]
    
    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение последнего профиля пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные профиля или None, если профиль не найден
        """
        profile = await self.fetch_one(
            "SELECT data FROM profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        
        if profile:
            try:
                return json.loads(profile[0])
            except json.JSONDecodeError:
                logger.error(f"Ошибка при декодировании JSON для профиля пользователя {user_id}")
                return None
        
        return None
    
    async def create_reminder(self, user_id: int, cron: str, message: str) -> int:
        """
        Создание напоминания для пользователя.
        
        Args:
            user_id: ID пользователя
            cron: Cron-выражение для расписания
            message: Текст напоминания
            
        Returns:
            int: ID созданного напоминания
        """
        await self.execute(
            "INSERT INTO reminders (user_id, cron, message) VALUES (?, ?, ?)",
            (user_id, cron, message)
        )
        
        # Получаем ID созданного напоминания
        reminder = await self.fetch_one(
            "SELECT id FROM reminders WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        
        return reminder[0]
    
    async def get_active_reminders(self) -> List[Dict[str, Any]]:
        """
        Получение всех активных напоминаний.
        
        Returns:
            List[Dict[str, Any]]: Список активных напоминаний
        """
        return await self.fetch_dict_all(
            """
            SELECT r.id, r.user_id, r.cron, r.message, u.tg_id
            FROM reminders r
            JOIN users u ON r.user_id = u.id
            WHERE r.active = 1
            """
        )
    
    async def deactivate_reminder(self, reminder_id: int) -> None:
        """
        Деактивация напоминания.
        
        Args:
            reminder_id: ID напоминания
        """
        await self.execute(
            "UPDATE reminders SET active = 0 WHERE id = ?",
            (reminder_id,)
        )

# Создаем экземпляр базы данных для использования в других модулях
db = Database() 