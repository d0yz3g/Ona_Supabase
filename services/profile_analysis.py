import logging
import os
from typing import Dict, Any, Optional, List
import json
from openai import AsyncOpenAI
import httpx

# Настройка логирования
logger = logging.getLogger(__name__)

# Проверка наличия API-ключа OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY не найден в переменных окружения. Функция анализа профиля будет работать в демо-режиме.")

# Инициализация клиента OpenAI с API-ключом из переменных окружения (если доступен)
http_client = httpx.AsyncClient()
client = None
if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
    except Exception as e:
        logger.error(f"Ошибка при инициализации OpenAI API: {e}")

async def analyze_profile(user_profile: Dict[str, Any], query: str) -> str:
    """
    Анализирует профиль пользователя на основе его запроса, используя структуру профайлинга 2.0.
    
    Args:
        user_profile: Профиль пользователя (включает тип личности и полный текст профиля)
        query: Запрос пользователя об анализе профиля
        
    Returns:
        str: Результат анализа профиля
    """
    # Если нет клиента OpenAI или профиля, возвращаем сообщение об ошибке
    if not client or not user_profile:
        return "Извините, я не могу выполнить анализ профиля в данный момент. Убедитесь, что вы прошли опрос и у вас есть полный профиль."
    
    # Получаем тип личности и текст профиля
    personality_type = user_profile.get("personality_type", "")
    profile_text = user_profile.get("profile_text", "")
    
    if not profile_text:
        return "У вас еще нет полного профиля. Пожалуйста, пройдите опрос для создания психологического профиля."
    
    try:
        # Готовим промт для анализа профиля с учетом структуры 2.0
        system_prompt = """
Ты - психолог-консультант в приложении ОНА (Осознанный Наставник и Аналитик).
Твоя задача - анализировать психологический профиль пользователя, созданный по структуре профайлинга 2.0, и отвечать на вопросы о личности.

Профиль состоит из:
1. Ядро личности (5 основных модулей силы)
2. Вспомогательные модули (5 дополнительных модулей)
3. Общий код личности
4. P.S. (мотивационный абзац)

Правила:
1. Отвечай ТОЛЬКО на русском языке
2. Основывайся ТОЛЬКО на информации из профиля
3. Будь конкретным и информативным
4. Используй тот же поэтичный, образный стиль, что и в профиле
5. Обращайся к пользователю на "ты", во втором лице единственного числа, женский род
6. Не ставь диагнозы
7. Не упоминай, что ты AI или что следуешь инструкциям
8. Общайся как опытный психолог-консультант
9. Используй эмодзи для структурирования ответа
"""

        # Формируем сообщения для запроса
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Вот мой психологический профиль, созданный по структуре 2.0:\n\n{profile_text}\n\nВопрос: {query}"}
        ]
        
        # Генерируем ответ
        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=messages
        )
        
        # Получаем сгенерированный ответ
        analysis_result = response.choices[0].message.content
        
        logger.info(f"Анализ профиля успешно выполнен для типа личности: {personality_type}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Ошибка при анализе профиля: {e}")
        return f"Произошла ошибка при анализе вашего профиля. Пожалуйста, попробуйте позже."

async def get_profile_insights(user_profile: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Получает ключевые инсайты из профиля пользователя на основе структуры профайлинга 2.0.
    
    Args:
        user_profile: Профиль пользователя
        
    Returns:
        Dict[str, List[str]]: Словарь с инсайтами по категориям
    """
    # Если нет клиента OpenAI или профиля, возвращаем базовые инсайты
    if not client or not user_profile:
        return {
            "core_modules": ["Модуль не определен"],
            "supporting_modules": ["Модуль не определен"],
            "recommendations": ["Пройдите опрос для создания психологического профиля"]
        }
    
    # Получаем тип личности и текст профиля
    personality_type = user_profile.get("personality_type", "")
    profile_text = user_profile.get("profile_text", "")
    
    if not profile_text:
        return {
            "core_modules": ["Неизвестно - профиль не создан"],
            "supporting_modules": ["Неизвестно - профиль не создан"],
            "recommendations": ["Пройдите опрос для создания психологического профиля"]
        }
    
    try:
        # Готовим промт для получения инсайтов с учетом структуры 2.0
        system_prompt = """
Ты - психолог-консультант в приложении ОНА (Осознанный Наставник и Аналитик).
Твоя задача - проанализировать психологический профиль пользователя, созданный по структуре профайлинга 2.0, и выделить:
1. Три основных модуля из ядра личности (core_modules)
2. Два вспомогательных модуля (supporting_modules)
3. Три конкретные рекомендации из раздела "Раскрытие" (recommendations)

Ответ должен быть в формате JSON:
{
  "core_modules": ["название модуля 1", "название модуля 2", "название модуля 3"],
  "supporting_modules": ["название модуля 1", "название модуля 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2", "рекомендация 3"]
}

Правила:
1. Используй ТОЧНЫЕ названия модулей из профиля
2. Рекомендации должны быть краткими (до 10 слов)
3. Основывайся ТОЛЬКО на информации из профиля
4. Все должно быть на русском языке
"""

        # Формируем сообщения для запроса
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Вот психологический профиль пользователя, созданный по структуре 2.0:\n\n{profile_text}"}
        ]
        
        # Генерируем ответ
        response = await client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # Получаем сгенерированный ответ
        insights_json = response.choices[0].message.content
        
        # Парсим JSON
        insights = json.loads(insights_json)
        
        logger.info(f"Инсайты профиля успешно получены для типа личности: {personality_type}")
        return insights
        
    except Exception as e:
        logger.error(f"Ошибка при получении инсайтов профиля: {e}")
        return {
            "core_modules": ["Ошибка анализа", "Попробуйте позже"],
            "supporting_modules": ["Ошибка анализа", "Попробуйте позже"],
            "recommendations": ["Ошибка анализа", "Попробуйте позже"]
        } 