import sqlite3
from datetime import datetime

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                description TEXT NOT NULL,
                amount INTEGER NOT NULL,
                category TEXT DEFAULT 'General',
                currency TEXT DEFAULT 'COP'
            )
        ''')
        cur = conn.execute("PRAGMA table_info(expenses)")
        columns = [row[1] for row in cur.fetchall()]
        if 'category' not in columns:
            conn.execute("ALTER TABLE expenses ADD COLUMN category TEXT DEFAULT 'General'")
        if 'currency' not in columns:
            conn.execute("ALTER TABLE expenses ADD COLUMN currency TEXT DEFAULT 'COP'")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount INTEGER NOT NULL,
                category TEXT DEFAULT 'General',
                day_of_month INTEGER NOT NULL,
                last_processed TEXT DEFAULT ''
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target INTEGER NOT NULL,
                saved INTEGER DEFAULT 0
            )
        ''')

        # Tabla de Deudas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person TEXT NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # MIGRACIÓN: Revisar si la columna 'status' existe en la tabla 'debts'
        cur_debts = conn.execute("PRAGMA table_info(debts)")
        cols_debts = [row[1] for row in cur_debts.fetchall()]
        if 'status' not in cols_debts:
            conn.execute("ALTER TABLE debts ADD COLUMN status TEXT DEFAULT 'pending'")

        # Tabla de Ingresos Extra
        conn.execute('''
            CREATE TABLE IF NOT EXISTS incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # Tabla de Presupuestos por Categoría
        conn.execute('''
            CREATE TABLE IF NOT EXISTS category_budgets (
                category TEXT PRIMARY KEY,
                amount INTEGER NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def add_expense(db_path, description, amount, created_at, category="General", currency="COP"):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            'INSERT INTO expenses (created_at, description, amount, category, currency) VALUES (?, ?, ?, ?, ?)',
            (created_at, description, int(amount), category, currency),
        )
        conn.commit()
    finally:
        conn.close()

def delete_expense(db_path, expense_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
    finally:
        conn.close()

def update_expense(db_path, expense_id, description, amount, category):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            'UPDATE expenses SET description = ?, amount = ?, category = ? WHERE id = ?',
            (description, int(amount), category, expense_id),
        )
        conn.commit()
    finally:
        conn.close()

def totals_for_period(db_path, start_date, end_date):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses "
            "WHERE date(created_at) BETWEEN ? AND ? AND currency = 'COP'",
            (start_date, end_date),
        )
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()

def get_available_months(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT DISTINCT substr(created_at, 1, 7) FROM expenses ORDER BY created_at DESC")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_totals_for_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE substr(created_at, 1, 7) = ? AND currency = 'COP'", (year_month,))
        return cur.fetchone()[0]
    finally:
        conn.close()

def get_expenses_for_month(db_path, year_month, search_text=""):
    conn = sqlite3.connect(db_path)
    try:
        query = "SELECT id, created_at, description, amount, category, currency FROM expenses WHERE substr(created_at, 1, 7) = ?"
        params = [year_month]
        if search_text:
            query += " AND (description LIKE ? OR category LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        query += " ORDER BY id DESC LIMIT 50"
        cur = conn.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

def get_expenses_for_date_range(db_path, start_date, end_date, search_text=""):
    conn = sqlite3.connect(db_path)
    try:
        query = "SELECT id, created_at, description, amount, category, currency FROM expenses WHERE date(created_at) BETWEEN ? AND ?"
        params = [start_date, end_date]
        if search_text:
            query += " AND (description LIKE ? OR category LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        query += " ORDER BY id DESC LIMIT 100"
        cur = conn.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

def get_expenses_by_category_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT category, SUM(amount) FROM expenses "
            "WHERE substr(created_at, 1, 7) = ? AND currency = 'COP' "
            "GROUP BY category ORDER BY SUM(amount) DESC",
            (year_month,),
        )
        return cur.fetchall()
    finally:
        conn.close()

def get_total_category_expense(db_path, year_month, category):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses "
            "WHERE substr(created_at, 1, 7) = ? AND category = ? AND currency = 'COP'",
            (year_month, category),
        )
        return cur.fetchone()[0]
    finally:
        conn.close()

# --- INGRESOS EXTRA ---
def add_income(db_path, description, amount, created_at):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT INTO incomes (description, amount, created_at) VALUES (?, ?, ?)', (description, int(amount), created_at))
        conn.commit()
    finally:
        conn.close()

def get_income_for_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes WHERE substr(created_at, 1, 7) = ?", (year_month,))
        return cur.fetchone()[0]
    finally:
        conn.close()

def get_all_incomes_month(db_path, year_month):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT id, description, amount, created_at FROM incomes WHERE substr(created_at, 1, 7) = ? ORDER BY id DESC", (year_month,))
        return cur.fetchall()
    finally:
        conn.close()

def delete_income(db_path, income_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DELETE FROM incomes WHERE id = ?', (income_id,))
        conn.commit()
    finally:
        conn.close()

# --- PRESUPUESTOS POR CATEGORIA ---
def save_category_budget(db_path, category, amount):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT OR REPLACE INTO category_budgets (category, amount) VALUES (?, ?)', (category, int(amount)))
        conn.commit()
    finally:
        conn.close()

def get_category_budget(db_path, category):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT amount FROM category_budgets WHERE category = ?", (category,))
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()

def get_all_category_budgets(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT category, amount FROM category_budgets")
        return cur.fetchall()
    finally:
        conn.close()

# --- GASTOS RECURRENTES ---
def add_recurring_expense(db_path, description, amount, category, day_of_month):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT INTO recurring_expenses (description, amount, category, day_of_month) VALUES (?, ?, ?, ?)', (description, int(amount), category, int(day_of_month)))
        conn.commit()
    finally:
        conn.close()

def get_recurring_expenses(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT id, description, amount, category, day_of_month FROM recurring_expenses')
        return cur.fetchall()
    finally:
        conn.close()

def delete_recurring_expense(db_path, rec_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DELETE FROM recurring_expenses WHERE id = ?', (rec_id,))
        conn.commit()
    finally:
        conn.close()

def process_recurring_expenses(db_path):
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    current_day = now.day
    today_str = now.isoformat(timespec='seconds')
    alertas = []
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT id, description, amount, category, day_of_month, last_processed FROM recurring_expenses')
        recurrentes = cur.fetchall()
        
        for r_id, desc, amount, cat, day, last_proc in recurrentes:
            if current_day >= day and last_proc != current_month:
                conn.execute('INSERT INTO expenses (created_at, description, amount, category) VALUES (?, ?, ?, ?)', (today_str, f"[Fijo] {desc}", int(amount), cat))
                conn.execute('UPDATE recurring_expenses SET last_processed = ? WHERE id = ?', (current_month, r_id))
            
            dias_faltantes = day - current_day
            if 0 < dias_faltantes <= 2:
                alertas.append(f"En {dias_faltantes} día(s) se cobra: {desc} ({amount})")
        conn.commit()
        return alertas
    finally:
        conn.close()

# --- METAS DE AHORRO ---
def add_savings_goal(db_path, name, target):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT INTO savings_goals (name, target, saved) VALUES (?, ?, 0)', (name, int(target)))
        conn.commit()
    finally:
        conn.close()

def get_savings_goals(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT id, name, target, saved FROM savings_goals')
        return cur.fetchall()
    finally:
        conn.close()

def add_to_savings_goal(db_path, goal_id, amount):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('UPDATE savings_goals SET saved = saved + ? WHERE id = ?', (int(amount), goal_id))
        conn.commit()
    finally:
        conn.close()

def delete_savings_goal(db_path, goal_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DELETE FROM savings_goals WHERE id = ?', (goal_id,))
        conn.commit()
    finally:
        conn.close()

def get_total_saved(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT COALESCE(SUM(saved), 0) FROM savings_goals')
        return cur.fetchone()[0]
    finally:
        conn.close()

# --- DEUDAS ---
def add_debt(db_path, person, amount, type_debt, description=""):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT INTO debts (person, amount, type, description) VALUES (?, ?, ?, ?)', (person, int(amount), type_debt, description))
        conn.commit()
    finally:
        conn.close()

def get_debts(db_path, status="pending"):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT id, person, amount, type, description FROM debts WHERE status = ? ORDER BY id DESC', (status,))
        return cur.fetchall()
    finally:
        conn.close()

def update_debt_status(db_path, debt_id, status):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('UPDATE debts SET status = ? WHERE id = ?', (status, debt_id))
        conn.commit()
    finally:
        conn.close()

def delete_debt(db_path, debt_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DELETE FROM debts WHERE id = ?', (debt_id,))
        conn.commit()
    finally:
        conn.close()

def get_total_debts(db_path, type_debt):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM debts WHERE type = ? AND status = "pending"', (type_debt,))
        return cur.fetchone()[0]
    finally:
        conn.close()

# --- CONFIGURACIÓN Y TUTORIAL ---
def save_user_email(db_path, email):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('user_email', email))
        conn.commit()
    finally:
        conn.close()

def get_user_email(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT value FROM config WHERE key = 'user_email'")
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def save_user_salary(db_path, salary):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('user_salary', str(salary)))
        conn.commit()
    finally:
        conn.close()

def get_user_salary(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT value FROM config WHERE key = 'user_salary'")
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()

def save_user_pin(db_path, pin):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('user_pin', str(pin)))
        conn.commit()
    finally:
        conn.close()

def get_user_pin(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT value FROM config WHERE key = 'user_pin'")
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def save_tutorial_shown(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('tutorial_shown', '1'))
        conn.commit()
    finally:
        conn.close()

def get_tutorial_shown(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT value FROM config WHERE key = 'tutorial_shown'")
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()
