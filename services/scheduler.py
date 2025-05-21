import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from db import Database

# Настройка логирования
logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Класс для работы с планировщиком напоминаний."""
    
    def __init__(self, bot: Bot, db: Database):
        """
        Инициализация планировщика напоминаний.
        
        Args:
            bot: Экземпляр бота для отправки сообщений.
            db: Экземпляр базы данных для получения пользователей.
        """
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()
        
        # Текст напоминания по умолчанию
        self.default_reminder_text = (
            "🔔 Не забудьте уделить время себе сегодня!\n\n"
            "Практика медитации поможет снять стресс и улучшить самочувствие.\n"
            "Попробуйте медитацию с помощью команды /meditate."
        )
    
    def start(self) -> None:
        """Запуск планировщика с ежедневным заданием в 20:00."""
        # Добавляем задание на отправку напоминаний каждый день в 20:00
        self.scheduler.add_job(
            self.send_reminders,
            CronTrigger(hour=20, minute=0),
            id="daily_reminders",
            replace_existing=True,
            name="Ежедневные напоминания в 20:00"
        )
        
        # Запускаем планировщик
        self.scheduler.start()
        logger.info("Планировщик напоминаний запущен, задание настроено на 20:00")
    
    def shutdown(self) -> None:
        """Остановка планировщика."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Планировщик напоминаний остановлен")
    
    async def send_reminders(self) -> None:
        """
        Отправка напоминаний всем активным пользователям.
        Получает пользователей из БД и отправляет сообщение каждому,
        у кого включены напоминания.
        """
        logger.info("Начинаем отправку напоминаний...")
        
        try:
            # Получаем всех пользователей с активными напоминаниями
            users_with_reminders = self.db.get_users_with_active_reminders()
            
            if not users_with_reminders:
                logger.info("Нет пользователей с активными напоминаниями")
                return
            
            logger.info(f"Найдено {len(users_with_reminders)} пользователей с активными напоминаниями")
            
            # Отправляем напоминания каждому пользователю
            for user in users_with_reminders:
                try:
                    tg_id = user.get("tg_id")
                    user_id = user.get("id")
                    
                    # Получаем текст напоминания для пользователя (если есть)
                    reminder_data = self.db.get_reminder_message(user_id)
                    message_text = reminder_data.get("message", self.default_reminder_text) if reminder_data else self.default_reminder_text
                    
                    # Отправляем сообщение пользователю
                    await self.bot.send_message(
                        chat_id=tg_id,
                        text=message_text
                    )
                    
                    logger.info(f"Напоминание отправлено пользователю {tg_id}")
                    
                    # Небольшая задержка между отправками сообщений
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"Ошибка при отправке напоминания пользователю {tg_id}: {e}")
            
            logger.info("Отправка напоминаний завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний: {e}")
    
    async def send_test_reminder(self, tg_id: int) -> bool:
        """
        Отправка тестового напоминания конкретному пользователю.
        
        Args:
            tg_id: Telegram ID пользователя.
            
        Returns:
            bool: True, если напоминание успешно отправлено, иначе False.
        """
        try:
            # Получаем пользователя из БД
            user = self.db.get_user_by_tg_id(tg_id)
            
            if not user:
                logger.warning(f"Пользователь с tg_id {tg_id} не найден в БД")
                return False
            
            user_id = user.get("id")
            
            # Получаем текст напоминания
            reminder_data = self.db.get_reminder_message(user_id)
            message_text = reminder_data.get("message", self.default_reminder_text) if reminder_data else self.default_reminder_text
            
            test_message = (
                "🔔 Тестовое напоминание\n\n"
                f"{message_text}\n\n"
                "✅ Напоминания успешно включены и будут приходить каждый день в 20:00."
            )
            
            # Отправляем тестовое напоминание
            await self.bot.send_message(
                chat_id=tg_id,
                text=test_message
            )
            
            logger.info(f"Тестовое напоминание отправлено пользователю {tg_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке тестового напоминания пользователю {tg_id}: {e}")
            return False 