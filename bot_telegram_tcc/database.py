import sqlite3
import datetime

DB_NAME = 'finance.db'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de usuários (versão simplificada)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  nickname TEXT)''')
    
    # Tabela de transações
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  type TEXT,
                  amount REAL,
                  description TEXT,
                  date TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados SQLite inicializado!")

def add_user(user_id, nickname):
    """Adiciona ou atualiza um usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, nickname) VALUES (?, ?)", 
              (user_id, nickname))
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
    c.execute("SELECT user_id, nickname FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'user_id': result[0],
            'nickname': result[1]
        }
    return None

def add_transaction(user_id, type, amount, description, date=None):
    """Adiciona uma transação (crédito ou débito)"""
    if date is None:
        date = datetime.datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)",
              (user_id, type, amount, description, date))
    conn.commit()
    conn.close()

def get_balance(user_id):
    """Calcula o saldo total do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT SUM(CASE WHEN type='credit' THEN amount ELSE -amount END) FROM transactions WHERE user_id=?", (user_id,))
    result = c.fetchone()[0]
    conn.close()
    return result or 0.0

def get_statement(user_id, limit=10):
    """Obtém o extrato do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT type, amount, description, date FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", 
              (user_id, limit))
    result = c.fetchall()
    conn.close()
    return result

def get_user_nickname(user_id):
    """Obtém o apelido do usuário"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nickname FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Usuário"