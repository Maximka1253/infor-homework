import sqlite3
import csv

# Настройка БД
conn = sqlite3.connect('company.db')
cursor = conn.cursor()

# Создание таблиц
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS departments (id INTEGER PRIMARY KEY, name TEXT);
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY, 
        name TEXT, 
        salary INTEGER, 
        department_id INTEGER,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    );
''')

# Функция импорта
def import_csv(filename, table_name):
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Пропуск заголовка
        for row in reader:
            placeholders = ','.join(['?'] * len(row))
            cursor.execute(f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})", row)
    conn.commit()
    print(f"Файл {filename} импортирован.")

# Функция вывода
def run_query(query, title):
    print(f"\n>>> {title}")
    cursor.execute(query)
    columns = [d[0] for d in cursor.description]
    print(" | ".join(columns))
    print("-" * 30)
    for row in cursor.fetchall():
        print(" | ".join(map(str, row)))

# Импорт
import_csv('departments.csv', 'departments')
import_csv('employees.csv', 'employees')


# Пять простых запросов
run_query("SELECT COUNT(*) FROM employees", "1. Кол-во сотрудников")
run_query("SELECT MAX(salary) FROM employees", "2. Макс. зарплата")
run_query("SELECT SUM(salary) FROM employees", "3. Общий ФОТ")
run_query("SELECT AVG(salary) FROM employees", "4. Средняя зарплата")
run_query("SELECT name FROM employees WHERE salary > 50000", "5. ЗП > 50к")

# Три запроса с агрегацией
run_query("SELECT department_id, AVG(salary) FROM employees GROUP BY department_id", "Агрегация 1: Ср. ЗП по отделам")
run_query("SELECT department_id, COUNT(*) FROM employees GROUP BY department_id", "Агрегация 2: Кол-во людей по отделам")
run_query("SELECT department_id, SUM(salary) FROM employees GROUP BY department_id HAVING SUM(salary) > 50000", "Агрегация 3: ФОТ по отделам (>50к)")

# Три запроса с объединением (JOIN)
run_query("SELECT e.name, d.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'IT'", "JOIN 1: Сотрудники IT")
run_query("SELECT d.name, AVG(e.salary) FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.name", "JOIN 2: Ср. ЗП по отделам")
run_query("SELECT e.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE e.salary > 40000 AND d.name IN ('IT', 'Sales')", "JOIN 3: Высокая ЗП в IT и Sales")

conn.close()