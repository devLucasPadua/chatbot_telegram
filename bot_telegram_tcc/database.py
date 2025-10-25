import sqlite3
import datetime
from datetime import datetime, timedelta

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
        date = datetime.now().strftime('%d/%m/%Y')
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

# --- FUNÇÕES ADICIONAIS PARA O COACH (OPCIONAIS) ---

def get_monthly_summary(user_id, year, month):
    """Obtém resumo mensal para análises mais avançadas (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{month+1:02d}-01"
    
    c.execute('''SELECT type, SUM(amount) 
                 FROM transactions 
                 WHERE user_id=? AND timestamp >= ? AND timestamp < ?
                 GROUP BY type''', 
              (user_id, start_date, end_date))
    
    result = c.fetchall()
    conn.close()
    
    summary = {'credit': 0, 'debit': 0}
    for row in result:
        summary[row[0]] = row[1] or 0
    
    return summary

def get_transactions_by_period(user_id, days=30):
    """Obtém transações de um período específico (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''SELECT type, amount, description, date, timestamp 
                 FROM transactions 
                 WHERE user_id=? AND timestamp >= ?
                 ORDER BY timestamp DESC''', 
              (user_id, since_date))
    
    transactions = c.fetchall()
    conn.close()
    return transactions

def get_expense_categories(user_id, days=30):
    """Analisa categorias de gastos (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''SELECT description, SUM(amount) 
                 FROM transactions 
                 WHERE user_id=? AND type='debit' AND timestamp >= ?
                 GROUP BY description''', 
              (user_id, since_date))
    
    expenses = c.fetchall()
    conn.close()
    
    # Categorização simplificada
    categories = {}
    for desc, amount in expenses:
        category = categorize_expense(desc)
        categories[category] = categories.get(category, 0) + amount
    
    return categories

def categorize_expense(description):
    """Categoriza despesas baseado na descrição (OPCIONAL)"""
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ['mercado', 'supermercado', 'alimentação', 'comida']):
        return 'alimentação'
    elif any(word in desc_lower for word in ['aluguel', 'luz', 'água', 'energia', 'internet']):
        return 'moradia'
    elif any(word in desc_lower for word in ['transporte', 'gasolina', 'uber', 'ônibus']):
        return 'transporte'
    elif any(word in desc_lower for word in ['restaurante', 'ifood', 'delivery', 'lanche']):
        return 'alimentação_externa'
    else:
        return 'outros'

# --- NOVAS TABELAS PARA VERSÃO AVANÇADA DO COACH (OPCIONAIS) ---

def init_advanced_tables():
    """Inicializa tabelas avançadas para tracking educacional (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela para acompanhar progresso educacional
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  concept_learned TEXT,
                  learning_date TEXT,
                  confidence_level INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    # Tabela para metas financeiras
    c.execute('''CREATE TABLE IF NOT EXISTS financial_goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  goal_name TEXT,
                  target_amount REAL,
                  current_amount REAL,
                  deadline TEXT,
                  created_date TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    # Tabela para dicas personalizadas
    c.execute('''CREATE TABLE IF NOT EXISTS user_tips
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  tip_text TEXT,
                  tip_category TEXT,
                  shown_date TEXT,
                  understood BOOLEAN,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()
    print("✅ Tabelas avançadas do coach inicializadas!")

def add_learning_progress(user_id, concept, confidence=1):
    """Registra progresso de aprendizado (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO user_progress (user_id, concept_learned, learning_date, confidence_level) VALUES (?, ?, ?, ?)",
              (user_id, concept, datetime.now().strftime('%Y-%m-%d'), confidence))
    conn.commit()
    conn.close()

def add_financial_goal(user_id, goal_name, target_amount, deadline):
    """Adiciona uma meta financeira (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO financial_goals (user_id, goal_name, target_amount, current_amount, deadline, created_date) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, goal_name, target_amount, 0, deadline, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

def get_user_goals(user_id):
    """Obtém metas do usuário (OPCIONAL)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT goal_name, target_amount, current_amount, deadline FROM financial_goals WHERE user_id=?", (user_id,))
    result = c.fetchall()
    conn.close()
    return result

# --- ATUALIZAÇÃO DA FUNÇÃO INIT_DB PARA INCLUIR TABELAS AVANÇADAS ---

def init_db_complete():
    """Inicializa o banco de dados completo com todas as tabelas"""
    init_db()  # Inicializa tabelas básicas
    init_advanced_tables()  # Inicializa tabelas avançadas (opcionais)