import sqlite3
import os

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de gastos original (con campo de tags)
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

    # ... (AQUÍ DEBES MANTENER EL RESTO DE TUS TABLAS: recurring, savings, debts, etc.) ...
    cursor.execute('''CREATE TABLE IF NOT EXISTS recurring_expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, category TEXT, day INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS savings_goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, target REAL, saved REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, person TEXT, amount REAL, type TEXT, status TEXT DEFAULT 'pending')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS incomes (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (category TEXT PRIMARY KEY, limit_amount REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT, salary REAL, pin TEXT, tutorial_shown INTEGER DEFAULT 0)''')

    conn.commit()
    conn.close()

# --- NUEVAS FUNCIONES PARA CATEGORÍAS ---
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
        return False # Ya existe
    finally:
        conn.close()

def delete_category(db_path, name):
    if name in ['General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros']:
        return False # Proteger las básicas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return True

# --- ACTUALIZACIÓN DE GASTOS CON ETIQUETAS (TAGS) ---
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

# (Asegúrate de mantener tus otras funciones como totals_for_period, delete_expense, etc., igual que antes)
