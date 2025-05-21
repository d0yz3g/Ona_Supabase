import os
import logging
import json
import httpx
from typing import Dict, Any, List
from openai import AsyncOpenAI

# Настройка логирования
logger = logging.getLogger(__name__)

# Проверка наличия API-ключа OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY не найден в переменных окружения. Будет использован стандартный психологический профиль.")

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

# Стандартный психологический профиль для случаев, когда API недоступен
DEFAULT_PROFILE = {
    "summary": """
        На основе представленных данных виден человек, нацеленный на саморазвитие и самопознание. 
        Вам важно найти баланс между личными целями и потребностями окружающих. 
        Вы обладаете способностью к эмпатии и склонны к аналитическому мышлению.
        Вам важно чувствовать свою компетентность и полезность, при этом сохраняя внутреннюю гармонию и время для себя.
    """,
    "strengths": [
        "Стремление к самопознанию и личностному росту",
        "Способность к эмпатии и пониманию других",
        "Аналитический склад ума и способность видеть взаимосвязи",
        "Умение находить решения в сложных ситуациях",
        "Умение ценить значимые отношения"
    ],
    "growth_areas": [
        "Развитие навыков управления стрессом",
        "Улучшение баланса между личными потребностями и внешними обязательствами",
        "Работа над принятием неопределенности и адаптивностью"
    ]
}

async def generate_profile(profile_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация психологического профиля пользователя с использованием OpenAI.
    Если OpenAI API недоступен, возвращается стандартный профиль.
    
    Args:
        profile_json: Данные профиля пользователя в формате JSON.
        
    Returns:
        Dict[str, Any]: Результат анализа профиля, включающий summary, strengths и growth_areas.
    """
    # Если клиент OpenAI не инициализирован, возвращаем стандартный профиль
    if not client:
        logger.info("Используется стандартный психологический профиль (API недоступен)")
        return DEFAULT_PROFILE
    
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
                    "content": "Ты — клинический психолог без эзотерики. Твоя задача - проанализировать профиль пользователя и предоставить психологическую оценку. Ответ должен быть в формате JSON и включать общий текстовый анализ (summary), список из 3-5 сильных сторон (strengths) и 2-3 направления для развития (growth_areas). Твои ответы должны быть профессиональными, основанными на данных и без эзотерики. Отвечай только на русском языке."
                },
                {
                    "role": "user",
                    "content": f"Вот данные профиля пользователя для анализа в формате json: {profile_str}"
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
                result[field] = DEFAULT_PROFILE[field]  # Используем значение из стандартного профиля
                
        logger.info("Успешно сгенерирован профиль пользователя")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при генерации профиля: {e}")
        # Возвращаем стандартный профиль в случае ошибки
        return DEFAULT_PROFILE 