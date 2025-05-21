from .meditate import meditate_router
# Исправляем относительный импорт на абсолютный
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from handlers import questionnaire_router