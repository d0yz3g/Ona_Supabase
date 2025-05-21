import os
import logging
import json
from typing import Dict, Any, List
from openai import AsyncOpenAI

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI с API-ключом из переменных окружения
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_profile(profile_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация психологического профиля пользователя с использованием OpenAI.
    
    Args:
        profile_json: Данные профиля пользователя в формате JSON.
        
    Returns:
        Dict[str, Any]: Результат анализа профиля, включающий summary, strengths и growth_areas.
    """
    try:
        # Преобразуем профиль в строку для передачи в промпт
        profile_str = json.dumps(profile_json, ensure_ascii=False, indent=2)
        
        # Создаем запрос к OpenAI
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Можно заменить на gpt-4, если доступен
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": "Ты — клинический психолог без эзотерики. Твоя задача - проанализировать профиль пользователя и предоставить психологическую оценку. Ответ должен включать общий текстовый анализ (summary), список из 3-5 сильных сторон (strengths) и 2-3 направления для развития (growth_areas). Твои ответы должны быть профессиональными, основанными на данных и без эзотерики. Отвечай только на русском языке."
                },
                {
                    "role": "user",
                    "content": f"Вот данные профиля пользователя для анализа: {profile_str}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Получаем результат
        result_content = response.choices[0].message.content
        
        # Преобразуем результат из JSON-строки в словарь
        result = json.loads(result_content)
        
        # Проверяем наличие необходимых полей
        expected_fields = ["summary", "strengths", "growth_areas"]
        for field in expected_fields:
            if field not in result:
                logger.warning(f"Поле {field} отсутствует в ответе OpenAI")
                result[field] = []  # Или другое дефолтное значение
                
        logger.info("Успешно сгенерирован профиль пользователя")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при генерации профиля: {e}")
        # Возвращаем базовый профиль в случае ошибки
        return {
            "summary": "Не удалось сгенерировать психологический профиль из-за технической ошибки.",
            "strengths": [],
            "growth_areas": []
        } 