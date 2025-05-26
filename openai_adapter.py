#!/usr/bin/env python3
"""
Адаптер для работы с openai API разных версий.
Поддерживает как старый API (0.28.x), так и новый (1.0.0+).
"""
import importlib.metadata
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Определение версии openai
try:
    openai_version = importlib.metadata.version('openai')
    major_version = int(openai_version.split('.')[0])
    logger.info(f"Обнаружена версия openai: {openai_version}")
except Exception as e:
    logger.error(f"Ошибка при определении версии openai: {e}")
    major_version = 0

# Импорт openai API в соответствии с версией
try:
    import openai
    
    if major_version >= 1:
        # Новый API (версия 1.0.0+)
        logger.info("Используется новый API openai (1.0.0+)")
        from openai import OpenAI, AsyncOpenAI
        
        class OpenAIAdapter:
            def __init__(self, api_key=None):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                self.client = OpenAI(api_key=self.api_key)
                
            def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
                return self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        
        class AsyncOpenAIAdapter:
            def __init__(self, api_key=None):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                self.client = AsyncOpenAI(api_key=self.api_key)
                
            async def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
                return await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        
    else:
        # Старый API (версия 0.28.x)
        logger.info("Используется старый API openai (0.28.x)")
        
        class OpenAIAdapter:
            def __init__(self, api_key=None):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                openai.api_key = self.api_key
                
            def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                    
                response = openai.ChatCompletion.create(**kwargs)
                return response
        
        class AsyncOpenAIAdapter:
            def __init__(self, api_key=None):
                self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
                openai.api_key = self.api_key
                
            async def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                    
                # Старая версия openai не поддерживает нативно async, используем обходной путь
                # через aiohttp или просто синхронный API
                try:
                    import asyncio
                    response = await asyncio.to_thread(openai.ChatCompletion.create, **kwargs)
                    return response
                except Exception as e:
                    logger.warning(f"Асинхронный вызов не удался: {e}. Использую синхронный API.")
                    return openai.ChatCompletion.create(**kwargs)
        
        # Эмулируем классы из нового API для совместимости
        class AsyncOpenAI:
            def __init__(self, api_key=None):
                self.api_key = api_key
                logger.warning("AsyncOpenAI - эмуляция класса из нового API через старый API")
                
        class OpenAI:
            def __init__(self, api_key=None):
                self.api_key = api_key
                logger.warning("OpenAI - эмуляция класса из нового API через старый API")

except ImportError as e:
    logger.error(f"Ошибка при импорте openai: {e}")
    
    # Заглушки на случай, если openai вообще не установлен
    class OpenAIAdapter:
        def __init__(self, api_key=None):
            self.api_key = api_key
            logger.error("OpenAI не установлен! Используется заглушка.")
            
        def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
            return {"choices": [{"message": {"content": "OpenAI не установлен!"}}]}
    
    class AsyncOpenAIAdapter:
        def __init__(self, api_key=None):
            self.api_key = api_key
            logger.error("OpenAI не установлен! Используется заглушка.")
            
        async def chat_completion_create(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
            return {"choices": [{"message": {"content": "OpenAI не установлен!"}}]}
    
    class AsyncOpenAI:
        def __init__(self, api_key=None):
            logger.error("OpenAI не установлен! Используется заглушка.")
    
    class OpenAI:
        def __init__(self, api_key=None):
            logger.error("OpenAI не установлен! Используется заглушка.")

# Создаем псевдонимы для использования в импорте
AsyncClient = AsyncOpenAI
SyncClient = OpenAI

# Для совместимости в точке входа
if __name__ == "__main__":
    print(f"OpenAI версия: {openai_version if 'openai_version' in locals() else 'не установлен'}")
    print(f"Используется {'новый' if major_version >= 1 else 'старый'} API")
    print("Доступные классы:")
    print("- OpenAIAdapter - адаптер для обеих версий API")
    print("- AsyncOpenAIAdapter - асинхронный адаптер для обеих версий API")
    print("- AsyncOpenAI - (совместимость с новым API)")
    print("- OpenAI - (совместимость с новым API)") 