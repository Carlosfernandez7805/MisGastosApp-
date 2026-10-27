import sqlite3
import os

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de gastos (con campo de tags)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            currency TEXT,
            tags TEXT DEFAULT ''
        )
    ''')
    
    # Detectar si la columna 'tags' falta (para apps ya instaladas)
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'tags' not in columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN tags TEXT DEFAULT ''")

    # Tabla de Categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    # Insertar categorías por defecto si está vacía
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_cats = ['General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros']
        for cat in default_cats:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))

    # Otras tablas
    cursor.execute('''CREATE TABLE IF NOT EXISTS recurring_expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, category TEXT, day INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS savings_goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, target REAL, saved REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, person TEXT, amount REAL, type TEXT, status TEXT DEFAULT 'pending')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS incomes (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (category TEXT PRIMARY KEY, limit_amount REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT, salary REAL, pin TEXT, tutorial_shown INTEGER DEFAULT 0)''')

    conn.commit()
    conn.close()

def get_all_categories(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name ASC")
    cats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cats

def add_custom_category(db_path, name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def delete_category(db_path, name):
    if name in ['General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros']:
        return False 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return True

def add_expense(db_path, description, amount, created_at, category, currency='COP', tags=''):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (description, amount, created_at, category, currency, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (description, amount, created_at, category, currency, tags))
    conn.commit()
    conn.close()

def get_expenses_for_month(db_path, year_month, search_text=""):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT id, created_at, description, amount, category, currency, tags FROM expenses WHERE strftime('%Y-%m', created_at) = ?"
    params = [year_month]
    
    if search_text:
        query += " AND (description LIKE ? OR category LIKE ? OR tags LIKE ?)"
        search_param = f"%{search_text}%"
        params.extend([search_param, search_param, search_param])
        
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_expense(db_path, expense_id, description, amount, category, tags):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expenses SET description=?, amount=?, category=?, tags=? WHERE id=?
    ''', (description, amount, category, tags, expense_id))
    conn.commit()
    conn.close()

def delete_expense(db_path, expense_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def totals_for_period(db_path, start_date, end_date):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(amount) FROM expenses 
        WHERE date(created_at) >= date(?) AND date(created_at) <= date(?)
    ''', (start_date, end_date))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_available_months(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT strftime('%Y-%m', created_at) FROM expenses ORDER BY created_at DESC")
    months = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return months

def get_totals_for_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', created_at) = ?", (year_month,))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_expenses_by_category_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, SUM(amount) FROM expenses 
        WHERE strftime('%Y-%m', created_at) = ?
        GROUP BY category
    ''', (year_month,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_expenses_for_date_range(db_path, start_date, end_date, search_text=""):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT id, created_at, description, amount, category, currency, tags FROM expenses WHERE date(created_at) >= date(?) AND date(created_at) <= date(?)"
    params = [start_date, end_date]
    
    if search_text:
        query += " AND (description LIKE ? OR category LIKE ? OR tags LIKE ?)"
        search_param = f"%{search_text}%"
        params.extend([search_param, search_param, search_param])
        
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

# GASTOS RECURRENTES
def add_recurring_expense(db_path, description, amount, category, day):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recurring_expenses (description, amount, category, day) VALUES (?, ?, ?, ?)", (description, amount, category, day))
    conn.commit()
    conn.close()

def get_recurring_expenses(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, category, day FROM recurring_expenses ORDER BY day ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_recurring_expense(db_path, r_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recurring_expenses WHERE id = ?", (r_id,))
    conn.commit()
    conn.close()

def process_recurring_expenses(db_path):
    pass # Placeholder for future implementation

# METAS
def add_savings_goal(db_path, name, target):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO savings_goals (name, target, saved) VALUES (?, ?, 0)", (name, target))
    conn.commit()
    conn.close()

def get_savings_goals(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, target, saved FROM savings_goals")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_to_savings_goal(db_path, goal_id, amount):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE savings_goals SET saved = saved + ? WHERE id = ?", (amount, goal_id))
    conn.commit()
    conn.close()

def delete_savings_goal(db_path, goal_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

def get_total_saved(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(saved) FROM savings_goals")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# DEUDAS
def add_debt(db_path, person, amount, type_d):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO debts (person, amount, type, status) VALUES (?, ?, ?, 'pending')", (person, amount, type_d))
    conn.commit()
    conn.close()

def get_debts(db_path, status):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, person, amount, type, 'pending' FROM debts WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_debt_status(db_path, debt_id, status):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE debts SET status = ? WHERE id = ?", (status, debt_id))
    conn.commit()
    conn.close()

def delete_debt(db_path, debt_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
    conn.commit()
    conn.close()

def get_total_debts(db_path, type_d):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM debts WHERE status = 'pending' AND type = ?", (type_d,))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# INGRESOS
def add_income(db_path, description, amount, date):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO incomes (description, amount, date) VALUES (?, ?, ?)", (description, amount, date))
    conn.commit()
    conn.close()

def get_income_for_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM incomes WHERE strftime('%Y-%m', date) = ?", (year_month,))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_all_incomes_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, date FROM incomes WHERE strftime('%Y-%m', date) = ? ORDER BY date DESC", (year_month,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_income(db_path, income_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incomes WHERE id = ?", (income_id,))
    conn.commit()
    conn.close()

# PRESUPUESTOS
def save_category_budget(db_path, category, limit_amount):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO budgets (category, limit_amount) VALUES (?, ?)", (category, limit_amount))
    conn.commit()
    conn.close()

def get_category_budget(db_path, category):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT limit_amount FROM budgets WHERE category = ?", (category,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_all_category_budgets(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category, limit_amount FROM budgets")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_category_expense(db_path, year_month, category):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', created_at) = ? AND category = ?", (year_month, category))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# USUARIO
def save_user_email(db_path, email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email, row[0]))
    else:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

def get_user_email(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def save_user_salary(db_path, salary):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET salary = ? WHERE id = ?", (salary, row[0]))
    else:
        cursor.execute("INSERT INTO users (salary) VALUES (?)", (salary,))
    conn.commit()
    conn.close()

def get_user_salary(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT salary FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0

def save_user_pin(db_path, pin):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET pin = ? WHERE id = ?", (pin, row[0]))
    else:
        cursor.execute("INSERT INTO users (pin) VALUES (?)", (pin,))
    conn.commit()
    conn.close()

def get_user_pin(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT pin FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def save_tutorial_shown(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET tutorial_shown = 1 WHERE id = ?", (row[0],))
    else:
        cursor.execute("INSERT INTO users (tutorial_shown) VALUES (1)")
    conn.commit()
    conn.close()

# ... (al final de tu database.py) ...

def save_user_theme(db_path, is_dark):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    row = cursor.fetchone()
    val = 1 if is_dark else 0
    if row:
        cursor.execute("UPDATE users SET tema_oscuro = ? WHERE id = ?", (val, row[0]))
    else:
        cursor.execute("INSERT INTO users (tema_oscuro) VALUES (?)", (val,))
    conn.commit()
    conn.close()

def get_user_theme(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Si la columna no existe, la creamos
    try:
        cursor.execute("SELECT tema_oscuro FROM users LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return bool(row[0]) if row else False
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN tema_oscuro INTEGER DEFAULT 0")
        conn.commit()
        conn.close()
        return False

def get_tutorial_shown(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT tutorial_shown FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0
