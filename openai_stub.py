
# Заглушка для AsyncOpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock AsyncOpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print(f"[Mock AsyncOpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

# Заглушка для OpenAI
class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock OpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print(f"[Mock OpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
