# database.py
import sqlite3
import datetime
from datetime import datetime, timedelta
import logging
import csv
import io

logger = logging.getLogger(__name__)
DB_NAME = 'finance.db'

def init_db():
    """Inicializa o banco de dados com nova estrutura"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, 
                      nickname TEXT,
                      salario_liquido REAL,
                      data_cadastro TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      tipo_gasto TEXT,
                      categoria TEXT,
                      subcategoria TEXT,
                      amount REAL,
                      description TEXT,
                      date TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS custom_categories
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      tipo TEXT,
                      nome_categoria TEXT,
                      created_date TEXT)''')
        
        # NOVA TABELA: objetivos financeiros
        c.execute('''CREATE TABLE IF NOT EXISTS goals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      tipo TEXT,
                      descricao TEXT,
                      valor_meta REAL,
                      valor_atual REAL,
                      data_criacao TEXT,
                      data_conclusao TEXT,
                      concluido INTEGER DEFAULT 0)''')
        
        # NOVA TABELA: histórico de salários
        c.execute('''CREATE TABLE IF NOT EXISTS salary_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      salario_liquido REAL,
                      data_alteracao TEXT)''')
        
        conn.commit()
        conn.close()
        logger.info("Banco de dados SQLite inicializado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False

def add_user(user_id, nickname, salario_liquido=None):
    """Adiciona ou atualiza um usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, nickname, salario_liquido, data_cadastro) VALUES (?, ?, ?, ?)", 
                  (user_id, nickname, salario_liquido, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar usuário: {e}")
        return False

def update_user_salary(user_id, salario_liquido):
    """Atualiza o salário do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET salario_liquido = ? WHERE user_id = ?", 
                  (salario_liquido, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar salário: {e}")
        return False

def user_exists(user_id):
    """Verifica se o usuário já está cadastrado"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone() is not None
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Erro ao verificar usuário: {e}")
        return False

def get_user_data(user_id):
    """Obtém todos os dados do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT user_id, nickname, salario_liquido FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'nickname': result[1],
                'salario_liquido': result[2] if result[2] else 0.0
            }
        return None
    except Exception as e:
        logger.error(f"Erro ao obter dados do usuário: {e}")
        return None

def add_transaction(user_id, tipo_gasto, categoria, subcategoria, amount, description, date=None):
    """Adiciona uma transação com nova estrutura"""
    try:
        if date is None:
            date = datetime.now().strftime('%d/%m/%Y')
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, tipo_gasto, categoria, subcategoria, amount, description, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, tipo_gasto, categoria, subcategoria, amount, description, date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar transação: {e}")
        return False

def add_custom_category(user_id, tipo, nome_categoria):
    """Adiciona uma categoria personalizada"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO custom_categories (user_id, tipo, nome_categoria, created_date) VALUES (?, ?, ?, ?)",
                  (user_id, tipo, nome_categoria, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar categoria personalizada: {e}")
        return False

def get_custom_categories(user_id, tipo):
    """Obtém categorias personalizadas do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nome_categoria FROM custom_categories WHERE user_id=? AND tipo=?", (user_id, tipo))
        result = c.fetchall()
        conn.close()
        return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Erro ao obter categorias personalizadas: {e}")
        return []

def get_monthly_expenses(user_id, month=None, year=None):
    """Obtém gastos do mês para resumo"""
    try:
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        c.execute('''SELECT tipo_gasto, categoria, subcategoria, SUM(amount) 
                     FROM transactions 
                     WHERE user_id=? AND timestamp >= ? AND timestamp < ?
                     GROUP BY tipo_gasto, categoria, subcategoria''', 
                  (user_id, start_date, end_date))
        
        result = c.fetchall()
        conn.close()
        
        expenses = {'fixo': {}, 'flexivel': {}}
        for row in result:
            tipo, categoria, subcategoria, amount = row
            if categoria not in expenses[tipo]:
                expenses[tipo][categoria] = {}
            expenses[tipo][categoria][subcategoria] = amount
        
        return expenses
    except Exception as e:
        logger.error(f"Erro ao obter gastos mensais: {e}")
        return {'fixo': {}, 'flexivel': {}}

def get_user_nickname(user_id):
    """Obtém o apelido do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nickname FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else "Usuário"
    except Exception as e:
        logger.error(f"Erro ao obter nickname: {e}")
        return "Usuário"

def get_balance(user_id):
    """Calcula o saldo total do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT SUM(CASE WHEN tipo_gasto='flexivel' THEN -amount ELSE 0 END) + SUM(CASE WHEN tipo_gasto='fixo' THEN -amount ELSE 0 END) FROM transactions WHERE user_id=?", (user_id,))
        result = c.fetchone()[0]
        conn.close()
        return result or 0.0
    except Exception as e:
        logger.error(f"Erro ao calcular saldo: {e}")
        return 0.0

def get_statement(user_id, limit=10):
    """Obtém o extrato do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT tipo_gasto, categoria, amount, description, date FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", 
                  (user_id, limit))
        result = c.fetchall()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Erro ao obter extrato: {e}")
        return []

# NOVAS FUNÇÕES PARA OBJETIVOS
def add_goal(user_id, tipo, descricao, valor_meta, valor_atual=0):
    """Adiciona um novo objetivo financeiro"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO goals (user_id, tipo, descricao, valor_meta, valor_atual, data_criacao) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, tipo, descricao, valor_meta, valor_atual, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar objetivo: {e}")
        return False

def get_goals(user_id):
    """Obtém todos os objetivos do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, tipo, descricao, valor_meta, valor_atual, data_criacao, concluido FROM goals WHERE user_id=? ORDER BY data_criacao DESC", (user_id,))
        result = c.fetchall()
        conn.close()
        
        goals = []
        for row in result:
            goals.append({
                'id': row[0],
                'tipo': row[1],
                'descricao': row[2],
                'valor_meta': row[3],
                'valor_atual': row[4],
                'data_criacao': row[5],
                'concluido': bool(row[6])
            })
        return goals
    except Exception as e:
        logger.error(f"Erro ao obter objetivos: {e}")
        return []

def update_goal_progress(goal_id, valor_atual):
    """Atualiza o progresso de um objetivo"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE goals SET valor_atual = ? WHERE id = ?", (valor_atual, goal_id))
        
        # Verificar se objetivo foi concluído
        c.execute("SELECT valor_meta, valor_atual FROM goals WHERE id = ?", (goal_id,))
        meta, atual = c.fetchone()
        if atual >= meta:
            c.execute("UPDATE goals SET concluido = 1, data_conclusao = ? WHERE id = ?", 
                     (datetime.now().strftime('%Y-%m-%d'), goal_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar objetivo: {e}")
        return False

def delete_goal(goal_id):
    """Exclui um objetivo"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao excluir objetivo: {e}")
        return False

# NOVAS FUNÇÕES PARA HISTÓRICO DE SALÁRIOS
def add_salary_history(user_id, salario_liquido):
    """Adiciona registro no histórico de salários"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO salary_history (user_id, salario_liquido, data_alteracao) VALUES (?, ?, ?)",
                  (user_id, salario_liquido, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar histórico de salário: {e}")
        return False

def get_salary_history(user_id, limit=5):
    """Obtém histórico de salários do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT salario_liquido, data_alteracao FROM salary_history WHERE user_id=? ORDER BY data_alteracao DESC LIMIT ?", 
                  (user_id, limit))
        result = c.fetchall()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Erro ao obter histórico de salários: {e}")
        return []

# NOVA FUNÇÃO: Exportar dados para CSV
def export_user_data(user_id):
    """Exporta todos os dados do usuário para formato CSV"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Dados do usuário
        c.execute("SELECT nickname, salario_liquido, data_cadastro FROM users WHERE user_id=?", (user_id,))
        user_data = c.fetchone()
        
        # Transações
        c.execute('''SELECT tipo_gasto, categoria, subcategoria, amount, description, date, timestamp 
                     FROM transactions WHERE user_id=? ORDER BY timestamp DESC''', (user_id,))
        transactions = c.fetchall()
        
        # Objetivos
        c.execute("SELECT tipo, descricao, valor_meta, valor_atual, data_criacao, concluido FROM goals WHERE user_id=?", (user_id,))
        goals = c.fetchall()
        
        conn.close()
        
        return {
            'user_data': user_data,
            'transactions': transactions,
            'goals': goals
        }
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        return None

# NOVA FUNÇÃO: Resetar dados do usuário
def reset_user_data(user_id):
    """Remove todos os dados do usuário (exceto cadastro básico)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Manter apenas dados básicos do usuário, remover todo o resto
        c.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM custom_categories WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM goals WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM salary_history WHERE user_id=?", (user_id,))
        
        # Resetar salário para NULL
        c.execute("UPDATE users SET salario_liquido = NULL WHERE user_id=?", (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao resetar dados: {e}")
        return False