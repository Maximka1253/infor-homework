import sqlite3
from datetime import datetime


class StoreManager:
    # Класс хранит всю работу с базой данных, чтобы GUI не содержал SQL-запросы.
    def __init__(self, db_name="store.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        # Создаем таблицы, если база запускается впервые.
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id_category INTEGER PRIMARY KEY AUTOINCREMENT,
                name_category TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id_product INTEGER PRIMARY KEY AUTOINCREMENT,
                name_of_product TEXT NOT NULL,
                id_category INTEGER NOT NULL,
                price REAL NOT NULL CHECK (price > 0),
                quantity_at_storage INTEGER NOT NULL CHECK (quantity_at_storage >= 0),
                FOREIGN KEY (id_category) REFERENCES categories(id_category)
            );

            CREATE TABLE IF NOT EXISTS receipts (
                id_check INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id_sale INTEGER PRIMARY KEY AUTOINCREMENT,
                id_check INTEGER NOT NULL,
                id_product INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                price_at_sale REAL NOT NULL CHECK (price_at_sale > 0),
                FOREIGN KEY (id_check) REFERENCES receipts(id_check),
                FOREIGN KEY (id_product) REFERENCES products(id_product)
            );
        """)
        self.conn.commit()

    def get_or_create_category(self, name):
        # Если категория уже есть, используем ее id, иначе добавляем новую.
        row = self.conn.execute(
            "SELECT id_category FROM categories WHERE name_category = ?",
            (name,),
        ).fetchone()
        if row:
            return row["id_category"]

        cursor = self.conn.execute(
            "INSERT INTO categories (name_category) VALUES (?)",
            (name,),
        )
        return cursor.lastrowid

    def get_products(self):
        return self.conn.execute("""
            SELECT p.id_product, p.name_of_product, c.name_category,
                   p.price, p.quantity_at_storage
            FROM products p
            JOIN categories c ON c.id_category = p.id_category
            ORDER BY p.id_product
        """).fetchall()

    def add_product(self, name, category, price, quantity):
        if price <= 0 or quantity < 0:
            raise ValueError("Цена должна быть больше 0, остаток не меньше 0")

        if self.conn.execute(
            "SELECT 1 FROM products WHERE LOWER(name_of_product) = LOWER(?)",
            (name,),
        ).fetchone():
            raise ValueError("Такой товар уже есть")

        category_id = self.get_or_create_category(category)
        self.conn.execute("""
            INSERT INTO products (name_of_product, id_category, price, quantity_at_storage)
            VALUES (?, ?, ?, ?)
        """, (name, category_id, price, quantity))
        self.conn.commit()

    def sell(self, cart):
        if not cart:
            raise ValueError("Корзина пуста")

        # Продажа идет одной транзакцией: чек, товары в чеке и уменьшение остатков.
        with self.conn:
            receipt_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            receipt_id = self.conn.execute(
                "INSERT INTO receipts (created_at) VALUES (?)",
                (receipt_date,),
            ).lastrowid

            for product_id, quantity in cart.items():
                if quantity <= 0:
                    raise ValueError("Количество должно быть больше 0")

                product = self.conn.execute(
                    "SELECT * FROM products WHERE id_product = ?",
                    (product_id,),
                ).fetchone()

                if not product:
                    raise ValueError("Товар не найден")
                if product["quantity_at_storage"] < quantity:
                    raise ValueError(f"Недостаточно товара: {product['name_of_product']}")

                self.conn.execute("""
                    INSERT INTO sale_items (id_check, id_product, quantity, price_at_sale)
                    VALUES (?, ?, ?, ?)
                """, (receipt_id, product_id, quantity, product["price"]))

                self.conn.execute("""
                    UPDATE products
                    SET quantity_at_storage = quantity_at_storage - ?
                    WHERE id_product = ?
                """, (quantity, product_id))

        return self.get_receipt(receipt_id)

    def get_receipt(self, receipt_id):
        items = self.conn.execute("""
            SELECT r.id_check, r.created_at, p.name_of_product,
                   si.quantity, si.price_at_sale,
                   si.quantity * si.price_at_sale AS line_total
            FROM receipts r
            JOIN sale_items si ON si.id_check = r.id_check
            JOIN products p ON p.id_product = si.id_product
            WHERE r.id_check = ?
        """, (receipt_id,)).fetchall()

        return {
            "id": receipt_id,
            "date": items[0]["created_at"],
            "items": items,
            "total": sum(item["line_total"] for item in items),
        }

    def sales_report(self, report_date):
        # Отчет группирует продажи за выбранную дату по каждому товару.
        items = self.conn.execute("""
            SELECT p.name_of_product, c.name_category,
                   SUM(si.quantity) AS sold_quantity,
                   SUM(si.quantity * si.price_at_sale) AS revenue
            FROM receipts r
            JOIN sale_items si ON si.id_check = r.id_check
            JOIN products p ON p.id_product = si.id_product
            JOIN categories c ON c.id_category = p.id_category
            WHERE DATE(r.created_at) = DATE(?)
            GROUP BY p.id_product, p.name_of_product, c.name_category
            ORDER BY p.name_of_product
        """, (report_date,)).fetchall()

        total = self.conn.execute("""
            SELECT COALESCE(SUM(si.quantity * si.price_at_sale), 0)
            FROM receipts r
            JOIN sale_items si ON si.id_check = r.id_check
            WHERE DATE(r.created_at) = DATE(?)
        """, (report_date,)).fetchone()[0]

        return items, total