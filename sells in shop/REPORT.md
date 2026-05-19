# Отчет по базе данных магазина

Проект разделен на несколько файлов:

- `shop.py` - запуск приложения;
- `gui.py` - графический интерфейс;
- `database.py` - работа с базой данных и SQL-запросы.

## Схема данных

```sql
CREATE TABLE categories (
    id_category INTEGER PRIMARY KEY AUTOINCREMENT,
    name_category TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id_product INTEGER PRIMARY KEY AUTOINCREMENT,
    name_of_product TEXT NOT NULL,
    id_category INTEGER NOT NULL,
    price REAL NOT NULL CHECK (price > 0),
    quantity_at_storage INTEGER NOT NULL CHECK (quantity_at_storage >= 0),
    FOREIGN KEY (id_category) REFERENCES categories(id_category)
);

CREATE TABLE receipts (
    id_check INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL
);

CREATE TABLE sale_items (
    id_sale INTEGER PRIMARY KEY AUTOINCREMENT,
    id_check INTEGER NOT NULL,
    id_product INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_at_sale REAL NOT NULL CHECK (price_at_sale > 0),
    FOREIGN KEY (id_check) REFERENCES receipts(id_check),
    FOREIGN KEY (id_product) REFERENCES products(id_product)
);
```

## Основные запросы

Список товаров с категориями:

```sql
SELECT
    p.id_product,
    p.name_of_product,
    c.name_category,
    p.price,
    p.quantity_at_storage
FROM products p
JOIN categories c ON c.id_category = p.id_category
ORDER BY p.id_product;
```

Поиск категории по названию:

```sql
SELECT id_category
FROM categories
WHERE name_category = :name_category;
```

Добавление новой категории:

```sql
INSERT INTO categories (name_category)
VALUES (:name_category);
```

Добавление нового товара:

```sql
INSERT INTO products (name_of_product, id_category, price, quantity_at_storage)
VALUES (:name, :id_category, :price, :quantity);
```

Проверка товара и количества на складе перед продажей:

```sql
SELECT *
FROM products
WHERE id_product = :id_product;
```

Создание чека:

```sql
INSERT INTO receipts (created_at)
VALUES (:created_at);
```

Добавление товара в чек:

```sql
INSERT INTO sale_items (id_check, id_product, quantity, price_at_sale)
VALUES (:id_check, :id_product, :quantity, :price_at_sale);
```

Уменьшение остатка после продажи:

```sql
UPDATE products
SET quantity_at_storage = quantity_at_storage - :quantity
WHERE id_product = :id_product;
```

Получение состава чека и стоимости покупки:

```sql
SELECT
    r.id_check,
    r.created_at,
    p.name_of_product,
    si.quantity,
    si.price_at_sale,
    si.quantity * si.price_at_sale AS line_total
FROM receipts r
JOIN sale_items si ON si.id_check = r.id_check
JOIN products p ON p.id_product = si.id_product
WHERE r.id_check = :id_check;
```

Количество каждого проданного товара и выручка за выбранную дату:

```sql
SELECT
    p.name_of_product,
    c.name_category,
    SUM(si.quantity) AS sold_quantity,
    SUM(si.quantity * si.price_at_sale) AS revenue
FROM receipts r
JOIN sale_items si ON si.id_check = r.id_check
JOIN products p ON p.id_product = si.id_product
JOIN categories c ON c.id_category = p.id_category
WHERE DATE(r.created_at) = DATE(:report_date)
GROUP BY p.id_product, p.name_of_product, c.name_category
ORDER BY p.name_of_product;
```

Выручка за выбранную дату:

```sql
SELECT COALESCE(SUM(si.quantity * si.price_at_sale), 0) AS total_revenue
FROM receipts r
JOIN sale_items si ON si.id_check = r.id_check
WHERE DATE(r.created_at) = DATE(:report_date);
```