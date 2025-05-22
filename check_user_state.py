import sqlite3
import json

# Подключаемся к базе данных
conn = sqlite3.connect('ona_bot.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Проверяем таблицы
print("=== Таблицы в базе данных ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
for table in tables:
    print(table['name'])

print("\n=== Пользователи ===")
cur.execute("SELECT * FROM users")
users = cur.fetchall()
for user in users:
    print(f"ID: {user['id']}, TG_ID: {user['tg_id']}")

# Проверим структуру таблицы profiles
print("\n=== Структура таблицы profiles ===")
cur.execute("PRAGMA table_info(profiles)")
columns = cur.fetchall()
for column in columns:
    print(f"{column['name']} ({column['type']})")

# Проверим профили
print("\n=== Профили ===")
cur.execute("SELECT id, user_id FROM profiles")
profiles = cur.fetchall()
for profile in profiles:
    print(f"ID: {profile['id']}, User ID: {profile['user_id']}")

# Проверим структуру таблицы fsm_data, если она существует
try:
    print("\n=== Структура таблицы FSM ===")
    cur.execute("PRAGMA table_info(fsm_data)")
    columns = cur.fetchall()
    if len(columns) > 0:
        for column in columns:
            print(f"{column['name']} ({column['type']})")
        
        # Проверим данные FSM
        print("\n=== Данные FSM ===")
        cur.execute("SELECT * FROM fsm_data")
        fsm_data = cur.fetchall()
        for data in fsm_data:
            print(f"Key: {data['key']}")
            try:
                value = json.loads(data['value'])
                print(f"Value: {json.dumps(value, indent=2)}")
            except:
                print(f"Value: {data['value']}")
    else:
        print("Таблица fsm_data не содержит столбцов")
except Exception as e:
    print(f"Ошибка при проверке FSM: {e}")

print("\n=== Поиск таблицы с FSM данными ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fsm%' OR name LIKE '%state%'")
tables = cur.fetchall()
for table in tables:
    print(f"Найдена таблица: {table['name']}")

# Закрываем соединение
conn.close() 