import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import os
import shutil
import calendar
from datetime import datetime


# =========================================================
# SETTINGS
# =========================================================

APP_NAME = "Shop Management System"

BG_DARK = "#0B1220"
CARD_DARK = "#111827"
CARD_LIGHT_DARK = "#172033"
TEXT_DARK = "#F8FAFC"
MUTED_DARK = "#94A3B8"
BORDER_DARK = "#263449"
BLUE = "#3B82F6"
BLUE_HOVER = "#2563EB"

BG_LIGHT = "#F3F4F6"
CARD_LIGHT = "#FFFFFF"
CARD_LIGHTER = "#F8FAFC"
TEXT_LIGHT = "#111827"
MUTED_LIGHT = "#64748B"
BORDER_LIGHT = "#D1D5DB"

DB_PATH = os.path.join("database", "shop.db")


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    os.makedirs("database", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def add_column_if_missing(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin'
        )
    """)

    # PRODUCTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            color TEXT,
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            date_added TEXT
        )
    """)

    # Existing old database compatibility
    add_column_if_missing(cursor, "products", "category", "TEXT")
    add_column_if_missing(cursor, "products", "color", "TEXT")
    add_column_if_missing(cursor, "products", "purchase_price", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "products", "selling_price", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "products", "date_added", "TEXT")

    # CUSTOMERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT
        )
    """)

    # SALES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            date TEXT,
            time TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            remaining REAL DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # SALE ITEMS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_code TEXT,
            quantity INTEGER,
            price REAL,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        )
    """)

    # PAYMENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            sale_id INTEGER,
            amount REAL DEFAULT 0,
            date TEXT,
            time TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        )
    """)

    # OLD DATABASE FIX
    add_column_if_missing(cursor, "payments", "customer_id", "INTEGER")
    add_column_if_missing(cursor, "payments", "sale_id", "INTEGER")
    add_column_if_missing(cursor, "payments", "amount", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "payments", "date", "TEXT")
    add_column_if_missing(cursor, "payments", "time", "TEXT")

    # EXPENSES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL DEFAULT 0,
            date TEXT,
            note TEXT DEFAULT ''
        )
    """)

    # DEFAULT ADMIN
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", "admin123", "admin"))

    connection.commit()
    connection.close()


# =========================================================
# GLOBAL THEME
# =========================================================

current_mode = "dark"


def colors():
    if current_mode == "dark":
        return {
            "bg": BG_DARK,
            "card": CARD_DARK,
            "card2": CARD_LIGHT_DARK,
            "text": TEXT_DARK,
            "muted": MUTED_DARK,
            "border": BORDER_DARK
        }

    return {
        "bg": BG_LIGHT,
        "card": CARD_LIGHT,
        "card2": CARD_LIGHTER,
        "text": TEXT_LIGHT,
        "muted": MUTED_LIGHT,
        "border": BORDER_LIGHT
    }


# =========================================================
# MAIN WINDOW
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title(APP_NAME)
window.geometry("1250x750")
window.minsize(1050, 650)


# =========================================================
# HELPERS
# =========================================================

def clear_window():
    for widget in window.winfo_children():
        widget.destroy()


def create_label(parent, text, size=14, bold=False):
    c = colors()

    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(
            size=size,
            weight="bold" if bold else "normal"
        ),
        text_color=c["text"]
    )


def create_entry(parent, placeholder="", width=250):
    c = colors()

    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width,
        height=40,
        fg_color=c["card2"],
        border_color=c["border"],
        text_color=c["text"]
    )


def create_button(parent, text, command, width=150):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=40,
        fg_color=BLUE,
        hover_color=BLUE_HOVER
    )


# =========================================================
# DATE CALENDAR
# =========================================================

def create_date_picker(parent, width=180, placeholder="Date YYYY-MM-DD"):
    """
    Date entry with calendar.
    User can either type YYYY-MM-DD manually
    or select Year -> Month -> Date from calendar.
    """

    frame = ctk.CTkFrame(
        parent,
        fg_color="transparent"
    )

    entry = create_entry(
        frame,
        placeholder,
        width
    )
    entry.pack(
        side="left",
        padx=(0, 5)
    )

    def open_calendar():

        c = colors()

        win = ctk.CTkToplevel(window)
        win.title("Select Date")
        win.geometry("430x500")
        win.resizable(False, False)
        win.grab_set()

        main_frame = ctk.CTkFrame(
            win,
            fg_color=c["card"],
            corner_radius=15
        )
        main_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        create_label(
            main_frame,
            "Select Date",
            22,
            True
        ).pack(
            pady=(20, 15)
        )

        # -------------------------------------------------
        # YEAR
        # -------------------------------------------------

        create_label(
            main_frame,
            "1. Select Year",
            14,
            True
        ).pack(
            pady=(5, 5)
        )

        current_year = datetime.now().year

        years = [
            str(year)
            for year in range(
                current_year - 10,
                current_year + 11
            )
        ]

        year_var = ctk.StringVar(
            value=str(current_year)
        )

        year_menu = ctk.CTkOptionMenu(
            main_frame,
            variable=year_var,
            values=years,
            width=250,
            height=40
        )
        year_menu.pack(
            pady=(0, 15)
        )

        # -------------------------------------------------
        # MONTH
        # -------------------------------------------------

        create_label(
            main_frame,
            "2. Select Month",
            14,
            True
        ).pack(
            pady=(5, 5)
        )

        months = [
            "01 - January",
            "02 - February",
            "03 - March",
            "04 - April",
            "05 - May",
            "06 - June",
            "07 - July",
            "08 - August",
            "09 - September",
            "10 - October",
            "11 - November",
            "12 - December"
        ]

        month_var = ctk.StringVar(
            value=months[datetime.now().month - 1]
        )

        month_menu = ctk.CTkOptionMenu(
            main_frame,
            variable=month_var,
            values=months,
            width=250,
            height=40
        )
        month_menu.pack(
            pady=(0, 15)
        )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        create_label(
            main_frame,
            "3. Select Date",
            14,
            True
        ).pack(
            pady=(5, 8)
        )

        days_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        days_frame.pack(
            fill="x",
            padx=20
        )

        def refresh_days(*args):

            for widget in days_frame.winfo_children():
                widget.destroy()

            try:
                selected_year = int(
                    year_var.get()
                )

                selected_month = int(
                    month_var.get().split(" ")[0]
                )

                days_in_month = calendar.monthrange(
                    selected_year,
                    selected_month
                )[1]

                for day in range(
                    1,
                    days_in_month + 1
                ):

                    row = (day - 1) // 7
                    col = (day - 1) % 7

                    ctk.CTkButton(
                        days_frame,
                        text=str(day),
                        width=42,
                        height=32,
                        command=lambda d=day:
                        select_date(
                            selected_year,
                            selected_month,
                            d
                        )
                    ).grid(
                        row=row,
                        column=col,
                        padx=3,
                        pady=3
                    )

            except Exception:
                pass

        def select_date(year, month, day):

            selected_date = (
                f"{year:04d}-{month:02d}-{day:02d}"
            )

            entry.delete(
                0,
                "end"
            )

            entry.insert(
                0,
                selected_date
            )

            win.destroy()

        year_var.trace_add(
            "write",
            refresh_days
        )

        month_var.trace_add(
            "write",
            refresh_days
        )

        refresh_days()

        ctk.CTkButton(
            main_frame,
            text="Cancel",
            command=win.destroy,
            width=150,
            height=38
        ).pack(
            pady=15
        )

    ctk.CTkButton(
        frame,
        text="📅",
        command=open_calendar,
        width=45,
        height=40
    ).pack(
        side="left"
    )

    return frame, entry


def backup_database():
    if not os.path.exists(DB_PATH):
        messagebox.showerror("Error", "Database not found.")
        return

    os.makedirs("backups", exist_ok=True)

    filename = datetime.now().strftime(
        "backup_%Y-%m-%d_%H-%M-%S.db"
    )

    destination = os.path.join("backups", filename)

    shutil.copy2(DB_PATH, destination)

    messagebox.showinfo(
        "Backup",
        f"Backup created successfully.\n\n{destination}"
    )


# =========================================================
# LOGIN
# =========================================================

def show_login():

    clear_window()

    c = colors()

    window.configure(fg_color=c["bg"])

    frame = ctk.CTkFrame(
        window,
        width=430,
        height=500,
        fg_color=c["card"],
        corner_radius=20
    )

    frame.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    title = create_label(
        frame,
        APP_NAME,
        28,
        True
    )
    title.pack(pady=(55, 10))

    subtitle = ctk.CTkLabel(
        frame,
        text="Admin Login",
        font=ctk.CTkFont(size=16),
        text_color=c["muted"]
    )
    subtitle.pack(pady=(0, 35))

    username = create_entry(
        frame,
        "Username",
        300
    )
    username.pack(pady=10)

    password = create_entry(
        frame,
        "Password",
        300
    )
    password.configure(show="*")
    password.pack(pady=10)

    show_password = ctk.BooleanVar(value=False)

    def toggle_password():
        if show_password.get():
            password.configure(show="")
        else:
            password.configure(show="*")

    ctk.CTkCheckBox(
        frame,
        text="Show Password",
        variable=show_password,
        command=toggle_password
    ).pack(pady=10)

    def login():

        u = username.get().strip()
        p = password.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, username, role
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (u, p))

        user = cursor.fetchone()

        connection.close()

        if user:
            show_dashboard()
        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password."
            )

    create_button(
        frame,
        "LOGIN",
        login,
        300
    ).pack(pady=25)

    ctk.CTkLabel(
        frame,
        text="Default: admin / admin123",
        text_color=c["muted"]
    ).pack()


# =========================================================
# DASHBOARD
# =========================================================

def show_dashboard():

    clear_window()

    c = colors()

    window.configure(fg_color=c["bg"])

    sidebar = ctk.CTkFrame(
        window,
        width=220,
        fg_color=c["card"],
        corner_radius=0
    )
    sidebar.pack(
        side="left",
        fill="y"
    )

    content = ctk.CTkFrame(
        window,
        fg_color=c["bg"],
        corner_radius=0
    )
    content.pack(
        side="right",
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        sidebar,
        text="SHOP POS",
        font=ctk.CTkFont(
            size=24,
            weight="bold"
        ),
        text_color=c["text"]
    )
    title.pack(
        pady=(35, 35)
    )

    def nav_button(text, command):
        ctk.CTkButton(
            sidebar,
            text=text,
            command=lambda: command(content),
            width=180,
            height=42,
            fg_color="transparent",
            hover_color=BLUE,
            text_color=c["text"],
            anchor="w"
        ).pack(
            pady=4,
            padx=15
        )

    nav_button(
        "Dashboard",
        dashboard_page
    )

    nav_button(
        "New Bill",
        new_bill_page
    )

    nav_button(
        "Products",
        products_page
    )

    nav_button(
        "Customers",
        customers_page
    )

    nav_button(
        "Old Bills",
        old_bills_page
    )

    nav_button(
        "Udhar / Credit",
        credit_page
    )

    nav_button(
        "Expenses",
        expenses_page
    )

    nav_button(
        "Reports",
        reports_page
    )

    nav_button(
        "Settings",
        settings_page
    )

    def toggle_theme():

        global current_mode

        if current_mode == "dark":
            current_mode = "light"
            ctk.set_appearance_mode("light")
        else:
            current_mode = "dark"
            ctk.set_appearance_mode("dark")

        show_dashboard()

    ctk.CTkButton(
        sidebar,
        text="☀ / ☾  Dark / Light",
        command=toggle_theme,
        width=180,
        height=40
    ).pack(
        side="bottom",
        pady=(5, 10)
    )

    ctk.CTkButton(
        sidebar,
        text="Backup Database",
        command=backup_database,
        width=180,
        height=40
    ).pack(
        side="bottom",
        pady=5
    )

    dashboard_page(content)


# =========================================================
# DASHBOARD PAGE
# =========================================================

def dashboard_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Dashboard",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 5)
    )

    create_label(
        parent,
        datetime.now().strftime(
            "%A, %d %B %Y"
        ),
        14
    ).pack(
        anchor="w",
        padx=30
    )

    stats_frame = ctk.CTkFrame(
        parent,
        fg_color="transparent"
    )
    stats_frame.pack(
        fill="x",
        padx=30,
        pady=30
    )

    connection = get_connection()
    cursor = connection.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM sales
        WHERE date = ?
    """, (today,))

    today_sales = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    products = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM customers"
    )

    customers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(remaining), 0)
        FROM sales
    """)

    udhar = cursor.fetchone()[0]

    connection.close()

    stats = [
        (
            "Today's Sales",
            f"Rs. {today_sales:,.2f}"
        ),
        (
            "Total Products",
            str(products)
        ),
        (
            "Customers",
            str(customers)
        ),
        (
            "Total Udhar",
            f"Rs. {udhar:,.2f}"
        )
    ]

    for title, value in stats:

        card = ctk.CTkFrame(
            stats_frame,
            fg_color=c["card"],
            corner_radius=15
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=7
        )

        create_label(
            card,
            title,
            14
        ).pack(
            pady=(25, 5)
        )

        create_label(
            card,
            value,
            24,
            True
        ).pack(
            pady=(0, 25)
        )


# =========================================================
# PRODUCTS
# =========================================================

def products_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    top = ctk.CTkFrame(
        parent,
        fg_color="transparent"
    )
    top.pack(
        fill="x",
        padx=30,
        pady=30
    )

    create_label(
        top,
        "Products",
        30,
        True
    ).pack(
        side="left"
    )

    create_button(
        top,
        "+ Add Product",
        lambda: add_product_window(parent),
        160
    ).pack(
        side="right"
    )

    search_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    search_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    search = create_entry(
        search_frame,
        "Search code / product / category / color",
        400
    )

    search.pack(
        side="left",
        padx=15,
        pady=15
    )

    table_frame = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    table_frame.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 30)
    )

    headers = [
        "Code",
        "Product",
        "Category",
        "Color",
        "Purchase",
        "Selling",
        "Actions"
    ]

    for col, header in enumerate(headers):

        create_label(
            table_frame,
            header,
            13,
            True
        ).grid(
            row=0,
            column=col,
            padx=12,
            pady=15,
            sticky="w"
        )

    def load_products():

        for widget in table_frame.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        text = search.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT id, product_code, product_name,
                   category, color,
                   purchase_price, selling_price
            FROM products
        """

        params = []

        if text:

            query += """
                WHERE product_code LIKE ?
                OR product_name LIKE ?
                OR category LIKE ?
                OR color LIKE ?
            """

            like = f"%{text}%"

            params = [
                like,
                like,
                like,
                like
            ]

        query += " ORDER BY id DESC"

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        connection.close()

        for row_num, row in enumerate(
            rows,
            start=1
        ):

            (
                product_id,
                code,
                name,
                category,
                color,
                purchase,
                selling
            ) = row

            values = [
                code,
                name,
                category or "",
                color or "",
                f"Rs. {purchase:,.2f}",
                f"Rs. {selling:,.2f}"
            ]

            for col, value in enumerate(values):

                create_label(
                    table_frame,
                    str(value),
                    13
                ).grid(
                    row=row_num,
                    column=col,
                    padx=12,
                    pady=10,
                    sticky="w"
                )

            action_frame = ctk.CTkFrame(
                table_frame,
                fg_color="transparent"
            )

            action_frame.grid(
                row=row_num,
                column=6,
                padx=5
            )

            ctk.CTkButton(
                action_frame,
                text="Edit",
                width=60,
                height=30,
                command=lambda pid=product_id:
                edit_product_window(
                    pid,
                    parent
                )
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                action_frame,
                text="Delete",
                width=65,
                height=30,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda pid=product_id:
                delete_product(
                    pid,
                    parent
                )
            ).pack(
                side="left",
                padx=2
            )

    ctk.CTkButton(
        search_frame,
        text="Search",
        command=load_products,
        width=100
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        search_frame,
        text="Clear",
        command=lambda: [
            search.delete(0, "end"),
            load_products()
        ],
        width=90
    ).pack(
        side="left",
        padx=5
    )

    load_products()


# =========================================================
# ADD PRODUCT
# =========================================================

def add_product_window(parent):

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title("Add Product")
    win.geometry("650x520")
    win.grab_set()

    frame = ctk.CTkFrame(
        win,
        fg_color=c["card"],
        corner_radius=15
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    create_label(
        frame,
        "Add New Product",
        24,
        True
    ).pack(
        pady=(25, 20)
    )

    form = ctk.CTkFrame(
        frame,
        fg_color="transparent"
    )

    form.pack(
        fill="x",
        padx=30
    )

    # ROW 1

    create_label(
        form,
        "Product Code",
        13,
        True
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    create_label(
        form,
        "Product Name",
        13,
        True
    ).grid(
        row=0,
        column=1,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    code_entry = create_entry(
        form,
        "e.g. CLO-1025",
        260
    )

    code_entry.grid(
        row=1,
        column=0,
        padx=10,
        pady=(0, 15)
    )

    name_entry = create_entry(
        form,
        "Product name",
        260
    )

    name_entry.grid(
        row=1,
        column=1,
        padx=10,
        pady=(0, 15)
    )

    # ROW 2

    create_label(
        form,
        "Category",
        13,
        True
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    create_label(
        form,
        "Color",
        13,
        True
    ).grid(
        row=2,
        column=1,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    category_entry = create_entry(
        form,
        "Category",
        260
    )

    category_entry.grid(
        row=3,
        column=0,
        padx=10,
        pady=(0, 15)
    )

    color_entry = create_entry(
        form,
        "Color",
        260
    )

    color_entry.grid(
        row=3,
        column=1,
        padx=10,
        pady=(0, 15)
    )

    # ROW 3

    create_label(
        form,
        "Purchase Price",
        13,
        True
    ).grid(
        row=4,
        column=0,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    create_label(
        form,
        "Selling Price",
        13,
        True
    ).grid(
        row=4,
        column=1,
        sticky="w",
        padx=10,
        pady=(5, 3)
    )

    purchase_entry = create_entry(
        form,
        "0.00",
        260
    )

    purchase_entry.grid(
        row=5,
        column=0,
        padx=10,
        pady=(0, 20)
    )

    selling_entry = create_entry(
        form,
        "0.00",
        260
    )

    selling_entry.grid(
        row=5,
        column=1,
        padx=10,
        pady=(0, 20)
    )

    def save_product():

        code = code_entry.get().strip()
        name = name_entry.get().strip()
        category = category_entry.get().strip()
        color = color_entry.get().strip()

        if not code:

            messagebox.showerror(
                "Error",
                "Product Code is required.",
                parent=win
            )

            return

        if not name:

            messagebox.showerror(
                "Error",
                "Product Name is required.",
                parent=win
            )

            return

        try:

            purchase = float(
                purchase_entry.get().strip() or 0
            )

            selling = float(
                selling_entry.get().strip() or 0
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Purchase Price and Selling Price must be numbers.",
                parent=win
            )

            return

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA table_info(products)"
            )

            existing_columns = [
                row[1]
                for row in cursor.fetchall()
            ]

            data = {
                "product_code": code,
                "product_name": name,
                "category": category,
                "color": color,
                "purchase_price": purchase,
                "selling_price": selling,
                "date_added": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            # Old database compatibility

            if "size" in existing_columns:
                data["size"] = ""

            if "stock" in existing_columns:
                data["stock"] = 0

            if "minimum_stock" in existing_columns:
                data["minimum_stock"] = 0

            if "supplier" in existing_columns:
                data["supplier"] = ""

            columns = list(data.keys())

            placeholders = ", ".join(
                ["?"] * len(columns)
            )

            query = f"""
                INSERT INTO products
                ({", ".join(columns)})
                VALUES ({placeholders})
            """

            cursor.execute(
                query,
                [
                    data[column]
                    for column in columns
                ]
            )

            connection.commit()
            connection.close()

            messagebox.showinfo(
                "Success",
                "Product saved successfully.",
                parent=win
            )

            win.destroy()
            products_page(parent)

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "This Product Code already exists.",
                parent=win
            )

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                str(error),
                parent=win
            )

    button_frame = ctk.CTkFrame(
        frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=10
    )

    create_button(
        button_frame,
        "Save Product",
        save_product,
        180
    ).pack(
        side="left",
        padx=8
    )

    ctk.CTkButton(
        button_frame,
        text="Cancel",
        command=win.destroy,
        width=150,
        height=40
    ).pack(
        side="left",
        padx=8
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

def edit_product_window(
    product_id,
    parent
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT product_code, product_name,
               category, color,
               purchase_price, selling_price
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    connection.close()

    if not product:

        messagebox.showerror(
            "Error",
            "Product not found."
        )

        return

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title("Edit Product")
    win.geometry("650x520")
    win.grab_set()

    frame = ctk.CTkFrame(
        win,
        fg_color=c["card"],
        corner_radius=15
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    create_label(
        frame,
        "Edit Product",
        24,
        True
    ).pack(
        pady=(25, 20)
    )

    form = ctk.CTkFrame(
        frame,
        fg_color="transparent"
    )

    form.pack(
        fill="x",
        padx=30
    )

    labels = [
        "Product Code",
        "Product Name",
        "Category",
        "Color",
        "Purchase Price",
        "Selling Price"
    ]

    entries = []

    values = [
        product[0],
        product[1],
        product[2] or "",
        product[3] or "",
        product[4],
        product[5]
    ]

    for i, (label, value) in enumerate(
        zip(labels, values)
    ):

        row = i // 2
        col = i % 2

        create_label(
            form,
            label,
            13,
            True
        ).grid(
            row=row * 2,
            column=col,
            sticky="w",
            padx=10,
            pady=(5, 3)
        )

        entry = create_entry(
            form,
            label,
            260
        )

        entry.insert(
            0,
            str(value)
        )

        entry.grid(
            row=row * 2 + 1,
            column=col,
            padx=10,
            pady=(0, 15)
        )

        entries.append(entry)

    def update_product():

        try:

            code = entries[0].get().strip()
            name = entries[1].get().strip()
            category = entries[2].get().strip()
            color = entries[3].get().strip()
            purchase = float(
                entries[4].get() or 0
            )
            selling = float(
                entries[5].get() or 0
            )

            if not code or not name:

                messagebox.showerror(
                    "Error",
                    "Product Code and Product Name are required.",
                    parent=win
                )

                return

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE products
                SET product_code = ?,
                    product_name = ?,
                    category = ?,
                    color = ?,
                    purchase_price = ?,
                    selling_price = ?
                WHERE id = ?
            """, (
                code,
                name,
                category,
                color,
                purchase,
                selling,
                product_id
            ))

            connection.commit()
            connection.close()

            messagebox.showinfo(
                "Success",
                "Product updated successfully.",
                parent=win
            )

            win.destroy()
            products_page(parent)

        except ValueError:

            messagebox.showerror(
                "Error",
                "Prices must be numbers.",
                parent=win
            )

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "Product Code already exists.",
                parent=win
            )

    create_button(
        frame,
        "Update Product",
        update_product,
        220
    ).pack(
        pady=15
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

def delete_product(
    product_id,
    parent
):

    answer = messagebox.askyesno(
        "Delete Product",
        "Are you sure you want to delete this product?"
    )

    if not answer:
        return

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    connection.commit()
    connection.close()

    products_page(parent)


# =========================================================
# NEW BILL
# =========================================================

def new_bill_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "New Bill",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 15)
    )

    top = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    top.pack(
        fill="x",
        padx=30
    )

    code_entry = create_entry(
        top,
        "Product Code",
        200
    )

    code_entry.grid(
        row=0,
        column=0,
        padx=10,
        pady=15
    )

    name_label = create_label(
        top,
        "Product: -",
        14,
        True
    )

    name_label.grid(
        row=0,
        column=1,
        padx=10
    )

    base_price_label = create_label(
        top,
        "Base Price: Rs. 0",
        14
    )

    base_price_label.grid(
        row=0,
        column=2,
        padx=10
    )

    qty_entry = create_entry(
        top,
        "Qty",
        80
    )

    qty_entry.grid(
        row=1,
        column=0,
        padx=10,
        pady=(0, 15)
    )

    qty_entry.insert(
        0,
        "1"
    )

    bill_price_entry = create_entry(
        top,
        "Bill Price",
        150
    )

    bill_price_entry.grid(
        row=1,
        column=1,
        padx=10,
        pady=(0, 15)
    )

    discount_entry = create_entry(
        top,
        "Discount Rs.",
        150
    )

    discount_entry.grid(
        row=1,
        column=2,
        padx=10,
        pady=(0, 15)
    )

    discount_entry.insert(
        0,
        "0"
    )

    bill_items = []

    def search_product():

        code = code_entry.get().strip()

        if not code:
            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT product_name, selling_price
            FROM products
            WHERE product_code = ?
        """, (code,))

        product = cursor.fetchone()

        connection.close()

        if not product:

            messagebox.showerror(
                "Product Not Found",
                "No product found with this code."
            )

            return

        name, selling = product

        name_label.configure(
            text=f"Product: {name}"
        )

        base_price_label.configure(
            text=f"Base Price: Rs. {selling:,.2f}"
        )

        bill_price_entry.delete(
            0,
            "end"
        )

        bill_price_entry.insert(
            0,
            str(selling)
        )

    ctk.CTkButton(
        top,
        text="Find Product",
        command=search_product,
        width=130
    ).grid(
        row=0,
        column=3,
        padx=10
    )

    table = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    table.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=15
    )

    headers = [
        "Code",
        "Product",
        "Qty",
        "Price",
        "Discount",
        "Total",
        "Remove"
    ]

    for col, header in enumerate(headers):

        create_label(
            table,
            header,
            13,
            True
        ).grid(
            row=0,
            column=col,
            padx=12,
            pady=12
        )

    totals_label = create_label(
        parent,
        "Subtotal: Rs. 0 | Discount: Rs. 0 | Grand Total: Rs. 0",
        17,
        True
    )

    totals_label.pack(
        anchor="e",
        padx=35
    )

    def refresh_bill():

        for widget in table.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        subtotal = 0
        total_discount = 0

        for i, item in enumerate(
            bill_items,
            start=1
        ):

            item_total = (
                item["qty"] * item["price"]
            ) - item["discount"]

            if item_total < 0:
                item_total = 0

            item["total"] = item_total

            subtotal += (
                item["qty"] * item["price"]
            )

            total_discount += item["discount"]

            values = [
                item["code"],
                item["name"],
                item["qty"],
                f"Rs. {item['price']:,.2f}",
                f"Rs. {item['discount']:,.2f}",
                f"Rs. {item_total:,.2f}"
            ]

            for col, value in enumerate(values):

                create_label(
                    table,
                    str(value),
                    13
                ).grid(
                    row=i,
                    column=col,
                    padx=12,
                    pady=8
                )

            ctk.CTkButton(
                table,
                text="X",
                width=50,
                height=28,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda index=i - 1:
                remove_bill_item(index)
            ).grid(
                row=i,
                column=6
            )

        grand_total = (
            subtotal - total_discount
        )

        totals_label.configure(
            text=(
                f"Subtotal: Rs. {subtotal:,.2f}   |   "
                f"Discount: Rs. {total_discount:,.2f}   |   "
                f"Grand Total: Rs. {grand_total:,.2f}"
            )
        )

    def remove_bill_item(index):

        if 0 <= index < len(bill_items):
            bill_items.pop(index)

        refresh_bill()

    def add_item():

        code = code_entry.get().strip()

        if not code:

            messagebox.showerror(
                "Error",
                "Enter Product Code."
            )

            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT product_name, selling_price,
                   purchase_price
            FROM products
            WHERE product_code = ?
        """, (code,))

        product = cursor.fetchone()

        connection.close()

        if not product:

            messagebox.showerror(
                "Error",
                "Product not found."
            )

            return

        name, base_price, purchase_price = product

        try:

            qty = int(
                qty_entry.get().strip() or 1
            )

            price = float(
                bill_price_entry.get().strip()
                or base_price
            )

            discount = float(
                discount_entry.get().strip()
                or 0
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Qty and prices must be valid numbers."
            )

            return

        # SAME PRODUCT COMBINE

        for item in bill_items:

            if item["code"] == code:

                item["qty"] += qty
                item["discount"] += discount
                item["price"] = price

                refresh_bill()

                return

        bill_items.append({
            "code": code,
            "name": name,
            "qty": qty,
            "price": price,
            "purchase_price": purchase_price,
            "discount": discount,
            "total": 0
        })

        refresh_bill()

    ctk.CTkButton(
        top,
        text="+ Add To Bill",
        command=add_item,
        width=130
    ).grid(
        row=1,
        column=3,
        padx=10
    )

    customer_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    customer_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    customer_name = create_entry(
        customer_frame,
        "Customer Name",
        250
    )

    customer_name.pack(
        side="left",
        padx=15,
        pady=15
    )

    customer_phone = create_entry(
        customer_frame,
        "Customer Phone",
        200
    )

    customer_phone.pack(
        side="left",
        padx=15
    )

    paid_entry = create_entry(
        customer_frame,
        "Paid Amount",
        180
    )

    paid_entry.pack(
        side="left",
        padx=15
    )

    paid_entry.insert(
        0,
        "0"
    )

    def save_bill():

        if not bill_items:

            messagebox.showerror(
                "Error",
                "Bill is empty."
            )

            return

        name = customer_name.get().strip()
        phone = customer_phone.get().strip()

        try:

            paid = float(
                paid_entry.get().strip() or 0
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Paid amount must be a number."
            )

            return

        subtotal = sum(
            item["qty"] * item["price"]
            for item in bill_items
        )

        discount = sum(
            item["discount"]
            for item in bill_items
        )

        total = subtotal - discount

        if paid < 0:
            paid = 0

        if paid > total:
            paid = total

        remaining = total - paid

        connection = get_connection()
        cursor = connection.cursor()

        try:

            customer_id = None

            if name or phone:

                if phone:

                    cursor.execute("""
                        SELECT id
                        FROM customers
                        WHERE phone = ?
                    """, (phone,))

                    existing = cursor.fetchone()

                    if existing:

                        customer_id = existing[0]

                        cursor.execute("""
                            UPDATE customers
                            SET name = ?
                            WHERE id = ?
                        """, (
                            name,
                            customer_id
                        ))

                if customer_id is None:

                    cursor.execute("""
                        INSERT INTO customers (name, phone)
                        VALUES (?, ?)
                    """, (
                        name,
                        phone
                    ))

                    customer_id = cursor.lastrowid

            now = datetime.now()

            cursor.execute("""
                INSERT INTO sales
                (
                    customer_id,
                    date,
                    time,
                    subtotal,
                    discount,
                    total,
                    paid,
                    remaining
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                subtotal,
                discount,
                total,
                paid,
                remaining
            ))

            sale_id = cursor.lastrowid

            for item in bill_items:

                cursor.execute("""
                    INSERT INTO sale_items
                    (
                        sale_id,
                        product_code,
                        quantity,
                        price,
                        discount,
                        total
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sale_id,
                    item["code"],
                    item["qty"],
                    item["price"],
                    item["discount"],
                    item["total"]
                ))

            connection.commit()
            connection.close()

            messagebox.showinfo(
                "Bill Saved",
                f"Bill saved successfully.\n\n"
                f"Total: Rs. {total:,.2f}\n"
                f"Paid: Rs. {paid:,.2f}\n"
                f"Remaining: Rs. {remaining:,.2f}"
            )

            new_bill_page(parent)

        except Exception as error:

            connection.rollback()
            connection.close()

            messagebox.showerror(
                "Database Error",
                str(error)
            )

    create_button(
        customer_frame,
        "SAVE BILL",
        save_bill,
        160
    ).pack(
        side="right",
        padx=15
    )


# =========================================================
# CUSTOMERS
# =========================================================

def customers_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Customers",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=30
    )

    search_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    search_frame.pack(
        fill="x",
        padx=30
    )

    search = create_entry(
        search_frame,
        "Search name / phone",
        350
    )

    search.pack(
        side="left",
        padx=15,
        pady=15
    )

    table = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    table.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=15
    )

    headers = [
        "Customer ID",
        "Name",
        "Phone",
        "Total Purchase",
        "Outstanding",
        "History"
    ]

    for col, header in enumerate(headers):

        create_label(
            table,
            header,
            13,
            True
        ).grid(
            row=0,
            column=col,
            padx=15,
            pady=15
        )

    def load_customers():

        for widget in table.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        text = search.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT
                c.id,
                c.name,
                c.phone,
                COALESCE(SUM(s.total), 0),
                COALESCE(SUM(s.remaining), 0)
            FROM customers c
            LEFT JOIN sales s
                ON c.id = s.customer_id
        """

        params = []

        if text:

            query += """
                WHERE c.name LIKE ?
                OR c.phone LIKE ?
                OR CAST(c.id AS TEXT) LIKE ?
            """

            like = f"%{text}%"

            params = [
                like,
                like,
                like
            ]

        query += """
            GROUP BY c.id
            ORDER BY c.id DESC
        """

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        connection.close()

        for row_num, row in enumerate(
            rows,
            start=1
        ):

            (
                customer_id,
                name,
                phone,
                total,
                outstanding
            ) = row

            values = [
                customer_id,
                name or "",
                phone or "",
                f"Rs. {total:,.2f}",
                f"Rs. {outstanding:,.2f}"
            ]

            for col, value in enumerate(values):

                create_label(
                    table,
                    str(value)
                ).grid(
                    row=row_num,
                    column=col,
                    padx=15,
                    pady=10
                )

            ctk.CTkButton(
                table,
                text="View History",
                width=120,
                height=32,
                command=lambda cid=customer_id:
                customer_history(cid)
            ).grid(
                row=row_num,
                column=5,
                padx=10
            )

    ctk.CTkButton(
        search_frame,
        text="Search",
        command=load_customers,
        width=100
    ).pack(
        side="left",
        padx=5
    )

    load_customers()


# =========================================================
# CUSTOMER HISTORY
# =========================================================

def customer_history(customer_id):

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title("Customer History")
    win.geometry("900x600")

    frame = ctk.CTkScrollableFrame(
        win,
        fg_color=c["card"]
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=15
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, phone
        FROM customers
        WHERE id = ?
    """, (customer_id,))

    customer = cursor.fetchone()

    cursor.execute("""
        SELECT
            id,
            date,
            time,
            total,
            paid,
            remaining
        FROM sales
        WHERE customer_id = ?
        ORDER BY id DESC
    """, (customer_id,))

    sales = cursor.fetchall()

    connection.close()

    if customer:

        create_label(
            frame,
            f"Customer: {customer[0] or '-'}",
            22,
            True
        ).pack(
            anchor="w",
            pady=10
        )

        create_label(
            frame,
            f"Phone: {customer[1] or '-'}",
            14
        ).pack(
            anchor="w",
            pady=5
        )

    for sale in sales:

        (
            sale_id,
            date,
            time,
            total,
            paid,
            remaining
        ) = sale

        card = ctk.CTkFrame(
            frame,
            fg_color=c["card2"],
            corner_radius=10
        )

        card.pack(
            fill="x",
            pady=7
        )

        create_label(
            card,
            f"Bill ID: {sale_id}",
            15,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 3)
        )

        create_label(
            card,
            f"{date}  {time}",
            13
        ).pack(
            anchor="w",
            padx=15
        )

        create_label(
            card,
            f"Total: Rs. {total:,.2f}   |   "
            f"Paid: Rs. {paid:,.2f}   |   "
            f"Remaining: Rs. {remaining:,.2f}",
            14
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )


# =========================================================
# OLD BILLS
# =========================================================

def old_bills_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Old Bills",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 15)
    )

    search_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    search_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    # DATE WITH CALENDAR

    date_frame, date_entry = create_date_picker(
        search_frame,
        180,
        "Date YYYY-MM-DD"
    )

    date_frame.pack(
        side="left",
        padx=10,
        pady=15
    )

    phone_entry = create_entry(
        search_frame,
        "Customer Phone",
        180
    )

    phone_entry.pack(
        side="left",
        padx=10
    )

    customer_id_entry = create_entry(
        search_frame,
        "Customer ID",
        150
    )

    customer_id_entry.pack(
        side="left",
        padx=10
    )

    table = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    table.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 30)
    )

    headers = [
        "Bill ID",
        "Date",
        "Time",
        "Customer",
        "Phone",
        "Total",
        "Paid",
        "Remaining",
        "View"
    ]

    for col, header in enumerate(headers):

        create_label(
            table,
            header,
            13,
            True
        ).grid(
            row=0,
            column=col,
            padx=10,
            pady=15
        )

    def load_bills():

        for widget in table.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        date = date_entry.get().strip()
        phone = phone_entry.get().strip()
        customer_id = customer_id_entry.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT
                s.id,
                s.date,
                s.time,
                COALESCE(c.name, '-'),
                COALESCE(c.phone, '-'),
                s.total,
                s.paid,
                s.remaining
            FROM sales s
            LEFT JOIN customers c
                ON s.customer_id = c.id
            WHERE 1 = 1
        """

        params = []

        if date:

            query += " AND s.date = ?"
            params.append(date)

        if phone:

            query += " AND c.phone LIKE ?"
            params.append(
                f"%{phone}%"
            )

        if customer_id:

            query += " AND c.id = ?"
            params.append(customer_id)

        query += " ORDER BY s.id DESC"

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        connection.close()

        for row_num, row in enumerate(
            rows,
            start=1
        ):

            (
                bill_id,
                date,
                time,
                name,
                phone,
                total,
                paid,
                remaining
            ) = row

            values = [
                bill_id,
                date,
                time,
                name,
                phone,
                f"Rs. {total:,.2f}",
                f"Rs. {paid:,.2f}",
                f"Rs. {remaining:,.2f}"
            ]

            for col, value in enumerate(values):

                create_label(
                    table,
                    str(value),
                    12
                ).grid(
                    row=row_num,
                    column=col,
                    padx=10,
                    pady=8
                )

            ctk.CTkButton(
                table,
                text="View",
                width=70,
                height=30,
                command=lambda sid=bill_id:
                view_bill(sid)
            ).grid(
                row=row_num,
                column=8
            )

    ctk.CTkButton(
        search_frame,
        text="Search",
        command=load_bills,
        width=100
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        search_frame,
        text="Today",
        command=lambda: [
            date_entry.delete(
                0,
                "end"
            ),
            date_entry.insert(
                0,
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            ),
            load_bills()
        ],
        width=90
    ).pack(
        side="left",
        padx=5
    )

    load_bills()


# =========================================================
# VIEW BILL
# =========================================================

def view_bill(sale_id):

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title(f"Bill #{sale_id}")
    win.geometry("800x650")

    frame = ctk.CTkScrollableFrame(
        win,
        fg_color=c["card"]
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.date,
            s.time,
            s.subtotal,
            s.discount,
            s.total,
            s.paid,
            s.remaining,
            c.name,
            c.phone
        FROM sales s
        LEFT JOIN customers c
            ON s.customer_id = c.id
        WHERE s.id = ?
    """, (sale_id,))

    sale = cursor.fetchone()

    cursor.execute("""
        SELECT
            product_code,
            quantity,
            price,
            discount,
            total
        FROM sale_items
        WHERE sale_id = ?
    """, (sale_id,))

    items = cursor.fetchall()

    connection.close()

    if not sale:
        return

    (
        date,
        time,
        subtotal,
        discount,
        total,
        paid,
        remaining,
        name,
        phone
    ) = sale

    create_label(
        frame,
        f"Bill #{sale_id}",
        26,
        True
    ).pack(
        anchor="w",
        pady=10
    )

    create_label(
        frame,
        f"Date: {date}    Time: {time}",
        14
    ).pack(
        anchor="w",
        pady=5
    )

    create_label(
        frame,
        f"Customer: {name or '-'}    Phone: {phone or '-'}",
        14
    ).pack(
        anchor="w",
        pady=5
    )

    for (
        code,
        qty,
        price,
        item_discount,
        item_total
    ) in items:

        card = ctk.CTkFrame(
            frame,
            fg_color=c["card2"],
            corner_radius=8
        )

        card.pack(
            fill="x",
            pady=4
        )

        create_label(
            card,
            f"{code}   |   Qty: {qty}   |   "
            f"Price: Rs. {price:,.2f}   |   "
            f"Discount: Rs. {item_discount:,.2f}   |   "
            f"Total: Rs. {item_total:,.2f}",
            13
        ).pack(
            padx=12,
            pady=10
        )

    create_label(
        frame,
        f"Subtotal: Rs. {subtotal:,.2f}",
        15
    ).pack(
        anchor="e",
        pady=5
    )

    create_label(
        frame,
        f"Discount: Rs. {discount:,.2f}",
        15
    ).pack(
        anchor="e",
        pady=5
    )

    create_label(
        frame,
        f"Total: Rs. {total:,.2f}",
        18,
        True
    ).pack(
        anchor="e",
        pady=5
    )

    create_label(
        frame,
        f"Paid: Rs. {paid:,.2f}",
        15
    ).pack(
        anchor="e",
        pady=5
    )

    create_label(
        frame,
        f"Remaining: Rs. {remaining:,.2f}",
        18,
        True
    ).pack(
        anchor="e",
        pady=5
    )


# =========================================================
# CREDIT / UDHAR
# =========================================================

def credit_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Udhar / Credit",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 15)
    )

    search_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    search_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    # DATE WITH CALENDAR

    date_frame, date_entry = create_date_picker(
        search_frame,
        170,
        "Date YYYY-MM-DD"
    )

    date_frame.pack(
        side="left",
        padx=8,
        pady=15
    )

    phone_entry = create_entry(
        search_frame,
        "Phone",
        170
    )

    phone_entry.pack(
        side="left",
        padx=8
    )

    customer_id_entry = create_entry(
        search_frame,
        "Customer ID",
        140
    )

    customer_id_entry.pack(
        side="left",
        padx=8
    )

    name_entry = create_entry(
        search_frame,
        "Customer Name",
        180
    )

    name_entry.pack(
        side="left",
        padx=8
    )

    table = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    table.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 30)
    )

    headers = [
        "Bill ID",
        "Date",
        "Customer ID",
        "Customer",
        "Phone",
        "Total",
        "Paid",
        "Remaining",
        "Receive"
    ]

    for col, header in enumerate(headers):

        create_label(
            table,
            header,
            12,
            True
        ).grid(
            row=0,
            column=col,
            padx=8,
            pady=15
        )

    def load_credit():

        for widget in table.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        date = date_entry.get().strip()
        phone = phone_entry.get().strip()
        customer_id = customer_id_entry.get().strip()
        name = name_entry.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT
                s.id,
                s.date,
                c.id,
                c.name,
                c.phone,
                s.total,
                s.paid,
                s.remaining
            FROM sales s
            LEFT JOIN customers c
                ON s.customer_id = c.id
            WHERE s.remaining > 0
        """

        params = []

        if date:

            query += " AND s.date = ?"
            params.append(date)

        if phone:

            query += " AND c.phone LIKE ?"
            params.append(
                f"%{phone}%"
            )

        if customer_id:

            query += " AND c.id = ?"
            params.append(customer_id)

        if name:

            query += " AND c.name LIKE ?"
            params.append(
                f"%{name}%"
            )

        query += " ORDER BY s.id DESC"

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        connection.close()

        for row_num, row in enumerate(
            rows,
            start=1
        ):

            (
                bill_id,
                date,
                cid,
                name,
                phone,
                total,
                paid,
                remaining
            ) = row

            values = [
                bill_id,
                date,
                cid or "-",
                name or "-",
                phone or "-",
                f"Rs. {total:,.2f}",
                f"Rs. {paid:,.2f}",
                f"Rs. {remaining:,.2f}"
            ]

            for col, value in enumerate(values):

                create_label(
                    table,
                    str(value),
                    12
                ).grid(
                    row=row_num,
                    column=col,
                    padx=8,
                    pady=9
                )

            ctk.CTkButton(
                table,
                text="Receive",
                width=85,
                height=30,
                command=lambda sid=bill_id:
                receive_payment(
                    sid,
                    parent
                )
            ).grid(
                row=row_num,
                column=8
            )

    ctk.CTkButton(
        search_frame,
        text="Search",
        command=load_credit,
        width=100
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        search_frame,
        text="Clear",
        command=lambda: [
            date_entry.delete(
                0,
                "end"
            ),
            phone_entry.delete(
                0,
                "end"
            ),
            customer_id_entry.delete(
                0,
                "end"
            ),
            name_entry.delete(
                0,
                "end"
            ),
            load_credit()
        ],
        width=90
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        search_frame,
        text="Payment History",
        command=payment_history,
        width=140
    ).pack(
        side="right",
        padx=10
    )

    load_credit()


# =========================================================
# RECEIVE PAYMENT
# =========================================================

def receive_payment(
    sale_id,
    parent
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.customer_id,
            s.total,
            s.paid,
            s.remaining,
            c.name,
            c.phone
        FROM sales s
        LEFT JOIN customers c
            ON s.customer_id = c.id
        WHERE s.id = ?
    """, (sale_id,))

    sale = cursor.fetchone()

    connection.close()

    if not sale:

        messagebox.showerror(
            "Error",
            "Bill not found."
        )

        return

    (
        customer_id,
        total,
        paid,
        remaining,
        name,
        phone
    ) = sale

    if remaining <= 0:

        messagebox.showinfo(
            "Already Paid",
            "This bill has no remaining payment."
        )

        return

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title("Receive Payment")
    win.geometry("450x430")
    win.grab_set()

    frame = ctk.CTkFrame(
        win,
        fg_color=c["card"],
        corner_radius=15
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    create_label(
        frame,
        "Receive Payment",
        25,
        True
    ).pack(
        pady=(30, 20)
    )

    create_label(
        frame,
        f"Customer: {name or '-'}",
        14
    ).pack(
        pady=5
    )

    create_label(
        frame,
        f"Phone: {phone or '-'}",
        14
    ).pack(
        pady=5
    )

    create_label(
        frame,
        f"Bill Total: Rs. {total:,.2f}",
        14
    ).pack(
        pady=5
    )

    create_label(
        frame,
        f"Already Paid: Rs. {paid:,.2f}",
        14
    ).pack(
        pady=5
    )

    create_label(
        frame,
        f"Remaining: Rs. {remaining:,.2f}",
        17,
        True
    ).pack(
        pady=10
    )

    amount_entry = create_entry(
        frame,
        "Payment Amount",
        280
    )

    amount_entry.pack(
        pady=15
    )

    def save_payment():

        try:

            amount = float(
                amount_entry.get().strip()
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Enter a valid payment amount.",
                parent=win
            )

            return

        if amount <= 0:

            messagebox.showerror(
                "Error",
                "Payment must be greater than 0.",
                parent=win
            )

            return

        if amount > remaining:

            messagebox.showerror(
                "Error",
                "Payment cannot be greater than remaining amount.",
                parent=win
            )

            return

        connection = get_connection()
        cursor = connection.cursor()

        try:

            now = datetime.now()

            # SAVE PAYMENT

            cursor.execute("""
                INSERT INTO payments
                (
                    customer_id,
                    sale_id,
                    amount,
                    date,
                    time
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                customer_id,
                sale_id,
                amount,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            ))

            # UPDATE SALE

            new_paid = paid + amount
            new_remaining = total - new_paid

            if new_remaining < 0:
                new_remaining = 0

            cursor.execute("""
                UPDATE sales
                SET paid = ?,
                    remaining = ?
                WHERE id = ?
            """, (
                new_paid,
                new_remaining,
                sale_id
            ))

            connection.commit()
            connection.close()

            messagebox.showinfo(
                "Payment Received",
                f"Payment: Rs. {amount:,.2f}\n"
                f"Remaining: Rs. {new_remaining:,.2f}",
                parent=win
            )

            win.destroy()
            credit_page(parent)

        except Exception as error:

            connection.rollback()
            connection.close()

            messagebox.showerror(
                "Payment Error",
                str(error),
                parent=win
            )

    create_button(
        frame,
        "Receive Payment",
        save_payment,
        220
    ).pack(
        pady=15
    )


# =========================================================
# PAYMENT HISTORY
# =========================================================

def payment_history():

    c = colors()

    win = ctk.CTkToplevel(window)
    win.title("Payment History")
    win.geometry("850x600")

    search_frame = ctk.CTkFrame(
        win,
        fg_color=c["card"],
        corner_radius=10
    )

    search_frame.pack(
        fill="x",
        padx=15,
        pady=15
    )

    # DATE WITH CALENDAR

    date_frame, date_entry = create_date_picker(
        search_frame,
        180,
        "Date YYYY-MM-DD"
    )

    date_frame.pack(
        side="left",
        padx=8,
        pady=12
    )

    phone_entry = create_entry(
        search_frame,
        "Customer Phone",
        180
    )

    phone_entry.pack(
        side="left",
        padx=8
    )

    table = ctk.CTkScrollableFrame(
        win,
        fg_color=c["card"],
        corner_radius=10
    )

    table.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 15)
    )

    headers = [
        "Payment ID",
        "Date",
        "Time",
        "Customer",
        "Phone",
        "Bill ID",
        "Amount"
    ]

    for col, header in enumerate(headers):

        create_label(
            table,
            header,
            12,
            True
        ).grid(
            row=0,
            column=col,
            padx=10,
            pady=12
        )

    def load_history():

        for widget in table.winfo_children():

            if widget.grid_info().get(
                "row",
                0
            ) != 0:

                widget.destroy()

        date = date_entry.get().strip()
        phone = phone_entry.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT
                p.id,
                p.date,
                p.time,
                c.name,
                c.phone,
                p.sale_id,
                p.amount
            FROM payments p
            LEFT JOIN customers c
                ON p.customer_id = c.id
            WHERE 1 = 1
        """

        params = []

        if date:

            query += " AND p.date = ?"
            params.append(date)

        if phone:

            query += " AND c.phone LIKE ?"
            params.append(
                f"%{phone}%"
            )

        query += " ORDER BY p.id DESC"

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        connection.close()

        for row_num, row in enumerate(
            rows,
            start=1
        ):

            for col, value in enumerate(row):

                if col == 6:

                    value = (
                        f"Rs. {value:,.2f}"
                    )

                create_label(
                    table,
                    str(value or "-"),
                    12
                ).grid(
                    row=row_num,
                    column=col,
                    padx=10,
                    pady=8
                )

    ctk.CTkButton(
        search_frame,
        text="Search",
        command=load_history,
        width=100
    ).pack(
        side="left",
        padx=5
    )

    load_history()


# =========================================================
# EXPENSES
# =========================================================

def expenses_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Expenses",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 15)
    )

    # ADD EXPENSE

    add_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    add_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    name_entry = create_entry(
        add_frame,
        "Expense Name",
        200
    )
    name_entry.pack(
        side="left",
        padx=10,
        pady=15
    )

    amount_entry = create_entry(
        add_frame,
        "Amount",
        150
    )
    amount_entry.pack(
        side="left",
        padx=10
    )

    date_frame, date_entry = create_date_picker(
        add_frame,
        180,
        "Date YYYY-MM-DD"
    )
    date_frame.pack(
        side="left",
        padx=10,
        pady=15
    )

    note_entry = create_entry(
        add_frame,
        "Note (Optional)",
        220
    )
    note_entry.pack(
        side="left",
        padx=10
    )

    table = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )
    table.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(0, 30)
    )

    headers = [
        "ID",
        "Date",
        "Expense Name",
        "Amount",
        "Note",
        "Remove"
    ]

    for col, header in enumerate(headers):
        create_label(
            table,
            header,
            13,
            True
        ).grid(
            row=0,
            column=col,
            padx=12,
            pady=15,
            sticky="w"
        )

    # SEARCH

    search_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )
    search_frame.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    search_date_frame, search_date_entry = create_date_picker(
        search_frame,
        180,
        "Search Date YYYY-MM-DD"
    )
    search_date_frame.pack(
        side="left",
        padx=10,
        pady=15
    )

    search_name = create_entry(
        search_frame,
        "Search Expense Name",
        220
    )
    search_name.pack(
        side="left",
        padx=10
    )

    def load_expenses():

        for widget in table.winfo_children():
            if widget.grid_info().get("row", 0) != 0:
                widget.destroy()

        date = search_date_entry.get().strip()
        name = search_name.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT id, date, name, amount, note
            FROM expenses
            WHERE 1 = 1
        """

        params = []

        if date:
            query += " AND date = ?"
            params.append(date)

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")

        query += " ORDER BY id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        connection.close()

        for row_num, row in enumerate(rows, start=1):

            expense_id, date, name, amount, note = row

            values = [
                expense_id,
                date or "-",
                name,
                f"Rs. {amount:,.2f}",
                note or "-"
            ]

            for col, value in enumerate(values):
                create_label(
                    table,
                    str(value),
                    13
                ).grid(
                    row=row_num,
                    column=col,
                    padx=12,
                    pady=10,
                    sticky="w"
                )

            ctk.CTkButton(
                table,
                text="Remove",
                width=80,
                height=30,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda eid=expense_id: delete_expense(eid, parent)
            ).grid(
                row=row_num,
                column=5,
                padx=8,
                pady=8
            )

    def add_expense():

        name = name_entry.get().strip()
        amount_text = amount_entry.get().strip()
        date = date_entry.get().strip()
        note = note_entry.get().strip()

        if not name or not amount_text or not date:
            messagebox.showerror(
                "Error",
                "Please enter expense name, amount and date."
            )
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror(
                "Error",
                "Amount must be a valid number."
            )
            return

        if amount < 0:
            messagebox.showerror(
                "Error",
                "Amount cannot be negative."
            )
            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO expenses (name, amount, date, note)
            VALUES (?, ?, ?, ?)
            """,
            (name, amount, date, note)
        )

        connection.commit()
        connection.close()

        name_entry.delete(0, "end")
        amount_entry.delete(0, "end")
        date_entry.delete(0, "end")
        note_entry.delete(0, "end")

        load_expenses()

        messagebox.showinfo(
            "Success",
            "Expense added successfully."
        )

    def search_expenses():
        load_expenses()

    def clear_search():
        search_date_entry.delete(0, "end")
        search_name.delete(0, "end")
        load_expenses()

    create_button(
        add_frame,
        "Add Expense",
        add_expense,
        130
    ).pack(
        side="left",
        padx=10
    )

    create_button(
        search_frame,
        "Search",
        search_expenses,
        100
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        search_frame,
        text="Clear",
        command=clear_search,
        width=90,
        height=40
    ).pack(
        side="left",
        padx=5
    )

    load_expenses()


def delete_expense(expense_id, parent):

    if not messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to remove this expense?"
    ):
        return

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    connection.commit()
    connection.close()

    expenses_page(parent)

    messagebox.showinfo(
        "Success",
        "Expense removed successfully."
    )


# =========================================================
# REPORTS
# =========================================================

def reports_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Sales Reports",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 15)
    )

    filter_frame = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    filter_frame.pack(
        fill="x",
        padx=30
    )

    # DATE WITH CALENDAR

    date_frame, date_entry = create_date_picker(
        filter_frame,
        220,
        "Specific Date YYYY-MM-DD"
    )

    date_frame.pack(
        side="left",
        padx=10,
        pady=15
    )

    product_entry = create_entry(
        filter_frame,
        "Product Code",
        180
    )

    product_entry.pack(
        side="left",
        padx=10
    )

    result_frame = ctk.CTkScrollableFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    result_frame.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=15
    )

    def run_report():

        for widget in result_frame.winfo_children():
            widget.destroy()

        date = date_entry.get().strip()
        product_code = product_entry.get().strip()

        connection = get_connection()
        cursor = connection.cursor()

        # DATE SALES

        query = """
            SELECT
                COUNT(id),
                COALESCE(SUM(subtotal), 0),
                COALESCE(SUM(discount), 0),
                COALESCE(SUM(total), 0),
                COALESCE(SUM(paid), 0),
                COALESCE(SUM(remaining), 0)
            FROM sales
            WHERE 1 = 1
        """

        params = []

        if date:

            query += " AND date = ?"
            params.append(date)

        cursor.execute(
            query,
            params
        )

        summary = cursor.fetchone()

        (
            bill_count,
            subtotal,
            discount,
            revenue,
            paid,
            remaining
        ) = summary

        create_label(
            result_frame,
            f"Total Bills: {bill_count}",
            20,
            True
        ).pack(
            anchor="w",
            pady=10
        )

        create_label(
            result_frame,
            f"Subtotal: Rs. {subtotal:,.2f}",
            16
        ).pack(
            anchor="w",
            pady=5
        )

        create_label(
            result_frame,
            f"Total Discount: Rs. {discount:,.2f}",
            16
        ).pack(
            anchor="w",
            pady=5
        )

        create_label(
            result_frame,
            f"Revenue / Sales: Rs. {revenue:,.2f}",
            18,
            True
        ).pack(
            anchor="w",
            pady=5
        )

        create_label(
            result_frame,
            f"Paid: Rs. {paid:,.2f}",
            16
        ).pack(
            anchor="w",
            pady=5
        )

        create_label(
            result_frame,
            f"Remaining Udhar: Rs. {remaining:,.2f}",
            18,
            True
        ).pack(
            anchor="w",
            pady=5
        )

        # PRODUCT-WISE SALES

        query = """
            SELECT
                si.product_code,
                p.product_name,
                SUM(si.quantity),
                SUM(si.total)
            FROM sale_items si
            LEFT JOIN products p
                ON si.product_code = p.product_code
            JOIN sales s
                ON si.sale_id = s.id
            WHERE 1 = 1
        """

        params = []

        if date:

            query += " AND s.date = ?"
            params.append(date)

        if product_code:

            query += " AND si.product_code = ?"
            params.append(product_code)

        query += """
            GROUP BY si.product_code, p.product_name
            ORDER BY SUM(si.quantity) DESC
        """

        cursor.execute(
            query,
            params
        )

        product_rows = cursor.fetchall()

        connection.close()

        create_label(
            result_frame,
            "Product-wise Sales",
            22,
            True
        ).pack(
            anchor="w",
            pady=(30, 15)
        )

        for (
            code,
            name,
            quantity,
            total
        ) in product_rows:

            card = ctk.CTkFrame(
                result_frame,
                fg_color=c["card2"],
                corner_radius=10
            )

            card.pack(
                fill="x",
                pady=5
            )

            create_label(
                card,
                f"{code}  |  {name or '-'}  |  "
                f"Qty Sold: {quantity}  |  "
                f"Sales: Rs. {total:,.2f}",
                14
            ).pack(
                padx=15,
                pady=12
            )

    ctk.CTkButton(
        filter_frame,
        text="Search Report",
        command=run_report,
        width=130
    ).pack(
        side="left",
        padx=5
    )

    ctk.CTkButton(
        filter_frame,
        text="Today",
        command=lambda: [
            date_entry.delete(
                0,
                "end"
            ),
            date_entry.insert(
                0,
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            ),
            run_report()
        ],
        width=90
    ).pack(
        side="left",
        padx=5
    )

    run_report()


# =========================================================
# SETTINGS
# =========================================================

def settings_page(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    c = colors()

    create_label(
        parent,
        "Settings",
        30,
        True
    ).pack(
        anchor="w",
        padx=30,
        pady=30
    )

    card = ctk.CTkFrame(
        parent,
        fg_color=c["card"],
        corner_radius=15
    )

    card.pack(
        fill="x",
        padx=30
    )

    create_label(
        card,
        "Change Admin Account",
        20,
        True
    ).pack(
        anchor="w",
        padx=25,
        pady=(25, 15)
    )

    # OLD USERNAME

    old_username = create_entry(
        card,
        "Old Username",
        300
    )

    old_username.pack(
        padx=25,
        pady=8
    )

    # OLD PASSWORD

    old_password = create_entry(
        card,
        "Old Password",
        300
    )

    old_password.configure(
        show="*"
    )

    old_password.pack(
        padx=25,
        pady=8
    )

    # NEW USERNAME

    new_username = create_entry(
        card,
        "New Username",
        300
    )

    new_username.pack(
        padx=25,
        pady=8
    )

    # NEW PASSWORD

    new_password = create_entry(
        card,
        "New Password",
        300
    )

    new_password.configure(
        show="*"
    )

    new_password.pack(
        padx=25,
        pady=8
    )

    # CONFIRM NEW PASSWORD

    confirm_password = create_entry(
        card,
        "Confirm New Password",
        300
    )

    confirm_password.configure(
        show="*"
    )

    confirm_password.pack(
        padx=25,
        pady=8
    )

    def update_account():

        old_u = old_username.get().strip()
        old_p = old_password.get().strip()

        new_u = new_username.get().strip()
        new_p = new_password.get().strip()
        confirm_p = confirm_password.get().strip()

        # CHECK ALL FIELDS

        if (
            not old_u
            or not old_p
            or not new_u
            or not new_p
            or not confirm_p
        ):

            messagebox.showerror(
                "Error",
                "Please fill all fields."
            )

            return

        # CHECK NEW PASSWORD

        if new_p != confirm_p:

            messagebox.showerror(
                "Error",
                "New password and confirm password do not match."
            )

            return

        connection = get_connection()
        cursor = connection.cursor()

        try:

            # VERIFY OLD USERNAME AND PASSWORD

            cursor.execute("""
                SELECT id
                FROM users
                WHERE username = ?
                AND password_hash = ?
                AND role = 'admin'
            """, (
                old_u,
                old_p
            ))

            admin = cursor.fetchone()

            if not admin:

                connection.close()

                messagebox.showerror(
                    "Error",
                    "Old username or password is incorrect."
                )

                return

            admin_id = admin[0]

            # CHECK IF NEW USERNAME ALREADY EXISTS

            cursor.execute("""
                SELECT id
                FROM users
                WHERE username = ?
                AND id != ?
            """, (
                new_u,
                admin_id
            ))

            existing_user = cursor.fetchone()

            if existing_user:

                connection.close()

                messagebox.showerror(
                    "Error",
                    "This username is already in use."
                )

                return

            # UPDATE ADMIN ACCOUNT

            cursor.execute("""
                UPDATE users
                SET username = ?,
                    password_hash = ?
                WHERE id = ?
                AND role = 'admin'
            """, (
                new_u,
                new_p,
                admin_id
            ))

            connection.commit()
            connection.close()

            # CLEAR FIELDS

            old_username.delete(
                0,
                "end"
            )

            old_password.delete(
                0,
                "end"
            )

            new_username.delete(
                0,
                "end"
            )

            new_password.delete(
                0,
                "end"
            )

            confirm_password.delete(
                0,
                "end"
            )

            messagebox.showinfo(
                "Success",
                "Admin username and password updated successfully."
            )

        except sqlite3.IntegrityError:

            connection.close()

            messagebox.showerror(
                "Error",
                "Username already exists."
            )

        except Exception as error:

            connection.rollback()
            connection.close()

            messagebox.showerror(
                "Database Error",
                str(error)
            )

    create_button(
        card,
        "Update Admin Account",
        update_account,
        220
    ).pack(
        padx=25,
        pady=20
    )

    create_label(
        card,
        "Default account: admin / admin123",
        13
    ).pack(
        padx=25,
        pady=(0, 25)
    )


# =========================================================
# START
# =========================================================

create_tables()
show_login()

window.mainloop()