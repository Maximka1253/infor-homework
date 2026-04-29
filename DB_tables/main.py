import sqlite3

# 1 Создание подключения и базы данных
conn = sqlite3.connect('my_database.db')
cursor = conn.cursor()

# Создание таблиц
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS Должности (
        Код_должности INTEGER PRIMARY KEY,
        Название TEXT
    );
    CREATE TABLE IF NOT EXISTS Клиенты (
        Код_клиента INTEGER PRIMARY KEY,
        Организация TEXT,
        Телефон TEXT
    );
    CREATE TABLE IF NOT EXISTS Сотрудники (
        Код_сотрудника INTEGER PRIMARY KEY,
        Фамилия TEXT,
        Имя TEXT,
        Телефон TEXT,
        Код_должности INTEGER,
        FOREIGN KEY (Код_должности) REFERENCES Должности(Код_должности)
    );
    CREATE TABLE IF NOT EXISTS Заказы (
        Код_заказа INTEGER PRIMARY KEY,
        Код_клиента INTEGER,
        Код_сотрудника INTEGER,
        Сумма REAL,
        Дата_выполнения TEXT,
        Отметка_о_выполнении INTEGER,
        FOREIGN KEY (Код_клиента) REFERENCES Клиенты(Код_клиента),
        FOREIGN KEY (Код_сотрудника) REFERENCES Сотрудники(Код_сотрудника)
    );
''')

# 2 Заполнение таблиц (пример)
cursor.execute("INSERT OR IGNORE INTO Должности VALUES (1, 'Менеджер')")
cursor.execute("INSERT OR IGNORE INTO Клиенты VALUES (1, 'ООО Ромашка', '555-0101')")
cursor.execute("INSERT OR IGNORE INTO Сотрудники VALUES (1, 'Иванов', 'Иван', '123-456', 1)")
cursor.execute("INSERT OR IGNORE INTO Заказы VALUES (1, 1, 1, 15000.0, '2026-04-20', 1)")
conn.commit()

# 3 Примеры запросов
def run_query(query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()

print(" Простой запрос (Все сотрудники) ")
print(run_query("SELECT * FROM Сотрудники"))

print("\n Запрос с параметром (Заказы сотрудника с ID 1) ")
print(run_query("SELECT * FROM Заказы WHERE Код_сотрудника = ?", (1,)))

print("\n Запрос с группировкой (Сумма заказов по сотруднику) ")
print(run_query("SELECT Код_сотрудника, SUM(Сумма) FROM Заказы GROUP BY Код_сотрудника"))

conn.close()