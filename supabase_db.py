import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from supabase import create_client, Client

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение ключей Supabase из .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Класс для работы с Supabase
class SupabaseDB:
    _instance = None
    
    def __new__(cls):
        """Паттерн Singleton для экземпляра SupabaseDB"""
        if cls._instance is None:
            cls._instance = super(SupabaseDB, cls).__new__(cls)
            try:
                cls._instance.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("Supabase клиент успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Supabase: {e}")
                cls._instance.supabase = None
        return cls._instance
    
    @property
    def is_connected(self) -> bool:
        """Проверяет подключение к Supabase"""
        return self.supabase is not None
    
    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по его Telegram ID
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        try:
            response = self.supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {telegram_id}: {e}")
            return None
    
    async def create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Создает нового пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя в Telegram
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные созданного пользователя или None в случае ошибки
        """
        try:
            user_data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }
            
            # Проверяем, существует ли пользователь
            existing_user = await self.get_user(telegram_id)
            if existing_user:
                # Обновляем данные пользователя
                response = self.supabase.table("users").update(user_data).eq("telegram_id", telegram_id).execute()
                logger.info(f"Обновлены данные пользователя {telegram_id}")
                return response.data[0] if response.data else None
            
            # Создаем нового пользователя
            response = self.supabase.table("users").insert(user_data).execute()
            logger.info(f"Создан новый пользователь {telegram_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении пользователя {telegram_id}: {e}")
            return None
    
    async def save_profile(self, telegram_id: int, profile_text: str, details_text: str, answers: Dict[str, Any]) -> bool:
        """
        Сохраняет профиль пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            profile_text: Текст краткого профиля
            details_text: Текст детального профиля
            answers: Словарь с ответами пользователя
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            # Проверяем, существует ли пользователь
            user = await self.get_user(telegram_id)
            if not user:
                logger.warning(f"Попытка сохранить профиль для несуществующего пользователя {telegram_id}")
                return False
            
            profile_data = {
                "user_id": user["id"],  # Используем UUID из таблицы users
                "telegram_id": telegram_id,
                "profile_text": profile_text,
                "details_text": details_text,
                "answers": json.dumps(answers, ensure_ascii=False)
            }
            
            # Проверяем, есть ли уже профиль у пользователя
            response = self.supabase.table("profiles").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                # Обновляем существующий профиль
                update_response = self.supabase.table("profiles").update(profile_data).eq("telegram_id", telegram_id).execute()
                logger.info(f"Обновлен профиль пользователя {telegram_id}")
                return True
            
            # Создаем новый профиль
            insert_response = self.supabase.table("profiles").insert(profile_data).execute()
            logger.info(f"Создан новый профиль для пользователя {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении профиля пользователя {telegram_id}: {e}")
            return False
    
    async def get_profile(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает профиль пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict[str, Any]]: Данные профиля или None, если профиль не найден
        """
        try:
            response = self.supabase.table("profiles").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                # Преобразуем строку JSON в словарь
                if "answers" in profile and profile["answers"]:
                    profile["answers"] = json.loads(profile["answers"])
                return profile
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении профиля пользователя {telegram_id}: {e}")
            return None
    
    async def save_reminder(self, telegram_id: int, time: str, days: List[str], active: bool) -> bool:
        """
        Сохраняет настройки напоминаний пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            time: Время напоминания в формате "HH:MM"
            days: Список дней недели для напоминаний
            active: Активность напоминаний
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            # Проверяем, существует ли пользователь
            user = await self.get_user(telegram_id)
            if not user:
                logger.warning(f"Попытка сохранить напоминание для несуществующего пользователя {telegram_id}")
                return False
            
            reminder_data = {
                "user_id": user["id"],  # Используем UUID из таблицы users
                "telegram_id": telegram_id,
                "time": time,
                "days": json.dumps(days, ensure_ascii=False),
                "active": active
            }
            
            # Проверяем, есть ли уже напоминания у пользователя
            response = self.supabase.table("reminders").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                # Обновляем существующие напоминания
                update_response = self.supabase.table("reminders").update(reminder_data).eq("telegram_id", telegram_id).execute()
                logger.info(f"Обновлены настройки напоминаний пользователя {telegram_id}")
                return True
            
            # Создаем новые настройки напоминаний
            insert_response = self.supabase.table("reminders").insert(reminder_data).execute()
            logger.info(f"Созданы новые настройки напоминаний для пользователя {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек напоминаний пользователя {telegram_id}: {e}")
            return False
    
    async def get_reminder(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает настройки напоминаний пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict[str, Any]]: Настройки напоминаний или None, если настройки не найдены
        """
        try:
            response = self.supabase.table("reminders").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                reminder = response.data[0]
                # Преобразуем строку JSON в список
                if "days" in reminder and reminder["days"]:
                    reminder["days"] = json.loads(reminder["days"])
                return reminder
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении настроек напоминаний пользователя {telegram_id}: {e}")
            return None
    
    async def get_all_active_reminders(self) -> List[Dict[str, Any]]:
        """
        Получает все активные напоминания
        
        Returns:
            List[Dict[str, Any]]: Список активных напоминаний
        """
        try:
            response = self.supabase.table("reminders").select("*").eq("active", True).execute()
            
            reminders = []
            for reminder in response.data:
                # Преобразуем строку JSON в список
                if "days" in reminder and reminder["days"]:
                    reminder["days"] = json.loads(reminder["days"])
                reminders.append(reminder)
            
            return reminders
        except Exception as e:
            logger.error(f"Ошибка при получении активных напоминаний: {e}")
            return []
    
    async def save_answer(self, telegram_id: int, question_id: str, answer_text: str) -> bool:
        """
        Сохраняет ответ пользователя на вопрос
        
        Args:
            telegram_id: ID пользователя в Telegram
            question_id: ID вопроса
            answer_text: Текст ответа
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            # Проверяем, существует ли пользователь
            user = await self.get_user(telegram_id)
            if not user:
                logger.warning(f"Попытка сохранить ответ для несуществующего пользователя {telegram_id}")
                return False
            
            answer_data = {
                "user_id": user["id"],  # Используем UUID из таблицы users
                "telegram_id": telegram_id,
                "question_id": question_id,
                "answer_text": answer_text
            }
            
            # Проверяем, есть ли уже ответ на этот вопрос
            response = self.supabase.table("answers").select("*").eq("telegram_id", telegram_id).eq("question_id", question_id).execute()
            
            if response.data and len(response.data) > 0:
                # Обновляем существующий ответ
                update_response = self.supabase.table("answers").update({"answer_text": answer_text}).eq("id", response.data[0]["id"]).execute()
                logger.info(f"Обновлен ответ пользователя {telegram_id} на вопрос {question_id}")
                return True
            
            # Создаем новый ответ
            insert_response = self.supabase.table("answers").insert(answer_data).execute()
            logger.info(f"Создан новый ответ пользователя {telegram_id} на вопрос {question_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении ответа пользователя {telegram_id} на вопрос {question_id}: {e}")
            return False
    
    async def get_user_answers(self, telegram_id: int) -> List[Dict[str, Any]]:
        """
        Получает все ответы пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            List[Dict[str, Any]]: Список ответов пользователя
        """
        try:
            response = self.supabase.table("answers").select("*").eq("telegram_id", telegram_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Ошибка при получении ответов пользователя {telegram_id}: {e}")
            return []

# Создаем глобальный экземпляр SupabaseDB
db = SupabaseDB() 