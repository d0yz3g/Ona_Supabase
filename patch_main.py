#!/usr/bin/env python3
"""
Патч для файла main.py, который добавляет импорт pre_import_fix в самое начало файла.
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("patch_main")

def patch_main_py():
    """Добавляет import pre_import_fix в начало файла main.py"""
    # Проверяем наличие файла main.py
    if not os.path.exists("main.py"):
        logger.error("Файл main.py не найден")
        return False
    
    # Читаем содержимое файла
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Проверяем, есть ли уже импорт pre_import_fix
    if "import pre_import_fix" in content:
        logger.info("Импорт pre_import_fix уже присутствует в main.py")
        return True
    
    # Создаем резервную копию файла
    with open("main.py.bak", "w", encoding="utf-8") as f:
        f.write(content)
    
    # Добавляем импорт в начало файла
    import_line = 'import pre_import_fix  # Фикс для AsyncOpenAI\n'
    
    # Находим первую строку с импортом
    lines = content.split("\n")
    import_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_index = i
            break
    
    if import_index == -1:
        # Если импортов нет, добавляем в начало файла
        new_content = import_line + content
    else:
        # Вставляем перед первым импортом
        lines.insert(import_index, import_line)
        new_content = "\n".join(lines)
    
    # Записываем обновленное содержимое
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    logger.info("Файл main.py успешно модифицирован, добавлен импорт pre_import_fix")
    return True

if __name__ == "__main__":
    if patch_main_py():
        print("✅ Файл main.py успешно пропатчен")
        sys.exit(0)
    else:
        print("❌ Не удалось пропатчить файл main.py")
        sys.exit(1) 