import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('ona_bot.db')
cur = conn.cursor()

# Удаляем все записи из таблицы answers
print("Удаление всех ответов...")
cur.execute('DELETE FROM answers')
print(f"Удалено {cur.rowcount} записей из таблицы answers")

# Удаляем все записи из таблицы profiles
print("Удаление всех профилей...")
cur.execute('DELETE FROM profiles')
print(f"Удалено {cur.rowcount} записей из таблицы profiles")

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print("База данных успешно очищена от ответов и профилей.") 