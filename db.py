import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

# Настройка логирования
logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с SQLite базой данных."""
    
    def __init__(self, db_path: str = "ona_bot.db"):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_path: Путь к файлу базы данных.
        """
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Получение соединения с базой данных.
        
        Returns:
            sqlite3.Connection: Объект соединения с базой данных.
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            # Настройка соединения для получения результатов в виде словарей
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self) -> None:
        """Инициализация схемы базы данных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Создание таблиц, если они не существуют
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            answer_text TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id, question_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            summary_json TEXT,
            natal_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            text TEXT,
            is_sent BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        logger.info("База данных инициализирована")
    
    # Функции для работы с пользователями
    
    def add_user(self, tg_id: int, full_name: Optional[str] = None) -> int:
        """
        Добавление нового пользователя или получение существующего.
        
        Args:
            tg_id: Telegram ID пользователя.
            full_name: Полное имя пользователя.
            
        Returns:
            int: ID пользователя в базе данных.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверка существования пользователя
        cursor.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            user_id = existing_user[0]
            # Обновляем имя, если оно предоставлено
            if full_name:
                cursor.execute(
                    "UPDATE users SET full_name = ? WHERE id = ?",
                    (full_name, user_id)
                )
                conn.commit()
            return user_id
        
        # Добавление нового пользователя
        cursor.execute(
            "INSERT INTO users (tg_id, full_name) VALUES (?, ?)",
            (tg_id, full_name)
        )
        conn.commit()
        
        # Получение ID нового пользователя
        user_id = cursor.lastrowid
        logger.info(f"Добавлен новый пользователь с ID {user_id} (tg_id: {tg_id})")
        return user_id
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            Optional[Dict]: Данные пользователя или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        
        return None
    
    def get_user_by_tg_id(self, tg_id: int) -> Optional[Dict]:
        """
        Получение пользователя по Telegram ID.
        
        Args:
            tg_id: Telegram ID пользователя.
            
        Returns:
            Optional[Dict]: Данные пользователя или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        
        return None
    
    def get_all_users(self) -> List[Dict]:
        """
        Получение всех пользователей.
        
        Returns:
            List[Dict]: Список всех пользователей.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        return [dict(user) for user in users]
    
    # Функции для работы с ответами
    
    def add_answer(self, user_id: int, question_id: str, answer_text: str) -> int:
        """
        Добавление ответа пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            question_id: ID вопроса.
            answer_text: Текст ответа.
            
        Returns:
            int: ID ответа в базе данных.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO answers (user_id, question_id, answer_text)
                VALUES (?, ?, ?)
                ON CONFLICT (user_id, question_id) 
                DO UPDATE SET answer_text = ?
                """,
                (user_id, question_id, answer_text, answer_text)
            )
            conn.commit()
            
            # Получение ID ответа
            cursor.execute(
                "SELECT id FROM answers WHERE user_id = ? AND question_id = ?",
                (user_id, question_id)
            )
            answer = cursor.fetchone()
            logger.info(f"Сохранен ответ на вопрос {question_id} для пользователя {user_id}")
            return answer[0]
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении ответа: {e}")
            conn.rollback()
            raise
    
    def get_answer(self, user_id: int, question_id: str) -> Optional[Dict]:
        """
        Получение ответа пользователя на конкретный вопрос.
        
        Args:
            user_id: ID пользователя в базе данных.
            question_id: ID вопроса.
            
        Returns:
            Optional[Dict]: Данные ответа или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM answers WHERE user_id = ? AND question_id = ?",
            (user_id, question_id)
        )
        answer = cursor.fetchone()
        
        if answer:
            return dict(answer)
        
        return None
    
    def get_answers_by_user_id(self, user_id: int) -> List[Dict]:
        """
        Получение всех ответов пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            List[Dict]: Список ответов пользователя.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM answers WHERE user_id = ?", (user_id,))
        answers = cursor.fetchall()
        
        return [dict(answer) for answer in answers]
    
    def delete_answers_by_user_id(self, user_id: int) -> bool:
        """
        Удаление всех ответов пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            bool: True, если удаление выполнено успешно, иначе False.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM answers WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Удалены все ответы пользователя {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении ответов: {e}")
            conn.rollback()
            return False
    
    # Функции для работы с профилями
    
    def add_profile(self, user_id: int, summary_json: Dict = None, natal_json: Dict = None) -> int:
        """
        Добавление профиля пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            summary_json: Данные сводки профиля.
            natal_json: Данные натальной карты.
            
        Returns:
            int: ID профиля в базе данных.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        summary = json.dumps(summary_json) if summary_json else None
        natal = json.dumps(natal_json) if natal_json else None
        
        try:
            cursor.execute(
                """
                INSERT INTO profiles (user_id, summary_json, natal_json)
                VALUES (?, ?, ?)
                ON CONFLICT (user_id) 
                DO UPDATE SET summary_json = ?, natal_json = ?, created_at = CURRENT_TIMESTAMP
                """,
                (user_id, summary, natal, summary, natal)
            )
            conn.commit()
            
            # Получение ID профиля
            cursor.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
            profile = cursor.fetchone()
            logger.info(f"Создан/обновлен профиль для пользователя {user_id}")
            return profile[0]
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении профиля: {e}")
            conn.rollback()
            raise
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        """
        Получение профиля пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            Optional[Dict]: Данные профиля пользователя или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        profile_row = cursor.fetchone()
        
        if not profile_row:
            return None
            
        profile = dict(profile_row)
        
        # Преобразование JSON-строк в словари
        if profile['summary_json']:
            profile['summary_json'] = json.loads(profile['summary_json'])
        
        if profile['natal_json']:
            profile['natal_json'] = json.loads(profile['natal_json'])
        
        return profile
    
    def update_profile_natal(self, user_id: int, natal_data: Dict) -> bool:
        """
        Обновление данных натальной карты в профиле пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            natal_data: Данные натальной карты.
            
        Returns:
            bool: True, если обновление выполнено успешно, иначе False.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверка наличия профиля
            cursor.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
            profile = cursor.fetchone()
            
            if not profile:
                # Профиль не существует, создаем новый с natal_json
                self.add_profile(user_id, None, natal_data)
                return True
            
            # Профиль существует, обновляем только natal_json
            natal_json = json.dumps(natal_data)
            cursor.execute(
                "UPDATE profiles SET natal_json = ? WHERE user_id = ?",
                (natal_json, user_id)
            )
            conn.commit()
            
            logger.info(f"Обновлены данные натальной карты для пользователя {user_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении данных натальной карты: {e}")
            conn.rollback()
            return False
    
    def update_profile_summary(self, user_id: int, summary_data: Dict) -> bool:
        """
        Обновление данных психологического профиля пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            summary_data: Данные психологического профиля.
            
        Returns:
            bool: True, если обновление выполнено успешно, иначе False.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверка наличия профиля
            cursor.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
            profile = cursor.fetchone()
            
            if not profile:
                # Профиль не существует, создаем новый с summary_json
                self.add_profile(user_id, summary_data, None)
                return True
            
            # Профиль существует, обновляем только summary_json
            summary_json = json.dumps(summary_data)
            cursor.execute(
                "UPDATE profiles SET summary_json = ? WHERE user_id = ?",
                (summary_json, user_id)
            )
            conn.commit()
            
            logger.info(f"Обновлены данные психологического профиля для пользователя {user_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении данных психологического профиля: {e}")
            conn.rollback()
            return False
    
    # Функции для работы с напоминаниями
    
    def add_reminder(self, user_id: int, reminder_time: str, text: str) -> int:
        """
        Добавление напоминания для пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            reminder_time: Время напоминания (формат ISO или cron).
            text: Текст напоминания.
            
        Returns:
            int: ID напоминания в базе данных.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO reminders (user_id, reminder_time, text) VALUES (?, ?, ?)",
            (user_id, reminder_time, text)
        )
        conn.commit()
        
        reminder_id = cursor.lastrowid
        logger.info(f"Добавлено напоминание ID {reminder_id} для пользователя {user_id}")
        return reminder_id
    
    def enable_reminder(self, user_id: int, message: Optional[str] = None) -> bool:
        """
        Включение напоминаний для пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            message: Опциональный текст напоминания.
            
        Returns:
            bool: True, если операция выполнена успешно.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем наличие записи в таблице reminders
            cursor.execute("SELECT id FROM reminders WHERE user_id = ?", (user_id,))
            reminder = cursor.fetchone()
            
            current_time = "20:00"  # Время напоминания по умолчанию
            
            if reminder:
                # Обновляем существующую запись
                if message:
                    cursor.execute(
                        "UPDATE reminders SET reminder_time = ?, text = ?, is_sent = 0 WHERE user_id = ?",
                        (current_time, message, user_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE reminders SET reminder_time = ?, is_sent = 0 WHERE user_id = ?",
                        (current_time, user_id)
                    )
            else:
                # Создаем новую запись с текстом по умолчанию
                default_message = (
                    "🔔 Время для практики!\n\n"
                    "Не забудьте уделить время себе сегодня. "
                    "Вы можете выполнить медитацию с помощью команды /meditate."
                )
                text = message if message else default_message
                
                cursor.execute(
                    "INSERT INTO reminders (user_id, reminder_time, text, is_sent) VALUES (?, ?, ?, 0)",
                    (user_id, current_time, text)
                )
            
            conn.commit()
            logger.info(f"Напоминания включены для пользователя {user_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при включении напоминаний: {e}")
            conn.rollback()
            return False
            
    def disable_reminder(self, user_id: int) -> bool:
        """
        Отключение напоминаний для пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            bool: True, если операция выполнена успешно.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем наличие записи
            cursor.execute("SELECT id FROM reminders WHERE user_id = ?", (user_id,))
            reminder = cursor.fetchone()
            
            if not reminder:
                # Если записи нет, считаем что напоминания отключены
                return True
                
            # Удаляем запись
            cursor.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
            conn.commit()
            
            logger.info(f"Напоминания отключены для пользователя {user_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при отключении напоминаний: {e}")
            conn.rollback()
            return False
            
    def get_reminder_status(self, user_id: int) -> Optional[Dict]:
        """
        Получение статуса напоминаний пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            Optional[Dict]: Словарь с данными о напоминаниях или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE user_id = ?", (user_id,))
        reminder = cursor.fetchone()
        
        if reminder:
            reminder_dict = dict(reminder)
            # Добавляем флаг активности
            reminder_dict["is_active"] = True
            return reminder_dict
            
        return None
        
    def get_reminder_message(self, user_id: int) -> Optional[Dict]:
        """
        Получение текста напоминания для пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            
        Returns:
            Optional[Dict]: Словарь с сообщением напоминания или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, text FROM reminders WHERE user_id = ?",
            (user_id,)
        )
        reminder = cursor.fetchone()
        
        if reminder:
            return dict(reminder)
            
        return None
        
    def get_users_with_active_reminders(self) -> List[Dict]:
        """
        Получение всех пользователей с активными напоминаниями.
        
        Returns:
            List[Dict]: Список пользователей с активными напоминаниями.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.tg_id, u.full_name
            FROM users u
            JOIN reminders r ON u.id = r.user_id
        """)
        users = cursor.fetchall()
        
        return [dict(user) for user in users]
    
    def get_reminder(self, reminder_id: int) -> Optional[Dict]:
        """
        Получение напоминания по ID.
        
        Args:
            reminder_id: ID напоминания.
            
        Returns:
            Optional[Dict]: Данные напоминания или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        reminder = cursor.fetchone()
        
        if reminder:
            return dict(reminder)
        
        return None
    
    def get_reminders_by_user_id(self, user_id: int, only_unsent: bool = False) -> List[Dict]:
        """
        Получение всех напоминаний пользователя.
        
        Args:
            user_id: ID пользователя в базе данных.
            only_unsent: Вернуть только неотправленные напоминания.
            
        Returns:
            List[Dict]: Список напоминаний пользователя.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM reminders WHERE user_id = ?"
        params = [user_id]
        
        if only_unsent:
            query += " AND is_sent = 0"
        
        cursor.execute(query, params)
        reminders = cursor.fetchall()
        
        return [dict(reminder) for reminder in reminders]
    
    def mark_reminder_sent(self, reminder_id: int) -> None:
        """
        Отметка напоминания как отправленного.
        
        Args:
            reminder_id: ID напоминания.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?",
            (reminder_id,)
        )
        conn.commit()
        logger.info(f"Напоминание ID {reminder_id} отмечено как отправленное")
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """
        Удаление напоминания.
        
        Args:
            reminder_id: ID напоминания.
            
        Returns:
            bool: True, если напоминание удалено, иначе False.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Напоминание ID {reminder_id} удалено")
            return True
            
        logger.warning(f"Напоминание ID {reminder_id} не найдено для удаления")
        return False
    
    def close(self) -> None:
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Соединение с базой данных закрыто")
    
    def __del__(self):
        """Деструктор для закрытия соединения при удалении объекта."""
        self.close() 