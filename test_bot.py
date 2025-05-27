#!/usr/bin/env python
"""
Тестирование основной функциональности бота
Проверяет ответы на базовые команды и обработку сообщений
"""

import os
import sys
import time
import asyncio
import argparse
import logging
from aiogram import Bot
from datetime import datetime
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [BOT_TEST] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bot_test.log")]
)
logger = logging.getLogger("bot_test")

# Загружаем переменные окружения
load_dotenv()

async def test_bot_commands(bot_token=None, admin_chat_id=None):
    """
    Тестирует базовые команды бота
    
    Args:
        bot_token (str, optional): Токен бота. Если не указан, 
                                 будет использоваться переменная окружения BOT_TOKEN.
        admin_chat_id (int, optional): ID чата администратора для тестирования. 
                                      Если не указан, команды не будут отправлены.
    
    Returns:
        dict: Результаты тестирования
    """
    if not bot_token:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("Не указан BOT_TOKEN")
            return {
                "success": False,
                "error": "BOT_TOKEN не найден",
                "results": {}
            }
    
    # Если не указан admin_chat_id, тестируем только подключение
    if not admin_chat_id:
        try:
            bot = Bot(token=bot_token)
            me = await bot.get_me()
            logger.info(f"Подключение к боту успешно: @{me.username}")
            await bot.session.close()
            return {
                "success": True,
                "bot_info": {"username": me.username, "id": me.id},
                "results": {}
            }
        except Exception as e:
            logger.error(f"Ошибка при подключении к боту: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {}
            }
    
    # Если указан admin_chat_id, тестируем команды
    results = {
        "start": {"success": False, "response": None, "error": None},
        "help": {"success": False, "response": None, "error": None},
        "profile": {"success": False, "response": None, "error": None},
        "text_message": {"success": False, "response": None, "error": None}
    }
    
    try:
        # Создаем экземпляр бота
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        logger.info(f"Подключение к боту успешно: @{me.username}")
        logger.info(f"Тестирование команд в чате {admin_chat_id}")
        
        # Тестируем команду /start
        try:
            logger.info("Тестирование команды /start")
            message = await bot.send_message(
                chat_id=admin_chat_id,
                text="[ТЕСТ] Запускаю тестирование команды /start"
            )
            response = await bot.send_message(
                chat_id=admin_chat_id,
                text="/start"
            )
            # Ждем ответа бота
            await asyncio.sleep(3)
            results["start"]["success"] = True
            logger.info("Команда /start отправлена успешно")
        except Exception as e:
            logger.error(f"Ошибка при тестировании команды /start: {e}")
            results["start"]["error"] = str(e)
        
        # Тестируем команду /help
        try:
            logger.info("Тестирование команды /help")
            message = await bot.send_message(
                chat_id=admin_chat_id,
                text="[ТЕСТ] Запускаю тестирование команды /help"
            )
            response = await bot.send_message(
                chat_id=admin_chat_id,
                text="/help"
            )
            # Ждем ответа бота
            await asyncio.sleep(3)
            results["help"]["success"] = True
            logger.info("Команда /help отправлена успешно")
        except Exception as e:
            logger.error(f"Ошибка при тестировании команды /help: {e}")
            results["help"]["error"] = str(e)
        
        # Тестируем команду /profile
        try:
            logger.info("Тестирование команды /profile")
            message = await bot.send_message(
                chat_id=admin_chat_id,
                text="[ТЕСТ] Запускаю тестирование команды /profile"
            )
            response = await bot.send_message(
                chat_id=admin_chat_id,
                text="/profile"
            )
            # Ждем ответа бота
            await asyncio.sleep(3)
            results["profile"]["success"] = True
            logger.info("Команда /profile отправлена успешно")
        except Exception as e:
            logger.error(f"Ошибка при тестировании команды /profile: {e}")
            results["profile"]["error"] = str(e)
        
        # Тестируем обработку обычного текстового сообщения
        try:
            logger.info("Тестирование обработки текстового сообщения")
            message = await bot.send_message(
                chat_id=admin_chat_id,
                text="[ТЕСТ] Запускаю тестирование обработки текстового сообщения"
            )
            response = await bot.send_message(
                chat_id=admin_chat_id,
                text="Тестовое сообщение для проверки функциональности бота"
            )
            # Ждем ответа бота
            await asyncio.sleep(5)
            results["text_message"]["success"] = True
            logger.info("Текстовое сообщение отправлено успешно")
        except Exception as e:
            logger.error(f"Ошибка при тестировании обработки текстового сообщения: {e}")
            results["text_message"]["error"] = str(e)
        
        # Завершаем тестирование
        try:
            await bot.send_message(
                chat_id=admin_chat_id,
                text="[ТЕСТ] Тестирование завершено"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения о завершении тестирования: {e}")
        
        # Закрываем сессию бота
        await bot.session.close()
        
        # Общий результат
        success = all(results[cmd]["success"] for cmd in results)
        
        return {
            "success": success,
            "bot_info": {"username": me.username, "id": me.id},
            "results": results
        }
    except Exception as e:
        logger.error(f"Ошибка при тестировании бота: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": results
        }

async def main():
    """
    Основная функция для запуска тестирования
    """
    parser = argparse.ArgumentParser(description="Тестирование основной функциональности бота")
    parser.add_argument("--token", help="Токен бота для тестирования")
    parser.add_argument("--admin-chat-id", type=int, help="ID чата администратора для тестирования")
    
    args = parser.parse_args()
    
    # Получаем токен бота
    bot_token = args.token or os.environ.get("BOT_TOKEN")
    if not bot_token:
        logger.error("Не указан токен бота")
        sys.exit(1)
    
    # Тестируем бота
    result = await test_bot_commands(bot_token, args.admin_chat_id)
    
    # Выводим результаты
    if result["success"]:
        logger.info(f"Тестирование успешно завершено. Бот: @{result['bot_info']['username']}")
        
        # Если был указан admin_chat_id, выводим результаты тестирования команд
        if args.admin_chat_id:
            for cmd, cmd_result in result["results"].items():
                status = "✅ Успешно" if cmd_result["success"] else f"❌ Ошибка: {cmd_result['error']}"
                logger.info(f"Тест команды {cmd}: {status}")
    else:
        logger.error(f"Тестирование завершилось с ошибкой: {result.get('error', 'Неизвестная ошибка')}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка при выполнении тестирования: {e}")
        sys.exit(1) 