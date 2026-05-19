import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from database import StoreManager


RECEIPTS_DIR = Path("receipts")


class StoreApp:
    # Класс отвечает только за окно, кнопки, таблицы и действия пользователя.
    def __init__(self, root):
        self.root = root
        self.root.title("Магазин")
        self.root.geometry("1000x620")
        self.root.configure(bg="#000000")

        self.store = StoreManager()
        self.cart = {}
        self.products_cache = {}

        self.setup_style()
        self.setup_ui()
        self.load_products()

    def setup_style(self):
        # Единая темная тема для элементов интерфейса.
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#000000"
        field = "#080808"
        border = "#2a2a2a"
        text = "#eeeeee"
        muted = "#b0b0b0"

        style.configure(".", background=bg, foreground=text, fieldbackground=field, font=("Segoe UI", 10))
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=text)
        style.configure("TButton", background=field, foreground=text, bordercolor=border, padding=6)
        style.map("TButton", background=[("active", "#111111")], foreground=[("active", text)])
        style.configure("TEntry", fieldbackground=field, foreground=text, bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TSpinbox", fieldbackground=field, foreground=text, bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=bg, foreground=muted, padding=(12, 6), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", field)], foreground=[("selected", text)])
        style.configure("Treeview", background=field, foreground=text, fieldbackground=field, bordercolor=border, rowheight=34)
        style.configure("Treeview.Heading", background="#000000", foreground=muted, bordercolor=border)
        style.map("Treeview", background=[("selected", "#1a1a1a")], foreground=[("selected", text)])

    def setup_ui(self):
        # Главное окно состоит из двух вкладок: продажа и отчет.
        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        sale_tab = ttk.Frame(tabs)
        report_tab = ttk.Frame(tabs)
        tabs.add(sale_tab, text="Продажа")
        tabs.add(report_tab, text="Отчет")

        self.setup_sale_tab(sale_tab)
        self.setup_report_tab(report_tab)

    def setup_sale_tab(self, tab):
        # Слева список товаров и управление складом, справа корзина покупателя.
        tab.columnconfigure(0, weight=3)
        tab.columnconfigure(1, weight=2)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        self.products_table = self.create_table(left, ("ID", "Название", "Категория", "Цена", "Остаток"), 0, 0)
        self.products_table.bind("<Double-1>", self.add_selected_product)
        self.products_table.bind("<<TreeviewSelect>>", self.fill_product_fields)

        product_controls = ttk.Frame(left)
        product_controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.add_fields(product_controls, (
            ("new_name_entry", "entry", "Название", 0, 0, {"width": 14}),
            ("new_category_entry", "entry", "Категория", 0, 2, {"width": 14}),
            ("new_price_entry", "entry", "Цена", 1, 0),
            ("new_quantity_entry", "entry", "Остаток", 1, 2),
        ))
        self.add_buttons(product_controls, (
            ("Новый товар", self.add_new_product, 1, 4),
        ))

        right = ttk.Frame(tab)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.cart_table = self.create_table(right, ("Товар", "Кол-во", "Цена", "Сумма"), 0, 0)

        controls = ttk.Frame(right)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.product_id_entry = self.add_entry(controls, "ID", 0, 0)
        self.quantity_spinbox = self.add_spinbox(controls, "Кол-во", 0, 2)

        self.add_buttons(controls, (
            ("Добавить", self.add_by_id, 0, 4),
            ("Удалить", self.remove_from_cart, 1, 0),
            ("Очистить", self.clear_cart, 1, 1),
            ("Оплатить", self.pay, 1, 2),
        ))

        self.total_label = ttk.Label(controls, text="Сумма: 0.00", font=("Segoe UI", 12, "bold"))
        self.total_label.grid(row=2, column=0, columnspan=5, sticky="e", pady=(8, 0))

    def setup_report_tab(self, tab):
        # Вкладка показывает продажи и выручку за выбранную дату.
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(top, text="Дата").pack(side="left")
        self.report_date_entry = ttk.Entry(top, width=14)
        self.report_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.report_date_entry.pack(side="left", padx=8)
        ttk.Button(top, text="Показать", command=self.load_report).pack(side="left")

        self.report_table = self.create_table(tab, ("Товар", "Категория", "Продано", "Выручка"), 1, 0)

        self.report_total_label = ttk.Label(tab, text="Выручка за дату: 0.00", font=("Segoe UI", 12, "bold"))
        self.report_total_label.grid(row=2, column=0, sticky="e", pady=(10, 0))

    def create_table(self, parent, columns, row, column):
        table = ttk.Treeview(parent, columns=columns, show="headings")
        for name in columns:
            table.heading(name, text=name)
            table.column(name, anchor="center", width=120)
        table.grid(row=row, column=column, sticky="nsew")
        return table

    def add_entry(self, parent, label, row, column, width=8, pady=4):
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=4, pady=pady)
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=column + 1, padx=4, pady=pady)
        return entry

    def add_spinbox(self, parent, label, row, column):
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=4, pady=4)
        spinbox = ttk.Spinbox(parent, from_=1, to=1000, width=8)
        spinbox.set(1)
        spinbox.grid(row=row, column=column + 1, padx=4, pady=4)
        return spinbox

    def add_button(self, parent, text, command, row, column):
        ttk.Button(parent, text=text, command=command).grid(row=row, column=column, padx=4, pady=4)

    def add_fields(self, parent, fields):
        factories = {"entry": self.add_entry, "spinbox": self.add_spinbox}
        for attr, kind, label, row, column, *options in fields:
            setattr(self, attr, factories[kind](parent, label, row, column, **(options[0] if options else {})))

    def add_buttons(self, parent, buttons):
        for text, command, row, column in buttons:
            self.add_button(parent, text, command, row, column)

    def load_products(self):
        # Обновляем таблицу товаров и кеш для быстрого доступа по id.
        self.clear_table(self.products_table)
        self.products_cache.clear()

        for product in self.store.get_products():
            product_id = product["id_product"]
            self.products_cache[product_id] = product
            self.products_table.insert("", "end", values=(
                product_id, product["name_of_product"], product["name_category"],
                self.money(product["price"]), product["quantity_at_storage"],
            ))

    def add_selected_product(self, _event=None):
        selected = self.products_table.selection()
        if selected:
            product_id = int(self.products_table.item(selected[0], "values")[0])
            self.add_to_cart(product_id, 1)

    def fill_product_fields(self, _event=None):
        selected = self.products_table.selection()
        if not selected:
            return

        values = self.products_table.item(selected[0], "values")
        self.set_entry(self.product_id_entry, values[0])

    def add_by_id(self):
        try:
            product_id = self.get_int(self.product_id_entry, "ID товара")
            quantity = self.get_int(self.quantity_spinbox, "Количество")
            self.add_to_cart(product_id, quantity)
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))

    def add_to_cart(self, product_id, quantity):
        # В корзину нельзя добавить больше, чем есть на складе.
        if quantity <= 0:
            messagebox.showerror("Ошибка", "Количество должно быть больше 0")
            return

        product = self.products_cache.get(product_id)
        if not product:
            messagebox.showerror("Ошибка", "Товар не найден")
            return

        new_quantity = self.cart.get(product_id, 0) + quantity
        if new_quantity > product["quantity_at_storage"]:
            messagebox.showerror("Ошибка", "Недостаточно товара на складе")
            return

        self.cart[product_id] = new_quantity
        self.update_cart()

    def update_cart(self):
        self.clear_table(self.cart_table)
        total = 0

        for product_id, quantity in self.cart.items():
            product = self.products_cache[product_id]
            line_total = product["price"] * quantity
            total += line_total
            self.cart_table.insert("", "end", tags=(product_id,), values=(
                product["name_of_product"], quantity, self.money(product["price"]), self.money(line_total),
            ))

        self.total_label.config(text=f"Сумма: {self.money(total)}")

    def remove_from_cart(self):
        selected = self.cart_table.selection()
        if selected:
            product_id = int(self.cart_table.item(selected[0], "tags")[0])
            self.cart.pop(product_id)
            self.update_cart()

    def clear_cart(self):
        self.cart.clear()
        self.update_cart()

    def pay(self):
        # После оплаты показываем чек и обновляем остатки на экране.
        try:
            receipt = self.store.sell(self.cart)
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))
            return

        self.show_receipt(receipt)
        self.cart.clear()
        self.update_cart()
        self.load_products()
        self.load_report()

    def add_new_product(self):
        name = self.new_name_entry.get().strip()
        category = self.new_category_entry.get().strip()

        try:
            price = self.get_float(self.new_price_entry, "Цена")
            quantity = self.get_int(self.new_quantity_entry, "Остаток")

            if not name or not category:
                raise ValueError("Заполните название и категорию")
            self.store.add_product(name, category, price, quantity)
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))
            return

        self.clear_entries(
            self.new_name_entry,
            self.new_category_entry,
            self.new_price_entry,
            self.new_quantity_entry,
        )
        self.load_products()
        messagebox.showinfo("Готово", "Товар добавлен")

    def load_report(self):
        report_date = self.report_date_entry.get()
        items, total = self.store.sales_report(report_date)
        self.clear_table(self.report_table)

        for item in items:
            self.report_table.insert("", "end", values=(
                item["name_of_product"], item["name_category"], item["sold_quantity"], self.money(item["revenue"]),
            ))

        self.report_total_label.config(text=f"Выручка за дату: {self.money(total)}")

    def show_receipt(self, receipt):
        # Чек показывается в отдельном окне и сохраняется в текстовый файл.
        lines = [
            "===== ЧЕК =====",
            f"ID чека: {receipt['id']}",
            f"Дата: {receipt['date']}",
            "---------------------",
        ]

        for item in receipt["items"]:
            lines.append(
                f"{item['name_of_product']} x{item['quantity']} = {self.money(item['line_total'])}"
            )

        lines += ["---------------------", f"ИТОГО: {self.money(receipt['total'])}"]
        text = "\n".join(lines)

        RECEIPTS_DIR.mkdir(exist_ok=True)
        receipt_path = RECEIPTS_DIR / f"receipt_{receipt['id']}.txt"
        with open(receipt_path, "w", encoding="utf-8") as file:
            file.write(text)

        window = tk.Toplevel(self.root)
        window.title("Чек")
        window.configure(bg="#000000")

        receipt_text = tk.Text(window, bg="#080808", fg="#eeeeee", insertbackground="#eeeeee", font=("Consolas", 11))
        receipt_text.insert("1.0", text)
        receipt_text.config(state="disabled")
        receipt_text.pack(fill="both", expand=True, padx=10, pady=10)

    @staticmethod
    def money(value):
        return f"{float(value):.2f}"

    @staticmethod
    def clear_table(table):
        table.delete(*table.get_children())

    @staticmethod
    def set_entry(entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    @staticmethod
    def get_int(entry, field_name):
        return StoreApp.get_number(entry, field_name, int, "целое число")

    @staticmethod
    def get_float(entry, field_name):
        return StoreApp.get_number(entry, field_name, float, "число")

    @staticmethod
    def get_number(entry, field_name, converter, type_name):
        try:
            return converter(entry.get())
        except ValueError:
            raise ValueError(f"{field_name}: введите {type_name}")

    @staticmethod
    def clear_entries(*entries):
        for entry in entries:
            entry.delete(0, tk.END)