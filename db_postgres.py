import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import shutil

# Настройка логирования
logger = logging.getLogger(__name__)

# Определяем путь к базе данных и тип базы данных в зависимости от окружения
if os.getenv("DATABASE_URL"):
    # Мы на Railway или другом хостинге с PostgreSQL
    DB_PATH = os.getenv("DATABASE_URL")
    USE_POSTGRES = True
    logger.info(f"Используется PostgreSQL: {DB_PATH}")
else:
    # Локальная разработка с SQLite
    DB_DIR = os.path.join(os.getcwd(), "data")
    DB_PATH = os.path.join(DB_DIR, "database.db")
    os.makedirs(DB_DIR, exist_ok=True)
    USE_POSTGRES = False
    logger.info(f"Используется SQLite: {DB_PATH}")

# SQL для создания таблиц в SQLite
SQLITE_CREATE_TABLES_SQL = """
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

# SQL для создания таблиц в PostgreSQL
POSTGRES_CREATE_TABLES_SQL = """
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE,
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
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица напоминаний
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    cron TEXT NOT NULL,
    message TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
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
        self._use_postgres = USE_POSTGRES
        
        if self._use_postgres:
            try:
                # Импортируем библиотеки для PostgreSQL только если они нужны
                import psycopg2
                import psycopg2.extras
                
                logger.info(f"Инициализация PostgreSQL по адресу: {self._db_path}")
                self._postgres_connection = None
                self._create_postgres_tables()
            except ImportError:
                logger.error("Ошибка импорта psycopg2. Установите пакет: pip install psycopg2-binary")
                raise
            except Exception as e:
                logger.error(f"Ошибка при инициализации PostgreSQL: {e}")
                raise
        else:
            try:
                import sqlite3
                
                logger.info(f"Инициализация SQLite по пути: {self._db_path}")
                
                # Проверяем, существует ли директория для БД
                if not os.path.exists(DB_DIR):
                    os.makedirs(DB_DIR)
                    logger.info(f"Создана директория для базы данных: {DB_DIR}")
                
                # Создаем соединение и таблицы
                self._create_sqlite_tables()
                
                logger.info("База данных SQLite успешно инициализирована")
            except ImportError:
                logger.error("Ошибка импорта sqlite3")
                raise
            except Exception as e:
                logger.error(f"Ошибка при инициализации SQLite: {e}")
                raise
    
    def _get_sqlite_connection(self):
        """Получение соединения с SQLite"""
        import sqlite3
        return sqlite3.connect(self._db_path)
    
    def _get_postgres_connection(self):
        """Получение соединения с PostgreSQL"""
        import psycopg2
        import psycopg2.extras
        
        if self._postgres_connection is None or self._postgres_connection.closed:
            self._postgres_connection = psycopg2.connect(self._db_path)
            self._postgres_connection.autocommit = False
        
        return self._postgres_connection
    
    def _create_sqlite_tables(self):
        """Создание таблиц в SQLite"""
        import sqlite3
        
        with self._get_sqlite_connection() as conn:
            conn.executescript(SQLITE_CREATE_TABLES_SQL)
    
    def _create_postgres_tables(self):
        """Создание таблиц в PostgreSQL"""
        import psycopg2
        
        conn = self._get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(POSTGRES_CREATE_TABLES_SQL)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при создании таблиц в PostgreSQL: {e}")
            raise
    
    async def execute(self, query: str, params: tuple = ()) -> None:
        """
        Асинхронное выполнение SQL-запроса без возврата результатов.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
        """
        async with self._lock:
            try:
                if self._use_postgres:
                    conn = self._get_postgres_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(query, params)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise e
                else:
                    with self._get_sqlite_connection() as conn:
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
                if self._use_postgres:
                    conn = self._get_postgres_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.executemany(query, params_list)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise e
                else:
                    with self._get_sqlite_connection() as conn:
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
                if self._use_postgres:
                    conn = self._get_postgres_connection()
                    with conn.cursor() as cursor:
                        cursor.execute(query, params)
                        return cursor.fetchone()
                else:
                    with self._get_sqlite_connection() as conn:
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
                if self._use_postgres:
                    conn = self._get_postgres_connection()
                    with conn.cursor() as cursor:
                        cursor.execute(query, params)
                        return cursor.fetchall()
                else:
                    with self._get_sqlite_connection() as conn:
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
                if self._use_postgres:
                    import psycopg2.extras
                    conn = self._get_postgres_connection()
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                        cursor.execute(query, params)
                        row = cursor.fetchone()
                        return dict(row) if row else None
                else:
                    import sqlite3
                    with self._get_sqlite_connection() as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute(query, params)
                        row = cursor.fetchone()
                        return dict(row) if row else None
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
                if self._use_postgres:
                    import psycopg2.extras
                    conn = self._get_postgres_connection()
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                        cursor.execute(query, params)
                        rows = cursor.fetchall()
                        return [dict(row) for row in rows]
                else:
                    import sqlite3
                    with self._get_sqlite_connection() as conn:
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
        user = await self.fetch_one("SELECT id FROM users WHERE tg_id = %s" if self._use_postgres else "SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        
        if user:
            # Обновляем данные пользователя, если он существует
            if username or first_name or last_name:
                update_query = "UPDATE users SET "
                update_params = []
                
                if username:
                    update_query += "username = %s, " if self._use_postgres else "username = ?, "
                    update_params.append(username)
                
                if first_name:
                    update_query += "first_name = %s, " if self._use_postgres else "first_name = ?, "
                    update_params.append(first_name)
                
                if last_name:
                    update_query += "last_name = %s, " if self._use_postgres else "last_name = ?, "
                    update_params.append(last_name)
                
                # Удаляем последнюю запятую и пробел
                update_query = update_query.rstrip(", ")
                
                # Добавляем условие WHERE
                update_query += " WHERE tg_id = %s" if self._use_postgres else " WHERE tg_id = ?"
                update_params.append(tg_id)
                
                await self.execute(update_query, tuple(update_params))
            
            return user[0]
        else:
            # Создаем нового пользователя
            insert_query = "INSERT INTO users (tg_id, username, first_name, last_name) VALUES (%s, %s, %s, %s) RETURNING id" if self._use_postgres else "INSERT INTO users (tg_id, username, first_name, last_name) VALUES (?, ?, ?, ?)"
            
            if self._use_postgres:
                user = await self.fetch_one(insert_query, (tg_id, username, first_name, last_name))
                return user[0]
            else:
                await self.execute(insert_query, (tg_id, username, first_name, last_name))
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
        select_query = "SELECT 1 FROM answers WHERE id = %s AND q_code = %s" if self._use_postgres else "SELECT 1 FROM answers WHERE id = ? AND q_code = ?"
        existing = await self.fetch_one(select_query, (user_id, q_code))
        
        if existing:
            # Обновляем существующий ответ
            update_query = "UPDATE answers SET value = %s WHERE id = %s AND q_code = %s" if self._use_postgres else "UPDATE answers SET value = ? WHERE id = ? AND q_code = ?"
            await self.execute(update_query, (value, user_id, q_code))
        else:
            # Создаем новый ответ
            insert_query = "INSERT INTO answers (id, q_code, value) VALUES (%s, %s, %s)" if self._use_postgres else "INSERT INTO answers (id, q_code, value) VALUES (?, ?, ?)"
            await self.execute(insert_query, (user_id, q_code, value))
    
    async def get_answers(self, user_id: int) -> Dict[str, str]:
        """
        Получение всех ответов пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, str]: Словарь с ответами пользователя (ключ - код вопроса, значение - ответ)
        """
        select_query = "SELECT q_code, value FROM answers WHERE id = %s" if self._use_postgres else "SELECT q_code, value FROM answers WHERE id = ?"
        rows = await self.fetch_all(select_query, (user_id,))
        
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
        
        if self._use_postgres:
            # Сохраняем профиль в PostgreSQL
            insert_query = "INSERT INTO profiles (user_id, data) VALUES (%s, %s) RETURNING id"
            profile = await self.fetch_one(insert_query, (user_id, profile_json))
            return profile[0]
        else:
            # Сохраняем профиль в SQLite
            insert_query = "INSERT INTO profiles (user_id, data) VALUES (?, ?)"
            await self.execute(insert_query, (user_id, profile_json))
            
            # Получаем ID созданного профиля
            select_query = "SELECT id FROM profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1"
            profile = await self.fetch_one(select_query, (user_id,))
            return profile[0]
    
    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение последнего профиля пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные профиля или None, если профиль не найден
        """
        select_query = "SELECT data FROM profiles WHERE user_id = %s ORDER BY created_at DESC LIMIT 1" if self._use_postgres else "SELECT data FROM profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1"
        profile = await self.fetch_one(select_query, (user_id,))
        
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
        if self._use_postgres:
            # Создаем напоминание в PostgreSQL
            insert_query = "INSERT INTO reminders (user_id, cron, message) VALUES (%s, %s, %s) RETURNING id"
            reminder = await self.fetch_one(insert_query, (user_id, cron, message))
            return reminder[0]
        else:
            # Создаем напоминание в SQLite
            insert_query = "INSERT INTO reminders (user_id, cron, message) VALUES (?, ?, ?)"
            await self.execute(insert_query, (user_id, cron, message))
            
            # Получаем ID созданного напоминания
            select_query = "SELECT id FROM reminders WHERE user_id = ? ORDER BY created_at DESC LIMIT 1"
            reminder = await self.fetch_one(select_query, (user_id,))
            return reminder[0]
    
    async def get_active_reminders(self) -> List[Dict[str, Any]]:
        """
        Получение всех активных напоминаний.
        
        Returns:
            List[Dict[str, Any]]: Список активных напоминаний
        """
        select_query = """
        SELECT r.id, r.user_id, r.cron, r.message, u.tg_id
        FROM reminders r
        JOIN users u ON r.user_id = u.id
        WHERE r.active = TRUE
        """ if self._use_postgres else """
        SELECT r.id, r.user_id, r.cron, r.message, u.tg_id
        FROM reminders r
        JOIN users u ON r.user_id = u.id
        WHERE r.active = 1
        """
        
        return await self.fetch_dict_all(select_query)
    
    async def deactivate_reminder(self, reminder_id: int) -> None:
        """
        Деактивация напоминания.
        
        Args:
            reminder_id: ID напоминания
        """
        update_query = "UPDATE reminders SET active = FALSE WHERE id = %s" if self._use_postgres else "UPDATE reminders SET active = 0 WHERE id = ?"
        await self.execute(update_query, (reminder_id,))
    
    async def backup_database(self) -> str:
        """
        Создание бэкапа базы данных.
        
        Returns:
            str: Путь к созданному бэкапу или сообщение об ошибке
        """
        if self._use_postgres:
            logger.info("Бэкап PostgreSQL не реализован в этой версии")
            return "Бэкап PostgreSQL не реализован в этой версии"
        else:
            try:
                # Создаем директорию для бэкапов
                backup_dir = os.path.join(DB_DIR, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                
                # Генерируем имя файла бэкапа с текущей датой и временем
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"database_{timestamp}.db")
                
                # Копируем файл базы данных
                shutil.copy2(DB_PATH, backup_path)
                logger.info(f"Создан бэкап базы данных: {backup_path}")
                
                # Очищаем старые бэкапы (оставляем только 5 последних)
                backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("database_")])
                if len(backup_files) > 5:
                    for old_backup in backup_files[:-5]:
                        os.remove(old_backup)
                        logger.info(f"Удален старый бэкап: {old_backup}")
                
                return backup_path
            except Exception as e:
                error_msg = f"Ошибка при создании бэкапа базы данных: {e}"
                logger.error(error_msg)
                return error_msg

# Создаем экземпляр базы данных для использования в других модулях
db = Database() 