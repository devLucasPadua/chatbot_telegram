import sqlite3
import datetime
import logging
import os
from typing import List, Dict, Optional, Tuple

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "financas.db"):
        self.db_path = db_path
        self.init_db()
        
    def get_connection(self):
        """Cria e retorna uma conexão com o banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com banco de dados: {e}")
            return None

    def init_db(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        try:
            conn = self.get_connection()
            if conn is None:
                logger.error("❌ Não foi possível conectar ao banco de dados")
                return False
                
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    nickname TEXT NOT NULL,
                    salario_liquido REAL NOT NULL,
                    data_criacao TEXT NOT NULL
                )
            ''')
            
            # Tabela de transações (gastos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    subcategoria TEXT NOT NULL,
                    valor REAL NOT NULL,
                    descricao TEXT,
                    data TEXT NOT NULL,
                    data_registro TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Tabela de categorias personalizadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    data_criacao TEXT NOT NULL,
                    UNIQUE(user_id, tipo, nome),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Tabela de objetivos financeiros
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    valor_meta REAL NOT NULL,
                    progresso REAL DEFAULT 0,
                    prazo TEXT,
                    data_criacao TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Tabela de salários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS salaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    origem TEXT NOT NULL,
                    valor REAL NOT NULL,
                    principal BOOLEAN DEFAULT 0,
                    data_criacao TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Tabela de rendas extras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extra_incomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    origem TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_criacao TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Banco de dados inicializado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
            return False

    def user_exists(self, user_id: int) -> bool:
        """Verifica se um usuário existe no banco de dados"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"❌ Erro ao verificar usuário: {e}")
            return False

    def add_user(self, user_id: int, nickname: str, salario_liquido: float) -> bool:
        """Adiciona um novo usuário ao banco de dados"""
        try:
            conn = self.get_connection()
            if conn is None:
                logger.error("❌ Não foi possível conectar ao banco para adicionar usuário")
                return False
                
            cursor = conn.cursor()
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Verificar se o usuário já existe (por segurança)
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                logger.info(f"ℹ️ Usuário {user_id} já existe, atualizando dados...")
                cursor.execute(
                    "UPDATE users SET nickname = ?, salario_liquido = ? WHERE user_id = ?",
                    (nickname, salario_liquido, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (user_id, nickname, salario_liquido, data_criacao) VALUES (?, ?, ?, ?)",
                    (user_id, nickname, salario_liquido, data_criacao)
                )
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Usuário {nickname} (ID: {user_id}) salvo com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar/atualizar usuário: {e}")
            return False

    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Obtém os dados de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return None
                
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados do usuário: {e}")
            return None

    def get_user_nickname(self, user_id: int) -> str:
        """Obtém o nickname de um usuário"""
        try:
            user_data = self.get_user_data(user_id)
            if user_data and 'nickname' in user_data:
                return user_data['nickname']
            return "Usuário"
        except Exception as e:
            logger.error(f"❌ Erro ao obter nickname: {e}")
            return "Usuário"

    def update_user_nickname(self, user_id: int, new_nickname: str) -> bool:
        """Atualiza o nickname de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET nickname = ? WHERE user_id = ?",
                (new_nickname, user_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"✅ Nickname atualizado para: {new_nickname}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar nickname: {e}")
            return False

    def update_user_salary(self, user_id: int, new_salary: float) -> bool:
        """Atualiza o salário de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET salario_liquido = ? WHERE user_id = ?",
                (new_salary, user_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"✅ Salário atualizado para: {new_salary}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar salário: {e}")
            return False

    def add_transaction(self, user_id: int, tipo: str, categoria: str, subcategoria: str, 
                       valor: float, descricao: str, data: str) -> bool:
        """Adiciona uma nova transação (gasto)"""
        try:
            # Validar e formatar a data
            data_formatada = self._parse_and_validate_date(data)
            if not data_formatada:
                logger.error(f"❌ Data inválida: {data}")
                return False
                
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            data_registro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, tipo, categoria, subcategoria, valor, descricao, data, data_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, tipo, categoria, subcategoria, valor, descricao, data_formatada, data_registro))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Transação de R$ {valor} adicionada para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar transação: {e}")
            return False

    def _parse_and_validate_date(self, date_str: str) -> Optional[str]:
        """Converte data no formato DD/MM/AAAA para AAAA-MM-DD"""
        try:
            # Remover espaços e caracteres especiais
            clean_date = ''.join(c for c in date_str if c.isdigit() or c == '/')
            
            if 'hoje' in date_str.lower():
                today = datetime.datetime.now()
                return today.strftime('%Y-%m-%d')
                
            parts = clean_date.split('/')
            if len(parts) == 3:
                day, month, year = parts
            else:
                # Tentar parse como DDMMAAAA
                if len(clean_date) == 8:
                    day, month, year = clean_date[:2], clean_date[2:4], clean_date[4:]
                else:
                    return None
            
            # Validar se são números
            if not (day.isdigit() and month.isdigit() and year.isdigit()):
                return None
            
            day_int, month_int, year_int = int(day), int(month), int(year)
            
            # Ajustar ano se necessário (2 dígitos)
            if year_int < 100:
                year_int += 2000 if year_int < 50 else 1900
            
            # Validações básicas
            if not (1 <= month_int <= 12):
                return None
            if not (1 <= day_int <= 31):
                return None
            if not (2020 <= year_int <= 2100):
                return None
            
            # Formatar para SQLite
            return f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
        except Exception as e:
            logger.error(f"❌ Erro ao converter data {date_str}: {e}")
            return None

    def get_monthly_expenses(self, user_id: int, month: int = None, year: int = None) -> Dict:
        """Obtém os gastos mensais agrupados por tipo e categoria"""
        try:
            if month is None:
                month = datetime.datetime.now().month
            if year is None:
                year = datetime.datetime.now().year
                
            conn = self.get_connection()
            if conn is None:
                return {'fixo': {}, 'flexivel': {}}
                
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tipo, categoria, subcategoria, SUM(valor) as total
                FROM transactions 
                WHERE user_id = ? 
                AND strftime('%m', data) = ? 
                AND strftime('%Y', data) = ?
                GROUP BY tipo, categoria, subcategoria
                ORDER BY tipo, total DESC
            ''', (user_id, f"{month:02d}", str(year)))
            
            rows = cursor.fetchall()
            conn.close()
            
            expenses = {'fixo': {}, 'flexivel': {}}
            
            for row in rows:
                tipo = row['tipo']
                categoria = row['categoria']
                subcategoria = row['subcategoria']
                total = row['total']
                
                if categoria not in expenses[tipo]:
                    expenses[tipo][categoria] = {}
                
                expenses[tipo][categoria][subcategoria] = total
                
            return expenses
        except Exception as e:
            logger.error(f"❌ Erro ao buscar gastos mensais: {e}")
            return {'fixo': {}, 'flexivel': {}}

    def get_monthly_transactions(self, user_id: int, month: int, year: int) -> List[Dict]:
        """Obtém todas as transações de um mês específico"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? 
                AND strftime('%m', data) = ? 
                AND strftime('%Y', data) = ?
                ORDER BY data DESC
            ''', (user_id, f"{month:02d}", str(year)))
            
            rows = cursor.fetchall()
            conn.close()
            
            transactions = []
            for row in rows:
                # Converter data para formato brasileiro
                try:
                    data_obj = datetime.datetime.strptime(row['data'], '%Y-%m-%d')
                    data_br = data_obj.strftime('%d/%m/%Y')
                except:
                    data_br = row['data']
                
                transaction = dict(row)
                transaction['data'] = data_br
                transactions.append(transaction)
                
            return transactions
        except Exception as e:
            logger.error(f"❌ Erro ao buscar transações mensais: {e}")
            return []

    def add_custom_category(self, user_id: int, tipo: str, nome: str) -> bool:
        """Adiciona uma categoria personalizada"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO custom_categories (user_id, tipo, nome, data_criacao)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, tipo, nome, data_criacao))
                conn.commit()
                logger.info(f"✅ Categoria '{nome}' adicionada com sucesso")
                success = True
            except sqlite3.IntegrityError:
                # Categoria já existe - isso é normal
                conn.rollback()
                success = True
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar categoria: {e}")
                success = False
                
            conn.close()
            return success
        except Exception as e:
            logger.error(f"❌ Erro ao acessar banco para categoria: {e}")
            return False

    def get_custom_categories(self, user_id: int, tipo: str) -> List[str]:
        """Obtém as categorias personalizadas de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nome FROM custom_categories 
                WHERE user_id = ? AND tipo = ?
                ORDER BY nome
            ''', (user_id, tipo))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row['nome'] for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar categorias personalizadas: {e}")
            return []

    def delete_custom_category(self, user_id: int, tipo: str, nome: str) -> bool:
        """Exclui uma categoria personalizada"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM custom_categories 
                WHERE user_id = ? AND tipo = ? AND nome = ?
            ''', (user_id, tipo, nome))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Categoria '{nome}' excluída")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao excluir categoria personalizada: {e}")
            return False

    def get_category_expenses(self, user_id: int, tipo: str, categoria: str) -> List[Dict]:
        """Obtém todos os gastos de uma categoria específica"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? AND tipo = ? AND categoria = ?
                ORDER BY data DESC
            ''', (user_id, tipo, categoria))
            
            rows = cursor.fetchall()
            conn.close()
            
            gastos = []
            for row in rows:
                # Converter data para formato brasileiro
                try:
                    data_obj = datetime.datetime.strptime(row['data'], '%Y-%m-%d')
                    data_br = data_obj.strftime('%d/%m/%Y')
                except:
                    data_br = row['data']
                
                gasto = dict(row)
                gasto['data'] = data_br
                gastos.append(gasto)
                
            return gastos
        except Exception as e:
            logger.error(f"❌ Erro ao buscar gastos da categoria: {e}")
            return []

    def add_goal(self, user_id: int, descricao: str, tipo: str, valor_meta: float, prazo: str = None) -> bool:
        """Adiciona um novo objetivo financeiro"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Converter prazo para formato SQLite se fornecido
            prazo_sql = None
            if prazo:
                prazo_sql = self._parse_and_validate_date(prazo)
            
            cursor.execute('''
                INSERT INTO goals (user_id, descricao, tipo, valor_meta, prazo, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, descricao, tipo, valor_meta, prazo_sql, data_criacao))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Objetivo '{descricao}' adicionado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar objetivo: {e}")
            return False

    def get_user_goals(self, user_id: int) -> List[Dict]:
        """Obtém todos os objetivos de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM goals 
                WHERE user_id = ? 
                ORDER BY data_criacao DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            goals = []
            for row in rows:
                goal = dict(row)
                
                # Converter prazo para formato brasileiro se existir
                if goal['prazo']:
                    try:
                        data_obj = datetime.datetime.strptime(goal['prazo'], '%Y-%m-%d')
                        goal['prazo'] = data_obj.strftime('%d/%m/%Y')
                    except:
                        pass
                
                goals.append(goal)
                
            return goals
        except Exception as e:
            logger.error(f"❌ Erro ao buscar objetivos: {e}")
            return []

    def update_goal_progress(self, goal_id: int, progresso: float) -> bool:
        """Atualiza o progresso de um objetivo"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE goals SET progresso = ? WHERE id = ?
            ''', (progresso, goal_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar progresso do objetivo: {e}")
            return False

    def delete_goal(self, goal_id: int) -> bool:
        """Exclui um objetivo"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Objetivo {goal_id} excluído")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao excluir objetivo: {e}")
            return False

    def reset_user_data(self, user_id: int) -> bool:
        """Reinicia os dados do usuário (exclui transações e objetivos)"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            # Excluir transações
            cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
            
            # Excluir objetivos
            cursor.execute('DELETE FROM goals WHERE user_id = ?', (user_id,))
            
            # Excluir categorias personalizadas
            cursor.execute('DELETE FROM custom_categories WHERE user_id = ?', (user_id,))
            
            # Excluir salários (exceto o principal)
            cursor.execute('DELETE FROM salaries WHERE user_id = ? AND principal = 0', (user_id,))
            
            # Excluir rendas extras
            cursor.execute('DELETE FROM extra_incomes WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Dados do usuário {user_id} resetados")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao reiniciar dados do usuário: {e}")
            return False

    def fix_goals_data(self):
        """Corrige dados inconsistentes na tabela de objetivos"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            # Verificar se a coluna progresso existe
            cursor.execute("PRAGMA table_info(goals)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'progresso' not in columns:
                logger.info("🔧 Adicionando coluna progresso à tabela goals")
                cursor.execute('ALTER TABLE goals ADD COLUMN progresso REAL DEFAULT 0')
            
            conn.commit()
            conn.close()
            logger.info("✅ Dados dos objetivos verificados/corrigidos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao corrigir dados dos objetivos: {e}")
            return False

    # ========== MÉTODOS PARA SALÁRIOS ==========

    def add_salary(self, user_id: int, origem: str, valor: float, principal: bool = False) -> bool:
        """Adiciona um novo salário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Se este é o salário principal, remover principal de outros
            if principal:
                cursor.execute('''
                    UPDATE salaries SET principal = 0 
                    WHERE user_id = ? AND principal = 1
                ''', (user_id,))
            
            cursor.execute('''
                INSERT INTO salaries (user_id, origem, valor, principal, data_criacao)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, origem, valor, 1 if principal else 0, data_criacao))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Salário de R$ {valor} adicionado para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar salário: {e}")
            return False

    def get_salaries(self, user_id: int) -> List[Dict]:
        """Obtém todos os salários de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM salaries 
                WHERE user_id = ? 
                ORDER BY principal DESC, data_criacao DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            salaries = []
            for row in rows:
                salary = dict(row)
                
                # Converter data para formato legível
                if salary['data_criacao']:
                    try:
                        data_obj = datetime.datetime.strptime(salary['data_criacao'], '%Y-%m-%d %H:%M:%S')
                        salary['data_criacao'] = data_obj.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                
                salaries.append(salary)
                
            return salaries
        except Exception as e:
            logger.error(f"❌ Erro ao buscar salários: {e}")
            return []

    def update_salary(self, salary_id: int, origem: str = None, valor: float = None) -> bool:
        """Atualiza um salário no banco de dados - VERSÃO CORRIGIDA"""
        try:
            logger.info(f"🔍 DATABASE: update_salary chamado - id: {salary_id}, origem: {origem}, valor: {valor}")
            
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            if origem is not None and valor is not None:
                cursor.execute('UPDATE salaries SET origem = ?, valor = ? WHERE id = ?', 
                            (origem, valor, salary_id))
                logger.info(f"✅ Database: Atualizando salário {salary_id} - origem: {origem}, valor: {valor}")
            elif origem is not None:
                cursor.execute('UPDATE salaries SET origem = ? WHERE id = ?', 
                            (origem, salary_id))
                logger.info(f"✅ Database: Atualizando salário {salary_id} - origem: {origem}")
            elif valor is not None:
                cursor.execute('UPDATE salaries SET valor = ? WHERE id = ?', 
                            (valor, salary_id))
                logger.info(f"✅ Database: Atualizando salário {salary_id} - valor: {valor}")
            else:
                logger.info("❌ Database: Nada para atualizar")
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Database: Salário {salary_id} atualizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"❌ Database: Erro ao atualizar salário {salary_id}: {e}")
            return False

    def set_principal_salary(self, salary_id: int, user_id: int) -> bool:
        """Define um salário como principal"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            # Remover principal de todos os salários do usuário
            cursor.execute('''
                UPDATE salaries SET principal = 0 
                WHERE user_id = ?
            ''', (user_id,))
            
            # Definir o salário selecionado como principal
            cursor.execute('''
                UPDATE salaries SET principal = 1 
                WHERE id = ? AND user_id = ?
            ''', (salary_id, user_id))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Salário {salary_id} definido como principal")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao definir salário principal: {e}")
            return False

    def delete_salary(self, salary_id: int) -> bool:
        """Exclui um salário (apenas se não for principal)"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            # Verificar se é o salário principal
            cursor.execute('SELECT principal FROM salaries WHERE id = ?', (salary_id,))
            result = cursor.fetchone()
            
            if result and result['principal']:
                # Não permitir excluir salário principal
                logger.info("❌ Tentativa de excluir salário principal bloqueada")
                return False
            
            cursor.execute('DELETE FROM salaries WHERE id = ?', (salary_id,))
            conn.commit()
            conn.close()
            logger.info(f"✅ Salário {salary_id} excluído")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao excluir salário: {e}")
            return False

    # ========== MÉTODOS PARA RENDAS EXTRAS ==========

    def add_extra_income(self, user_id: int, origem: str, valor: float) -> bool:
        """Adiciona uma nova renda extra"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO extra_incomes (user_id, origem, valor, data_criacao)
                VALUES (?, ?, ?, ?)
            ''', (user_id, origem, valor, data_criacao))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Renda extra de R$ {valor} adicionada para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar renda extra: {e}")
            return False

    def get_extra_incomes(self, user_id: int) -> List[Dict]:
        """Obtém todas as rendas extras de um usuário"""
        try:
            conn = self.get_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM extra_incomes 
                WHERE user_id = ? 
                ORDER BY data_criacao DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            incomes = []
            for row in rows:
                income = dict(row)
                
                # Converter data para formato legível
                if income['data_criacao']:
                    try:
                        data_obj = datetime.datetime.strptime(income['data_criacao'], '%Y-%m-%d %H:%M:%S')
                        income['data_criacao'] = data_obj.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                
                incomes.append(income)
                
            return incomes
        except Exception as e:
            logger.error(f"❌ Erro ao buscar rendas extras: {e}")
            return []

    def update_extra_income(self, income_id: int, origem: str = None, valor: float = None) -> bool:
        """Atualiza uma renda extra existente"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            if origem is not None and valor is not None:
                cursor.execute('''
                    UPDATE extra_incomes SET origem = ?, valor = ? 
                    WHERE id = ?
                ''', (origem, valor, income_id))
            elif origem is not None:
                cursor.execute('''
                    UPDATE extra_incomes SET origem = ? 
                    WHERE id = ?
                ''', (origem, income_id))
            elif valor is not None:
                cursor.execute('''
                    UPDATE extra_incomes SET valor = ? 
                    WHERE id = ?
                ''', (valor, income_id))
            else:
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Renda extra {income_id} atualizada")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar renda extra: {e}")
            return False

    def delete_extra_income(self, income_id: int) -> bool:
        """Exclui uma renda extra"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute('DELETE FROM extra_incomes WHERE id = ?', (income_id,))
            conn.commit()
            conn.close()
            logger.info(f"✅ Renda extra {income_id} excluída")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao excluir renda extra: {e}")
            return False

    # ========== MÉTODOS DE BACKUP E RECUPERAÇÃO ==========

    def backup_database(self, backup_path: str) -> bool:
        """Cria um backup do banco de dados"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Backup criado em: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restaura o banco de dados a partir de um backup"""
        try:
            import shutil
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.db_path)
                logger.info("✅ Banco de dados restaurado do backup")
                return True
            else:
                logger.error("❌ Arquivo de backup não encontrado")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar backup: {e}")
            return False

# Instância global do banco de dados
db = Database()

# Funções de compatibilidade (para manter a interface existente)
def init_db():
    """Inicializa o banco de dados"""
    return db.init_db()

def user_exists(user_id: int) -> bool:
    """Verifica se um usuário existe"""
    return db.user_exists(user_id)

def add_user(user_id: int, nickname: str, salario_liquido: float) -> bool:
    """Adiciona um novo usuário"""
    return db.add_user(user_id, nickname, salario_liquido)

def get_user_data(user_id: int) -> Optional[Dict]:
    """Obtém os dados de um usuário"""
    return db.get_user_data(user_id)

def get_user_nickname(user_id: int) -> str:
    """Obtém o nickname de um usuário"""
    return db.get_user_nickname(user_id)

def update_user_nickname(user_id: int, new_nickname: str) -> bool:
    """Atualiza o nickname de um usuário"""
    return db.update_user_nickname(user_id, new_nickname)

def update_user_salary(user_id: int, new_salary: float) -> bool:
    """Atualiza o salário de um usuário"""
    return db.update_user_salary(user_id, new_salary)

def add_transaction(user_id: int, tipo: str, categoria: str, subcategoria: str, 
                   valor: float, descricao: str, data: str) -> bool:
    """Adiciona uma transação"""
    return db.add_transaction(user_id, tipo, categoria, subcategoria, valor, descricao, data)

def get_monthly_expenses(user_id: int, month: int = None, year: int = None) -> Dict:
    """Obtém gastos mensais"""
    return db.get_monthly_expenses(user_id, month, year)

def get_monthly_transactions(user_id: int, month: int, year: int) -> List[Dict]:
    """Obtém transações mensais"""
    return db.get_monthly_transactions(user_id, month, year)

def add_custom_category(user_id: int, tipo: str, nome: str) -> bool:
    """Adiciona categoria personalizada"""
    return db.add_custom_category(user_id, tipo, nome)

def get_custom_categories(user_id: int, tipo: str) -> List[str]:
    """Obtém categorias personalizadas"""
    return db.get_custom_categories(user_id, tipo)

def delete_custom_category(user_id: int, tipo: str, nome: str) -> bool:
    """Exclui categoria personalizada"""
    return db.delete_custom_category(user_id, tipo, nome)

def get_category_expenses(user_id: int, tipo: str, categoria: str) -> List[Dict]:
    """Obtém gastos por categoria"""
    return db.get_category_expenses(user_id, tipo, categoria)

def add_goal(user_id: int, descricao: str, tipo: str, valor_meta: float, prazo: str = None) -> bool:
    """Adiciona objetivo"""
    return db.add_goal(user_id, descricao, tipo, valor_meta, prazo)

def get_user_goals(user_id: int) -> List[Dict]:
    """Obtém objetivos do usuário"""
    return db.get_user_goals(user_id)

def update_goal_progress(goal_id: int, progresso: float) -> bool:
    """Atualiza progresso do objetivo"""
    return db.update_goal_progress(goal_id, progresso)

def delete_goal(goal_id: int) -> bool:
    """Exclui objetivo"""
    return db.delete_goal(goal_id)

def reset_user_data(user_id: int) -> bool:
    """Reinicia dados do usuário"""
    return db.reset_user_data(user_id)

def fix_goals_data():
    """Corrige dados dos objetivos"""
    return db.fix_goals_data()

# Funções para salários
def add_salary(user_id: int, origem: str, valor: float, principal: bool = False) -> bool:
    """Adiciona salário"""
    return db.add_salary(user_id, origem, valor, principal)

def get_salaries(user_id: int) -> List[Dict]:
    """Obtém salários do usuário"""
    return db.get_salaries(user_id)

def update_salary(salary_id: int, origem: str = None, valor: float = None) -> bool:
    """Atualiza salário"""
    return db.update_salary(salary_id, origem, valor)

def set_principal_salary(salary_id: int, user_id: int) -> bool:
    """Define salário principal"""
    return db.set_principal_salary(salary_id, user_id)

def delete_salary(salary_id: int) -> bool:
    """Exclui salário"""
    return db.delete_salary(salary_id)

# Funções para rendas extras
def add_extra_income(user_id: int, origem: str, valor: float) -> bool:
    """Adiciona renda extra"""
    return db.add_extra_income(user_id, origem, valor)

def get_extra_incomes(user_id: int) -> List[Dict]:
    """Obtém rendas extras do usuário"""
    return db.get_extra_incomes(user_id)

def update_extra_income(income_id: int, origem: str = None, valor: float = None) -> bool:
    """Atualiza renda extra"""
    return db.update_extra_income(income_id, origem, valor)

def delete_extra_income(income_id: int) -> bool:
    """Exclui renda extra"""
    return db.delete_extra_income(income_id)