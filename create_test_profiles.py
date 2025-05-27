import json
import os

# Создаем тестовые профили
profiles = {
    "123456789": {
        "answers": {
            "name": "Test User",
            "age": "30",
            "birthdate": "01.01.1990",
            "birthplace": "Test City",
            "timezone": "UTC+3"
        },
        "profile_completed": True,
        "profile_text": "This is a test profile for the persistence functionality.",
        "profile_details": "This is a detailed test profile for the persistence functionality.",
        "personality_type": "Интеллектуальный",
        "secondary_type": "Творческий",
        "type_counts": {
            "A": 10,
            "B": 5,
            "C": 8,
            "D": 7
        }
    },
    "987654321": {
        "answers": {
            "name": "New Test User",
            "age": "25",
            "birthdate": "01.01.1995",
            "birthplace": "Test City 2",
            "timezone": "UTC+4"
        },
        "profile_completed": True,
        "profile_text": "This is a new test profile for the persistence functionality.",
        "profile_details": "This is a detailed new test profile for the persistence functionality.",
        "personality_type": "Эмоциональный",
        "secondary_type": "Практический",
        "type_counts": {
            "A": 5,
            "B": 10,
            "C": 7,
            "D": 8
        }
    }
}

# Путь к файлу
file_path = "user_profiles.json"

# Сохраняем профили в файл
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(profiles, f, ensure_ascii=False, indent=4)

print(f"Файл {file_path} обновлен. Добавлено {len(profiles)} профилей.")

# Проверяем содержимое файла
print(f"\nСодержимое файла {file_path}:")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)

print(f"\nРазмер файла: {os.path.getsize(file_path)} байт") 