"""
Модуль-заглушка для Supabase, используется при отсутствии пакета supabase-py
"""
import logging
import json
import os
import sqlite3
from typing import Dict, Any, Optional, List

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем моклк-класс для Supabase
class SupabaseDB:
    _instance = None
    
    def __new__(cls):
        """Паттерн Singleton для экземпляра SupabaseDB"""
        if cls._instance is None:
            cls._instance = super(SupabaseDB, cls).__new__(cls)
            cls._instance.supabase = None
            logger.warning("Используется заглушка для Supabase. База данных работает в SQLite-режиме.")
            
            # Инициализация SQLite
            try:
                db_path = os.getenv("SQLITE_DB_PATH", "ona.db")
                cls._instance.conn = sqlite3.connect(db_path)
                cls._instance.conn.row_factory = sqlite3.Row
                logger.info(f"Подключено к SQLite базе данных: {db_path}")
            except Exception as e:
                logger.error(f"Ошибка при подключении к SQLite: {e}")
                cls._instance.conn = None
        
        return cls._instance
    
    @property
    def is_connected(self) -> bool:
        """Проверяет подключение к базе данных"""
        return self.conn is not None
    
    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по его Telegram ID"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {telegram_id}: {e}")
            return None
    
    async def create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
        """Создает нового пользователя"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Обновляем данные пользователя
                cursor.execute(
                    "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE telegram_id = ?",
                    (username, first_name, last_name, telegram_id)
                )
            else:
                # Создаем нового пользователя
                cursor.execute(
                    "INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                    (telegram_id, username, first_name, last_name)
                )
            
            self.conn.commit()
            
            # Получаем обновленные данные пользователя
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении пользователя {telegram_id}: {e}")
            return None
    
    async def save_profile(self, telegram_id: int, profile_text: str, details_text: str, answers: Dict[str, Any]) -> bool:
        """Сохраняет профиль пользователя"""
        if not self.is_connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Преобразуем словарь в JSON
            answers_json = json.dumps(answers, ensure_ascii=False)
            
            # Проверяем, есть ли уже профиль у пользователя
            cursor.execute("SELECT * FROM profiles WHERE telegram_id = ?", (telegram_id,))
            existing_profile = cursor.fetchone()
            
            if existing_profile:
                # Обновляем существующий профиль
                cursor.execute(
                    "UPDATE profiles SET profile_text = ?, details_text = ?, answers = ? WHERE telegram_id = ?",
                    (profile_text, details_text, answers_json, telegram_id)
                )
            else:
                # Создаем новый профиль
                cursor.execute(
                    "INSERT INTO profiles (telegram_id, profile_text, details_text, answers) VALUES (?, ?, ?, ?)",
                    (telegram_id, profile_text, details_text, answers_json)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении профиля пользователя {telegram_id}: {e}")
            return False
    
    async def get_profile(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает профиль пользователя"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE telegram_id = ?", (telegram_id,))
            profile = cursor.fetchone()
            
            if profile:
                profile_dict = dict(profile)
                # Преобразуем строку JSON в словарь
                if "answers" in profile_dict and profile_dict["answers"]:
                    profile_dict["answers"] = json.loads(profile_dict["answers"])
                return profile_dict
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении профиля пользователя {telegram_id}: {e}")
            return None
    
    async def save_reminder(self, telegram_id: int, time: str, days: List[str], active: bool) -> bool:
        """Сохраняет настройки напоминаний пользователя"""
        if not self.is_connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Преобразуем список в JSON
            days_json = json.dumps(days, ensure_ascii=False)
            
            # Проверяем, есть ли уже напоминания у пользователя
            cursor.execute("SELECT * FROM reminders WHERE telegram_id = ?", (telegram_id,))
            existing_reminder = cursor.fetchone()
            
            if existing_reminder:
                # Обновляем существующие напоминания
                cursor.execute(
                    "UPDATE reminders SET time = ?, days = ?, active = ? WHERE telegram_id = ?",
                    (time, days_json, active, telegram_id)
                )
            else:
                # Создаем новые настройки напоминаний
                cursor.execute(
                    "INSERT INTO reminders (telegram_id, time, days, active) VALUES (?, ?, ?, ?)",
                    (telegram_id, time, days_json, active)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек напоминаний пользователя {telegram_id}: {e}")
            return False
    
    async def get_reminder(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает настройки напоминаний пользователя"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM reminders WHERE telegram_id = ?", (telegram_id,))
            reminder = cursor.fetchone()
            
            if reminder:
                reminder_dict = dict(reminder)
                # Преобразуем строку JSON в список
                if "days" in reminder_dict and reminder_dict["days"]:
                    reminder_dict["days"] = json.loads(reminder_dict["days"])
                return reminder_dict
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении настроек напоминаний пользователя {telegram_id}: {e}")
            return None
    
    async def get_all_active_reminders(self) -> List[Dict[str, Any]]:
        """Получает все активные напоминания"""
        if not self.is_connected:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM reminders WHERE active = 1")
            reminders = cursor.fetchall()
            
            result = []
            for reminder in reminders:
                reminder_dict = dict(reminder)
                # Преобразуем строку JSON в список
                if "days" in reminder_dict and reminder_dict["days"]:
                    reminder_dict["days"] = json.loads(reminder_dict["days"])
                result.append(reminder_dict)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении активных напоминаний: {e}")
            return []
    
    async def save_answer(self, telegram_id: int, question_id: str, answer_text: str) -> bool:
        """Сохраняет ответ пользователя на вопрос"""
        if not self.is_connected:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Проверяем, есть ли уже ответ на этот вопрос
            cursor.execute(
                "SELECT * FROM answers WHERE telegram_id = ? AND question_id = ?", 
                (telegram_id, question_id)
            )
            existing_answer = cursor.fetchone()
            
            if existing_answer:
                # Обновляем существующий ответ
                cursor.execute(
                    "UPDATE answers SET answer_text = ? WHERE telegram_id = ? AND question_id = ?",
                    (answer_text, telegram_id, question_id)
                )
            else:
                # Создаем новый ответ
                cursor.execute(
                    "INSERT INTO answers (telegram_id, question_id, answer_text) VALUES (?, ?, ?)",
                    (telegram_id, question_id, answer_text)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении ответа пользователя {telegram_id} на вопрос {question_id}: {e}")
            return False
    
    async def get_user_answers(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получает все ответы пользователя"""
        if not self.is_connected:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM answers WHERE telegram_id = ?", (telegram_id,))
            answers = cursor.fetchall()
            
            return [dict(answer) for answer in answers]
        except Exception as e:
            logger.error(f"Ошибка при получении ответов пользователя {telegram_id}: {e}")
            return []

# Создаем экземпляр класса, который будет использоваться в приложении
db = SupabaseDB() 