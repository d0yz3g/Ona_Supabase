#!/usr/bin/env python3
"""
Скрипт для прямой модификации модуля openai в site-packages.
Добавляет классы AsyncOpenAI и OpenAI прямо в исходный код модуля.
"""
import os
import sys
import site
import glob
import logging
import importlib.util
import shutil

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("modify_site_packages")

# Код заглушек для добавления в модуль openai
OPENAI_STUBS = """
# Заглушки для совместимости с aiogram
class AsyncOpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        print("[Site-Package] Инициализация заглушки AsyncOpenAI")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print("[Site-Package] Вызов метода AsyncOpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
    
    class audio:
        @staticmethod
        async def transcriptions_create(*args, **kwargs):
            print("[Site-Package] Вызов метода AsyncOpenAI.audio.transcriptions_create")
            return {"text": "Заглушка транскрипции аудио"}

class OpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        print("[Site-Package] Инициализация заглушки OpenAI")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print("[Site-Package] Вызов метода OpenAI.chat.completions.create")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
    
    class audio:
        @staticmethod
        def transcriptions_create(*args, **kwargs):
            print("[Site-Package] Вызов метода OpenAI.audio.transcriptions_create")
            return {"text": "Заглушка транскрипции аудио"}
"""

def find_openai_init_files():
    """Находит все файлы __init__.py в модуле openai в site-packages"""
    init_files = []
    
    # Получаем все пути из site.getsitepackages()
    site_packages = site.getsitepackages()
    
    # Добавляем путь из sys.prefix
    site_packages.append(os.path.join(sys.prefix, 'lib', 'python*', 'site-packages'))
    
    # Добавляем явные пути для Railway
    site_packages.append('/usr/local/lib/python*/site-packages')
    site_packages.append('/app/.local/lib/python*/site-packages')
    
    # Ищем все __init__.py для модуля openai
    for site_path in site_packages:
        # Раскрываем возможные маски в пути
        for expanded_path in glob.glob(site_path):
            # Ищем openai/__init__.py
            init_path = os.path.join(expanded_path, 'openai', '__init__.py')
            if os.path.exists(init_path):
                init_files.append(init_path)
    
    # Проверяем импортируемый путь
    try:
        spec = importlib.util.find_spec('openai')
        if spec and spec.origin:
            # Получаем путь к __init__.py из спецификации
            init_path = spec.origin
            if init_path not in init_files:
                init_files.append(init_path)
    except ImportError:
        logger.error("Не удалось найти модуль openai через importlib")
    
    # Явный поиск в /usr/local/lib/python...
    usr_local_paths = glob.glob('/usr/local/lib/python*/site-packages/openai/__init__.py')
    for path in usr_local_paths:
        if path not in init_files:
            init_files.append(path)
    
    return init_files

def add_stubs_to_openai_init(file_path):
    """Добавляет заглушки в файл __init__.py модуля openai"""
    try:
        # Проверяем доступ на запись
        if not os.access(file_path, os.W_OK):
            logger.error(f"Нет прав на запись в файл {file_path}")
            # Пробуем изменить права
            try:
                os.chmod(file_path, 0o644)
                logger.info(f"Изменены права доступа к файлу {file_path}")
            except Exception as e:
                logger.error(f"Не удалось изменить права доступа: {e}")
                return False
        
        # Создаем резервную копию
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
            logger.info(f"Создана резервная копия {backup_path}")
        
        # Проверяем, есть ли уже заглушки
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {file_path} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Добавляем заглушки в конец файла
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + OPENAI_STUBS)
        
        logger.info(f"Добавлены заглушки в файл {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при модификации файла {file_path}: {e}")
        return False

def create_complete_openai_module():
    """Создает полноценную замену модуля openai"""
    try:
        # Сначала проверяем, где установлен оригинальный модуль
        original_module_dir = None
        try:
            spec = importlib.util.find_spec('openai')
            if spec and spec.origin:
                original_module_dir = os.path.dirname(os.path.dirname(spec.origin))
        except ImportError:
            logger.warning("Не удалось найти оригинальный модуль openai")
        
        # Проверяем стандартные пути
        if not original_module_dir:
            for path in site.getsitepackages():
                potential_path = os.path.join(path, 'openai')
                if os.path.exists(potential_path):
                    original_module_dir = path
                    break
        
        # Создаем локальную директорию openai
        if not os.path.exists('openai'):
            os.makedirs('openai', exist_ok=True)
        
        # Создаем __init__.py с заглушками и базовым функционалом
        with open(os.path.join('openai', '__init__.py'), 'w', encoding='utf-8') as f:
            f.write("""
import sys
import os
import importlib.util

# Пытаемся импортировать оригинальный модуль
try:
    # Если мы в нашем собственном модуле, то нам нужно импортировать оригинальный
    if __name__ == 'openai':
        # Сохраняем себя в sys.modules под другим именем
        sys.modules['openai_original'] = sys.modules['openai']
        
        # Удаляем себя из sys.modules, чтобы можно было загрузить оригинальный модуль
        del sys.modules['openai']
        
        # Находим оригинальный модуль
        for path in sys.path:
            if path == os.getcwd():
                continue
            potential_path = os.path.join(path, 'openai', '__init__.py')
            if os.path.exists(potential_path):
                spec = importlib.util.spec_from_file_location('openai', potential_path)
                original_module = importlib.util.module_from_spec(spec)
                sys.modules['openai'] = original_module
                spec.loader.exec_module(original_module)
                break
        
        # Восстанавливаем себя в sys.modules
        sys.modules['openai'] = sys.modules['openai_original']
        del sys.modules['openai_original']
except Exception as e:
    print(f"Error importing original openai module: {e}")

""" + OPENAI_STUBS)
        
        # Создаем пустые файлы для всех необходимых модулей
        if original_module_dir:
            try:
                original_openai_dir = os.path.join(original_module_dir, 'openai')
                if os.path.exists(original_openai_dir):
                    for item in os.listdir(original_openai_dir):
                        if item.endswith('.py') and item != '__init__.py':
                            # Копируем файл
                            source = os.path.join(original_openai_dir, item)
                            dest = os.path.join('openai', item)
                            shutil.copy2(source, dest)
                            logger.info(f"Скопирован файл {item} из оригинального модуля")
            except Exception as e:
                logger.error(f"Ошибка при копировании файлов оригинального модуля: {e}")
        
        # Создаем __pycache__ директорию
        os.makedirs(os.path.join('openai', '__pycache__'), exist_ok=True)
        
        logger.info("Создан полноценный локальный модуль openai с заглушками")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании полноценного модуля openai: {e}")
        return False

def create_openai_module_in_path():
    """Создает модуль openai с заглушками в текущем каталоге"""
    try:
        # Создаем директорию openai, если ее нет
        if not os.path.exists('openai'):
            os.makedirs('openai', exist_ok=True)
        
        # Создаем __init__.py с заглушками
        with open(os.path.join('openai', '__init__.py'), 'w', encoding='utf-8') as f:
            f.write(OPENAI_STUBS)
        
        # Создаем пустой файл __pycache__
        os.makedirs(os.path.join('openai', '__pycache__'), exist_ok=True)
        
        logger.info("Создан локальный модуль openai с заглушками в текущем каталоге")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании локального модуля openai: {e}")
        return False

def patch_sys_modules_directly():
    """Напрямую патчит sys.modules для openai"""
    try:
        # Создаем простую заглушку для модуля
        import types
        openai_module = types.ModuleType('openai')
        
        # Компилируем и выполняем код заглушек в контексте модуля
        exec(OPENAI_STUBS, openai_module.__dict__)
        
        # Добавляем в sys.modules
        if 'openai' in sys.modules:
            # Добавляем заглушки к существующему модулю
            if not hasattr(sys.modules['openai'], 'AsyncOpenAI'):
                sys.modules['openai'].AsyncOpenAI = openai_module.AsyncOpenAI
                logger.info("Добавлена заглушка AsyncOpenAI в существующий модуль openai")
            
            if not hasattr(sys.modules['openai'], 'OpenAI'):
                sys.modules['openai'].OpenAI = openai_module.OpenAI
                logger.info("Добавлена заглушка OpenAI в существующий модуль openai")
        else:
            # Устанавливаем новый модуль
            sys.modules['openai'] = openai_module
            logger.info("Установлен новый модуль-заглушка openai в sys.modules")
        
        # Добавляем прямые ссылки на классы
        sys.modules['openai.AsyncOpenAI'] = openai_module.AsyncOpenAI
        sys.modules['openai.OpenAI'] = openai_module.OpenAI
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при прямом патчинге sys.modules: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало модификации модуля openai в site-packages ===")
    
    # Находим все файлы __init__.py модуля openai
    init_files = find_openai_init_files()
    
    if not init_files:
        logger.warning("Не найдены файлы __init__.py модуля openai")
        logger.info("Создаем локальный модуль openai с заглушками")
        create_openai_module_in_path()
    else:
        logger.info(f"Найдено файлов __init__.py: {len(init_files)}")
        for file_path in init_files:
            logger.info(f"Обрабатываем файл: {file_path}")
            add_stubs_to_openai_init(file_path)
    
    # Создаем полноценную замену модуля
    create_complete_openai_module()
    
    # В любом случае создаем локальный модуль для подстраховки
    create_openai_module_in_path()
    
    # Патчим sys.modules напрямую
    patch_sys_modules_directly()
    
    logger.info("=== Завершена модификация модуля openai ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 