import sqlite3
import csv

# Подключение к базе данных
conn = sqlite3.connect("university.db")
cur = conn.cursor()

# Создание таблиц
cur.executescript("""
    CREATE TABLE IF NOT EXISTS уровень_обучения (id_уровня INTEGER PRIMARY KEY, название VARCHAR(100));
    CREATE TABLE IF NOT EXISTS направления (id_направления INTEGER PRIMARY KEY, название VARCHAR(100));
    CREATE TABLE IF NOT EXISTS типы_обучения (id_типа INTEGER PRIMARY KEY, название VARCHAR(100));
    CREATE TABLE IF NOT EXISTS студенты (
        id_студента INTEGER PRIMARY KEY,
        id_уровня INTEGER,
        id_направления INTEGER,
        id_типа_обучения INTEGER,
        фамилия VARCHAR(100),
        имя VARCHAR(100),
        отчество VARCHAR(100),
        средний_балл INTEGER
    );
""")

# Функция импорта
def import_csv(file_name, insert_query):
    with open(file_name, encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # пропуск заголовка
        cur.executemany(insert_query, reader)

# Загрузка данных
import_csv('levels.csv', "INSERT OR IGNORE INTO уровень_обучения VALUES (?, ?)")
import_csv('majors.csv', "INSERT OR IGNORE INTO направления VALUES (?, ?)")
import_csv('types.csv', "INSERT OR IGNORE INTO типы_обучения VALUES (?, ?)")
import_csv('students.csv', "INSERT OR IGNORE INTO студенты VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
conn.commit()

# Вспомогательная функция для вывода отчетов
def report(title, sql):
    print(f"\n>>> {title}")
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print(" | ".join(f"{c:15}" for c in cols))
    print("-" * 80)
    for row in rows:
        print(" | ".join(f"{str(v):15}" for v in row))


report("1. Общее количество студентов", "SELECT COUNT(*) AS всего FROM студенты")

report("2. Студенты по направлениям", """
    SELECT n.название, COUNT(*) as кол_во 
    FROM студенты s JOIN направления n ON s.id_направления = n.id_направления 
    GROUP BY n.название
""")

report("3. По формам обучения", """
    SELECT t.название, COUNT(*) as кол_во 
    FROM студенты s JOIN типы_обучения t ON s.id_типа_обучения = t.id_типа 
    GROUP BY t.название
""")

report("4. Баллы по направлениям", """
    SELECT n.название, MAX(средний_балл), MIN(средний_балл), ROUND(AVG(средний_балл), 2)
    FROM студенты s JOIN направления n ON s.id_направления = n.id_направления 
    GROUP BY n.название
""")

report("5. Средний балл (направление/уровень/форма)", """
    SELECT n.название as напр, l.название as ур, t.название as форма, ROUND(AVG(средний_балл), 2) as ср_балл
    FROM студенты s
    JOIN направления n ON s.id_направления = n.id_направления
    JOIN уровень_обучения l ON s.id_уровня = l.id_уровня
    JOIN типы_обучения t ON s.id_типа_обучения = t.id_типа
    GROUP BY 1, 2, 3
""")

report("6. Топ-5 Пр. Информатика (Очная)", """
    SELECT фамилия, имя, средний_балл 
    FROM студенты s
    JOIN направления n ON s.id_направления = n.id_направления
    JOIN типы_обучения t ON s.id_типа_обучения = t.id_типа
    WHERE n.название = 'Прикладная Информатика' AND t.название = 'Очная'
    ORDER BY средний_балл DESC LIMIT 5
""")

report("7. Однофамильцы", "SELECT фамилия, COUNT(*) FROM студенты GROUP BY фамилия HAVING COUNT(*) > 1")

report("8. Полные тезки", "SELECT фамилия, имя, отчество, COUNT(*) FROM студенты GROUP BY 1,2,3 HAVING COUNT(*) > 1")