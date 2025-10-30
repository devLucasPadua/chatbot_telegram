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
        
        c.execute('''CREATE TABLE IF NOT EXISTS salary_history
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        salario_liquido REAL,
        data_alteracao TEXT)''')
        
        # Na função init_db(), adicione:
        c.execute('''CREATE TABLE IF NOT EXISTS salaries
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     origem TEXT,
                     valor REAL,
                     principal INTEGER DEFAULT 0,
                     data_criacao TEXT)''')
                     
        # Na função init_db(), adicione:
        c.execute('''CREATE TABLE IF NOT EXISTS extra_incomes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      origem TEXT,
                      valor REAL,
                      data_criacao TEXT)''')
        
        conn.commit()
        conn.close()
        
        # Atualizar estrutura da tabela goals se necessário
        update_goals_table()
        
        logger.info("✅ Tabela 'salaries' verificada/criada com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        return False
        
        logger.info("Banco de dados SQLite inicializado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False
        
# Função auxiliar para debug
def debug_salaries(user_id):
    """Função de debug para verificar salários"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM salaries WHERE user_id=?", (user_id,))
        result = c.fetchall()
        conn.close()
        print(f"DEBUG Salários para user {user_id}: {result}")
        return result
    except Exception as e:
        print(f"DEBUG Erro: {e}")
        return []

def create_sample_salaries(user_id):
    """Cria salários de exemplo para testes"""
    try:
        # Salário principal
        add_salary(user_id, "Salário Principal", 3000.00, principal=True)
        # Salários extras
        add_salary(user_id, "Freelance", 800.00, principal=False)
        add_salary(user_id, "Aluguel", 1200.00, principal=False)
        print("✅ Salários de exemplo criados!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar salários de exemplo: {e}")
        return False
   
def add_extra_income(user_id, origem, valor):
    """Adiciona uma nova renda extra"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO extra_incomes (user_id, origem, valor, data_criacao) VALUES (?, ?, ?, ?)",
                 (user_id, origem, valor, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar renda extra: {e}")
        return False

def get_extra_incomes(user_id):
    """Obtém todas as rendas extras do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, origem, valor, data_criacao FROM extra_incomes WHERE user_id=? ORDER BY data_criacao DESC", (user_id,))
        result = c.fetchall()
        conn.close()
        
        incomes = []
        for row in result:
            incomes.append({
                'id': row[0],
                'origem': row[1],
                'valor': row[2],
                'data_criacao': row[3]
            })
        return incomes
    except Exception as e:
        logger.error(f"Erro ao obter rendas extras: {e}")
        return []

def update_extra_income(income_id, origem=None, valor=None):
    """Atualiza uma renda extra"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if origem and valor:
            c.execute("UPDATE extra_incomes SET origem=?, valor=? WHERE id=?", (origem, valor, income_id))
        elif origem:
            c.execute("UPDATE extra_incomes SET origem=? WHERE id=?", (origem, income_id))
        elif valor:
            c.execute("UPDATE extra_incomes SET valor=? WHERE id=?", (valor, income_id))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar renda extra: {e}")
        return False

def delete_extra_income(income_id):
    """Exclui uma renda extra"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM extra_incomes WHERE id=?", (income_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao excluir renda extra: {e}")
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

def get_user_nickname(user_id):
    """Obtém o apelido do usuário de forma segura"""
    try:
        user_data = get_user_data(user_id)
        if user_data and user_data['nickname']:
            return user_data['nickname']
        return "Usuário"
    except Exception as e:
        logger.error(f"Erro ao obter nickname: {e}")
        return "Usuário"

def get_all_transactions(user_id):
    """Obtém todas as transações do usuário para o extrato completo"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT 
                    tipo_gasto, 
                    categoria, 
                    subcategoria,
                    amount, 
                    description, 
                    date,
                    timestamp
                 FROM transactions 
                 WHERE user_id=? 
                 ORDER BY timestamp DESC''', (user_id,))
        
        result = c.fetchall()
        conn.close()
        
        transactions = []
        for row in result:
            transactions.append({
                'tipo': row[0],
                'categoria': row[1],
                'subcategoria': row[2],
                'valor': row[3],
                'descricao': row[4],
                'data': row[5],
                'timestamp': row[6]
            })
            
        return transactions
    except Exception as e:
        logger.error(f"Erro ao obter todas as transações: {e}")
        return []
        
def get_category_expenses(user_id, tipo, categoria):
    """Obtém todos os gastos de uma categoria específica"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT amount, description, date 
                 FROM transactions 
                 WHERE user_id=? AND tipo_gasto=? AND categoria=?
                 ORDER BY timestamp DESC''', 
                 (user_id, tipo, categoria))
        
        result = c.fetchall()
        conn.close()
        
        gastos = []
        for row in result:
            gastos.append({
                'valor': row[0],
                'descricao': row[1],
                'data': row[2]
            })
            
        return gastos
    except Exception as e:
        logger.error(f"Erro ao obter gastos da categoria: {e}")
        return []

def update_user_name(user_id, new_name):
    """Atualiza o nome do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET nickname = ? WHERE user_id = ?", 
                 (new_name, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar nome do usuário: {e}")
        return False

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

def add_goal(user_id, tipo, descricao, valor_meta, prazo, valor_atual=0):
    """Adiciona um novo objetivo financeiro - VERSÃO CORRIGIDA"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Verificar se a tabela tem a coluna 'prazo'
        c.execute("PRAGMA table_info(goals)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'prazo' in columns:
            # Se a coluna 'prazo' existe, usar a nova estrutura
            c.execute("INSERT INTO goals (user_id, tipo, descricao, valor_meta, valor_atual, data_criacao, prazo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, tipo, descricao, valor_meta, valor_atual, datetime.now().strftime('%Y-%m-%d'), prazo))
        else:
            # Se não existe, usar estrutura antiga (para compatibilidade)
            c.execute("INSERT INTO goals (user_id, tipo, descricao, valor_meta, valor_atual, data_criacao) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, tipo, descricao, valor_meta, valor_atual, datetime.now().strftime('%Y-%m-%d')))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar objetivo: {e}")
        return False
        
def fix_goals_data():
    """Corrige dados inconsistentes na tabela goals"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Verificar se há valores não numéricos em valor_atual
        c.execute("SELECT id, valor_atual FROM goals WHERE typeof(valor_atual) != 'real' AND typeof(valor_atual) != 'integer'")
        problematic_goals = c.fetchall()
        
        for goal_id, valor_atual in problematic_goals:
            # Se o valor_atual for uma data ou string não numérica, resetar para 0
            if valor_atual and not valor_atual.replace('.', '').replace(',', '').isdigit():
                c.execute("UPDATE goals SET valor_atual = 0 WHERE id = ?", (goal_id,))
                logger.info(f"Corrigido objetivo {goal_id}: valor_atual de '{valor_atual}' para 0")
        
        conn.commit()
        conn.close()
        logger.info("Dados dos objetivos corrigidos com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao corrigir dados dos objetivos: {e}")
        return False

def get_goals(user_id):
    """Obtém todos os objetivos do usuário - VERSÃO CORRIGIDA"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Verificar se a coluna 'prazo' existe
        c.execute("PRAGMA table_info(goals)")
        columns = [column[1] for column in c.fetchall()]
        has_prazo = 'prazo' in columns
        
        if has_prazo:
            c.execute("SELECT id, tipo, descricao, valor_meta, valor_atual, data_criacao, prazo, concluido FROM goals WHERE user_id=? ORDER BY data_criacao DESC", (user_id,))
        else:
            c.execute("SELECT id, tipo, descricao, valor_meta, valor_atual, data_criacao, concluido FROM goals WHERE user_id=? ORDER BY data_criacao DESC", (user_id,))
            
        result = c.fetchall()
        conn.close()
        
        goals = []
        for row in result:
            goal_data = {
                'id': row[0],
                'tipo': row[1],
                'descricao': row[2],
                'valor_meta': float(row[3]) if row[3] else 0.0,
                'valor_atual': float(row[4]) if row[4] and str(row[4]).replace('.', '').isdigit() else 0.0,
                'data_criacao': row[5],
                'concluido': bool(row[-1])  # Última coluna é sempre 'concluido'
            }
            
            # Adicionar prazo se existir
            if has_prazo and len(row) > 7:
                goal_data['prazo'] = row[6]
                
            goals.append(goal_data)
            
        return goals
    except Exception as e:
        logger.error(f"Erro ao obter objetivos: {e}")
        return []

def update_goals_table():
    """Atualiza a estrutura da tabela goals para incluir a coluna prazo"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Verificar se a coluna 'prazo' existe
        c.execute("PRAGMA table_info(goals)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'prazo' not in columns:
            # Adicionar coluna prazo
            c.execute("ALTER TABLE goals ADD COLUMN prazo TEXT")
            logger.info("Coluna 'prazo' adicionada à tabela goals")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar tabela goals: {e}")
        return False
        
def update_goal_progress(goal_id, valor_atual):
    """Atualiza o progresso de um objetivo"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE goals SET valor_atual = ? WHERE id = ?", (valor_atual, goal_id))
        
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

def delete_custom_category(user_id, tipo, nome_categoria):
    """Exclui uma categoria personalizada do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM custom_categories WHERE user_id=? AND tipo=? AND nome_categoria=?", 
                 (user_id, tipo, nome_categoria))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao excluir categoria personalizada: {e}")
        return False

# Adicione estas funções ao database.py

def add_salary(user_id, origem, valor, principal=False):
    """Adiciona um novo salário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Se for principal, remover o status de principal dos outros salários
        if principal:
            c.execute("UPDATE salaries SET principal = 0 WHERE user_id = ?", (user_id,))
        
        c.execute("INSERT INTO salaries (user_id, origem, valor, principal, data_criacao) VALUES (?, ?, ?, ?, ?)",
                 (user_id, origem, valor, 1 if principal else 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar salário: {e}")
        return False

def get_salaries(user_id):
    """Obtém todos os salários do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, origem, valor, principal, data_criacao FROM salaries WHERE user_id=? ORDER BY principal DESC, data_criacao DESC", (user_id,))
        result = c.fetchall()
        conn.close()
        
        salaries = []
        for row in result:
            salaries.append({
                'id': row[0],
                'origem': row[1],
                'valor': row[2],
                'principal': bool(row[3]),
                'data_criacao': row[4]
            })
        return salaries
    except Exception as e:
        logger.error(f"Erro ao obter salários: {e}")
        return []

def get_principal_salary(user_id):
    """Obtém o salário principal do usuário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT origem, valor FROM salaries WHERE user_id=? AND principal=1", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'origem': result[0],
                'valor': result[1]
            }
        return None
    except Exception as e:
        logger.error(f"Erro ao obter salário principal: {e}")
        return None

def update_salary(salary_id, origem=None, valor=None):
    """Atualiza um salário"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if origem and valor:
            c.execute("UPDATE salaries SET origem=?, valor=? WHERE id=?", (origem, valor, salary_id))
        elif origem:
            c.execute("UPDATE salaries SET origem=? WHERE id=?", (origem, salary_id))
        elif valor:
            c.execute("UPDATE salaries SET valor=? WHERE id=?", (valor, salary_id))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar salário: {e}")
        return False

def delete_salary(salary_id):
    """Exclui um salário (não permite excluir o principal)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Verificar se é principal
        c.execute("SELECT principal FROM salaries WHERE id=?", (salary_id,))
        result = c.fetchone()
        
        if result and result[0] == 1:
            return False  # Não permite excluir o principal
            
        c.execute("DELETE FROM salaries WHERE id=?", (salary_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao excluir salário: {e}")
        return False

def set_principal_salary(salary_id, user_id):
    """Define um salário como principal"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Remover principal de todos os salários do usuário
        c.execute("UPDATE salaries SET principal = 0 WHERE user_id = ?", (user_id,))
        
        # Definir o novo salário como principal
        c.execute("UPDATE salaries SET principal = 1 WHERE id = ?", (salary_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao definir salário principal: {e}")
        return False
        
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

def export_user_data(user_id):
    """Exporta todos os dados do usuário para formato CSV"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute("SELECT nickname, salario_liquido, data_cadastro FROM users WHERE user_id=?", (user_id,))
        user_data = c.fetchone()
        
        c.execute('''SELECT tipo_gasto, categoria, subcategoria, amount, description, date, timestamp 
        FROM transactions WHERE user_id=? ORDER BY timestamp DESC''', (user_id,))
        transactions = c.fetchall()
        
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

def reset_user_data(user_id):
    """Remove todos os dados do usuário (exceto cadastro básico)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM custom_categories WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM goals WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM salary_history WHERE user_id=?", (user_id,))
        
        c.execute("UPDATE users SET salario_liquido = NULL WHERE user_id=?", (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erro ao resetar dados: {e}")
        return False