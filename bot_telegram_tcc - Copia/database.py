import sqlite3
import datetime

DB_NAME = 'finance.db'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  nickname TEXT,
                  salary REAL,
                  created_date TEXT)''')
    
    # Tabela de transações
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  type TEXT,
                  category TEXT,
                  subcategory TEXT,
                  amount REAL,
                  description TEXT,
                  date TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados SQLite inicializado!")

def add_user(user_id, nickname, salary=None):
    """Adiciona ou atualiza um usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if salary:
        c.execute("INSERT OR REPLACE INTO users (user_id, nickname, salary, created_date) VALUES (?, ?, ?, ?)", 
                  (user_id, nickname, salary, datetime.datetime.now().strftime('%d/%m/%Y')))
    else:
        c.execute("INSERT OR REPLACE INTO users (user_id, nickname, created_date) VALUES (?, ?, ?)", 
                  (user_id, nickname, datetime.datetime.now().strftime('%d/%m/%Y')))
    conn.commit()
    conn.close()

def update_user_salary(user_id, salary):
    """Atualiza o salário do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET salary = ? WHERE user_id = ?", (salary, user_id))
    conn.commit()
    conn.close()

def user_exists(user_id):
    """Verifica se o usuário já está cadastrado"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def get_user_data(user_id):
    """Obtém todos os dados do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, nickname, salary FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'user_id': result[0],
            'nickname': result[1],
            'salary': result[2] if result[2] is not None else 0
        }
    return None

def add_transaction(user_id, type, category, subcategory, amount, description, date=None):
    """Adiciona uma transação"""
    if date is None:
        date = datetime.datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, type, category, subcategory, amount, description, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, type, category, subcategory, amount, description, date))
    conn.commit()
    conn.close()

def get_monthly_transactions(user_id, month_year=None):
    """Obtém transações do mês"""
    if month_year is None:
        month_year = datetime.datetime.now().strftime('%m/%Y')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT type, category, subcategory, amount, date, description 
                 FROM transactions 
                 WHERE user_id=? AND substr(date, 4, 7)=? 
                 ORDER BY date DESC''', 
              (user_id, month_year))
    result = c.fetchall()
    conn.close()
    return result

def get_transactions_summary(user_id, month_year=None):
    """Obtém resumo das transações por categoria"""
    transactions = get_monthly_transactions(user_id, month_year)
    
    fixed_expenses = {}
    flexible_expenses = {}
    total_fixed = 0
    total_flexible = 0
    
    for transaction in transactions:
        type_, category, subcategory, amount, date, description = transaction
        
        if type_ == 'fixed':
            if subcategory not in fixed_expenses:
                fixed_expenses[subcategory] = 0
            fixed_expenses[subcategory] += amount
            total_fixed += amount
        else:
            if subcategory not in flexible_expenses:
                flexible_expenses[subcategory] = 0
            flexible_expenses[subcategory] += amount
            total_flexible += amount
    
    return {
        'fixed_expenses': fixed_expenses,
        'flexible_expenses': flexible_expenses,
        'total_fixed': total_fixed,
        'total_flexible': total_flexible,
        'total_expenses': total_fixed + total_flexible
    }

def get_user_nickname(user_id):
    """Obtém o apelido do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nickname FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Usuário"