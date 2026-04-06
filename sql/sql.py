import sqlite3
import csv

#Настройка базы данных в памяти
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

#Создание таблиц
cursor.execute('CREATE TABLE employees (id INT, name TEXT, group_id INT, salary NUMERIC)')
cursor.execute('CREATE TABLE products (id INT, product TEXT, category TEXT, price NUMERIC)')
cursor.execute('CREATE TABLE sales (id INT, product_id INT, employee_id INT, quantity INT)')

# Загрузка данных из CSV
def load_to_sql(file_name, table_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        query = f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        cursor.executemany(query, [list(row.values()) for row in reader])

# Загрузка данных (файлы уже должны существовать)
load_to_sql('employees.csv', 'employees')
load_to_sql('products.csv', 'products')
load_to_sql('sales.csv', 'sales')

#1. Запросы с CASE
print("1. Запросы с CASE:")


cursor.execute('''
    SELECT name, salary, 
    CASE WHEN salary > 170000 THEN 'Высокая' WHEN salary > 155000 THEN 'Средняя' ELSE 'Базовая' END 
    FROM employees
''')
print("Уровни зарплат:", cursor.fetchall())

cursor.execute('''SELECT id, quantity, CASE WHEN quantity >= 3 THEN 'Опт' ELSE 'Розница' END FROM sales''')
print("Тип продаж:", cursor.fetchall())

cursor.execute('''SELECT product, CASE WHEN price > 50000 THEN 'Premium' WHEN price > 5000 THEN 'Business' ELSE 'Economy' END FROM products''')
print("Сегменты товаров:", cursor.fetchall())


# подзапросы
print("\n2. Подзапросы")

cursor.execute('SELECT product, price FROM products WHERE price > (SELECT AVG(price) FROM products)')
print("Дороже среднего:", cursor.fetchall())

cursor.execute('SELECT name FROM employees WHERE id IN (SELECT employee_id FROM sales)')
print("Активные продавцы:", cursor.fetchall())

cursor.execute('SELECT product FROM products WHERE price = (SELECT MIN(price) FROM products)')
print("Самый дешевый:", cursor.fetchall(),)


#CTE
print("\n3. Запросы с CTE:")

cursor.execute('''
    WITH SaleDetails AS (
        SELECT s.id, p.product, (s.quantity * p.price) as total_sum
        FROM sales s JOIN products p ON s.product_id = p.id
    )
    SELECT * FROM SaleDetails WHERE total_sum > 10000
''')
print("Крупные сделки:", cursor.fetchall())

cursor.execute('''
    WITH DeptStats AS (
        SELECT group_id, AVG(salary) as avg_sal, COUNT(*) as emp_count
        FROM employees GROUP BY group_id
    )
    SELECT * FROM DeptStats WHERE emp_count > 1
''')
print("Статистика по группам:", cursor.fetchall())

cursor.execute('''
    WITH EmpSales AS (
        SELECT employee_id, SUM(quantity) as total_qty FROM sales GROUP BY employee_id
    )
    SELECT e.name, es.total_qty FROM employees e JOIN EmpSales es ON e.id = es.employee_id
''')
print("Итоги продаж по именам:", cursor.fetchall())

conn.close()