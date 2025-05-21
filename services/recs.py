import os
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI с API-ключом из переменных окружения
http_client = httpx.AsyncClient()
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=http_client
)

# Список доступных фокусов для рекомендаций
AVAILABLE_FOCUSES = {
    "burnout": "эмоциональным выгоранием",
    "anxiety": "тревогой",
    "depression": "депрессией",
    "stress": "стрессом",
    "postpartum": "послеродовым периодом",
    "self-esteem": "низкой самооценкой",
    "grief": "горем и утратой",
    "relationship": "отношениями",
    "family": "семейными проблемами",
    "career": "карьерными вопросами",
    "motivation": "мотивацией",
    "sleep": "проблемами сна",
    "default": "повседневными трудностями"
}

# Словарь для хранения последнего времени запроса пользователя
last_request_time: Dict[int, float] = {}

async def generate_recommendation(text: str, user_id: int, focus: str = "default") -> str:
    """
    Генерация персонализированной рекомендации для пользователя с использованием OpenAI.
    
    Args:
        text: Текст сообщения пользователя.
        user_id: ID пользователя в Telegram.
        focus: Фокус рекомендации (burnout, anxiety, postpartum и т.д.).
        
    Returns:
        str: Сгенерированная рекомендация.
    """
    # Проверка наличия антиспам-защиты
    current_time = asyncio.get_event_loop().time()
    if user_id in last_request_time:
        time_diff = current_time - last_request_time[user_id]
        if time_diff < 5:  # Не чаще одного раза в 5 секунд
            wait_time = round(5 - time_diff, 1)
            return f"Пожалуйста, подождите {wait_time} сек. перед следующим запросом."
    
    # Обновляем время последнего запроса
    last_request_time[user_id] = current_time
    
    # Нормализуем фокус
    normalized_focus = focus.lower()
    if normalized_focus not in AVAILABLE_FOCUSES:
        normalized_focus = "default"
    
    # Получаем текстовое описание фокуса
    focus_description = AVAILABLE_FOCUSES[normalized_focus]
    
    try:
        # Создаем запрос к OpenAI
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Можно заменить на gpt-4, если доступен
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": f"Ты — профессиональный психолог. Дай 1–2 коротких, практических совета для клиента с фокусом: {focus_description}. Ответ должен быть на русском языке, не более 3-4 предложений, без введения и заключения."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        
        # Получаем результат
        result = response.choices[0].message.content.strip()
        logger.info(f"Сгенерирована рекомендация для пользователя {user_id} с фокусом '{normalized_focus}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при генерации рекомендации: {e}")
        return "Извините, не удалось сгенерировать рекомендацию. Пожалуйста, попробуйте позже."

def detect_focus(text: str) -> Optional[str]:
    """
    Определяет фокус рекомендации на основе текста пользователя.
    
    Args:
        text: Текст сообщения пользователя.
        
    Returns:
        Optional[str]: Фокус рекомендации или None, если фокус не определен.
    """
    text_lower = text.lower()
    
    focus_keywords = {
        "burnout": ["выгорание", "выгорел", "устал", "истощение", "нет сил", "перегрузк"],
        "anxiety": ["тревога", "тревожность", "паник", "волнение", "беспокойств", "страх"],
        "depression": ["депресси", "подавлен", "грусть", "тоска", "печаль", "апатия", "нет настроения"],
        "stress": ["стресс", "напряжение", "нервы", "нервничаю", "давление"],
        "postpartum": ["после родов", "послеродов", "ребенок", "малыш", "грудное", "кормление"],
        "self-esteem": ["самооценка", "неуверенность", "комплекс", "не справляюсь", "недостаточно"],
        "grief": ["горе", "потеря", "утрата", "умер", "смерть", "скорбь"],
        "relationship": ["отношения", "партнер", "муж", "жена", "расстался", "любовь", "измена"],
        "family": ["семья", "родители", "дети", "мама", "папа", "ребенок", "конфликт"],
        "career": ["работа", "карьера", "должность", "профессия", "увольнение", "коллеги"],
        "motivation": ["мотивация", "лень", "прокрастинация", "откладываю", "не могу начать"],
        "sleep": ["сон", "бессонница", "не спится", "просыпаюсь", "недосып"]
    }
    
    for focus, keywords in focus_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return focus
    
    return None 