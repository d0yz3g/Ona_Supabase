import sqlite3
import json

# Подключаемся к базе данных
conn = sqlite3.connect('ona_bot.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Выводим информацию о профилях
print("=== Профили ===")
cur.execute('SELECT id, user_id FROM profiles')
profiles = cur.fetchall()
for profile in profiles:
    print(f"ID: {profile['id']}, User ID: {profile['user_id']}")

# Выводим информацию о оценках в профилях
print("\n=== Оценки в профилях ===")
cur.execute('SELECT id, user_id, summary_json FROM profiles')
profiles = cur.fetchall()
for profile in profiles:
    data = json.loads(profile['summary_json'])
    print(f"Профиль ID: {profile['id']}, User ID: {profile['user_id']}")
    if 'scores' in data:
        print("Оценки:", data['scores'])
    else:
        print("Оценки отсутствуют")
    print()

# Выводим информацию о ответах на вопросы о сильных сторонах
print("\n=== Ответы на вопросы о сильных сторонах ===")
cur.execute('SELECT user_id, question_id, answer_text FROM answers WHERE question_id LIKE "strength%"')
answers = cur.fetchall()
answers_by_user = {}
for answer in answers:
    user_id = answer['user_id']
    if user_id not in answers_by_user:
        answers_by_user[user_id] = []
    answers_by_user[user_id].append((answer['question_id'], answer['answer_text']))

for user_id, user_answers in answers_by_user.items():
    print(f"User ID: {user_id}")
    print(f"Количество ответов: {len(user_answers)}")
    print("Примеры ответов:")
    for i, (question_id, answer_text) in enumerate(user_answers[:5]):
        print(f"  {question_id}: {answer_text}")
    if len(user_answers) > 5:
        print(f"  ... и еще {len(user_answers) - 5} ответов")
    print()

# Проверяем категории вопросов
print("\n=== Категории вопросов ===")
from questions import get_strength_questions
strength_questions = get_strength_questions()
categories = {}
for question in strength_questions:
    category = question.get('category')
    if category not in categories:
        categories[category] = []
    categories[category].append(question['id'])

for category, question_ids in categories.items():
    print(f"Категория: {category}")
    print(f"Количество вопросов: {len(question_ids)}")
    print("Примеры вопросов:", ', '.join(question_ids[:3]))
    print()

# Закрываем соединение
conn.close() 