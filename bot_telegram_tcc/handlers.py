from telegram import (
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, Update
)
from telegram.ext import ContextTypes, ConversationHandler
import database as db
import datetime
import calendar
import logging
import re
import config
import coach
import asyncio

# ========== ESTADOS DA CONVERSA ==========
# Cadastro inicial (0-2)
GET_NAME, GET_SALARY, TIPO_GASTO = range(3)

# Registro de gastos (3-10)
CATEGORIA_FIXA, CATEGORIA_FLEXIVEL, NOVA_CATEGORIA_FIXA, NOVA_CATEGORIA_FLEXIVEL = range(3, 7)
VALOR_GASTO, DATA_GASTO, CONTINUAR_GASTOS, RESUMO_GASTOS = range(7, 11)

# Categorias personalizadas (11-18)
OUTROS_FLEXIVEIS, MINHAS_CATEGORIAS, NOVA_CATEGORIA_OUTROS, CONFIRM_GASTO_OUTROS = range(11, 15)
OUTROS_FIXOS, MINHAS_CATEGORIAS_FIXAS, NOVA_CATEGORIA_OUTROS_FIXOS, CONFIRM_GASTO_OUTROS_FIXOS = range(15, 19)

# Suas categorias (19-23)
SUAS_CATEGORIAS, CATEGORIAS_FIXAS, CATEGORIAS_FLEXIVEIS = range(19, 22)
SELECIONAR_CATEGORIA_EXCLUIR, CONFIRMAR_EXCLUSAO_CATEGORIA = range(22, 24)

# Configurações (24-26)
EDIT_NAME, EDIT_SALARY, CONFIRM_RESET = range(24, 27)

# Objetivos (27-35)
GOAL_TYPE, GOAL_DESCRIPTION, GOAL_TARGET, GOAL_DEADLINE = range(27, 31)
SELECT_GOAL, UPDATE_GOAL_PROGRESS, SELECT_GOAL_DELETE, CONFIRM_DELETE_GOAL = range(31, 35)
GOAL_DEADLINE_CALENDAR = 35

# Extrato do mês (36)
EXTRATO_MES  = 36

# Educação Financeira (37-39)
DICA_DIA, GLOSSARIO, MODULOS_EDUCATIVOS = range(37, 40)

# Salários (40-45)
ADD_SALARY_ORIGIN, ADD_SALARY_VALUE = range(40, 42)
EDIT_SALARY_SELECT, EDIT_SALARY_ORIGIN, EDIT_SALARY_VALUE, EDIT_SALARY_ACTION = range(42, 46)

# Rendas Extras (46-51)
ADD_EXTRA_INCOME_ORIGIN, ADD_EXTRA_INCOME_VALUE = range(46, 48)
EDIT_EXTRA_INCOME_SELECT, EDIT_EXTRA_INCOME_ORIGIN, EDIT_EXTRA_INCOME_VALUE, EDIT_EXTRA_INCOME_ACTION = range(48, 52)

# ========== CONFIGURAÇÃO DE LOGGING ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== KEYBOARDS ==========
def main_keyboard():
    keyboard = [
        ['🧮 Gastos / Rendas ', '🧾 Meu Extrato'],
        ['📈 Saúde Financeira', '🎓 Educação Financeira'],
        ['🎯 Objetivos', '⚙️ Configurações'],
        ['❓ Ajuda']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def gastos_keyboard():
    keyboard = [
        ['🏦 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['💰 Salário', '💵 Renda extra'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def tipo_gasto_keyboard():
    keyboard = [
        ['🏦 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_fixas_keyboard():
    keyboard = []
    categorias = list(config.CATEGORIAS_FIXAS.keys())
    for i in range(0, len(categorias), 2):
        keyboard.append(categorias[i:i+2])
    #keyboard.append(['Outros...'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_flexiveis_keyboard():
    keyboard = []
    categorias = list(config.CATEGORIAS_FLEXIVEIS.keys())
    for i in range(0, len(categorias), 2):
        keyboard.append(categorias[i:i+2])
    #keyboard.append(['Outros...'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def sim_nao_keyboard():
    return ReplyKeyboardMarkup([['✅ SIM', '❌ NÃO']], resize_keyboard=True)

def outros_flexiveis_keyboard():
    keyboard = [
        ['📂 Minhas categorias', '➕ Adicionar novo'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def outros_fixos_keyboard():
    keyboard = [
        ['📂 Minhas categorias', '➕ Adicionar novo'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def minhas_categorias_keyboard(user_id):
    cats = db.get_custom_categories(user_id, 'flexivel')
    keyboard = [[c] for c in cats] or [['(Vazio)']]
    keyboard.append(['↩️ Voltar para Outros...'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def minhas_categorias_fixas_keyboard(user_id):
    cats = db.get_custom_categories(user_id, 'fixo')
    keyboard = [[c] for c in cats] or [['(Vazio)']]
    keyboard.append(['↩️ Voltar para Outros...'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def suas_categorias_keyboard():
    keyboard = [
        ['🏦 Fixas', '🛍️ Flexíveis'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_fixas_keyboard_with_delete(user_id):
    cats = db.get_custom_categories(user_id, 'fixo')
    keyboard = [[f'📂 {c}'] for c in cats]
    if cats:
        keyboard.append(['🗑️ Excluir Categoria'])
    keyboard.append(['↩️ Voltar para Suas Categorias'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_flexiveis_keyboard_with_delete(user_id):
    cats = db.get_custom_categories(user_id, 'flexivel')
    keyboard = [[f'📂 {c}'] for c in cats]
    if cats:
        keyboard.append(['🗑️ Excluir Categoria'])
    keyboard.append(['↩️ Voltar para Suas Categorias'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_excluir_keyboard(user_id, tipo):
    cats = db.get_custom_categories(user_id, tipo)
    keyboard = [[f'🗑️ {c}'] for c in cats]
    tipo_texto = 'Fixas' if tipo == 'fixo' else 'Flexíveis'
    keyboard.append([f'↩️ Voltar para Categorias {tipo_texto}'])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def confirmar_exclusao_categoria_keyboard():
    keyboard = [
        ['✅ SIM, Excluir', '❌ NÃO, Cancelar'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def objetivos_keyboard():
    keyboard = [
        ['🎯 Adicionar Objetivo', '📊 Atualizar Progresso'],
        ['🗑️ Excluir Objetivo', '📋 Meus Objetivos'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def config_keyboard():
    keyboard = [
        ['✏️ Editar Perfil', '🔄 Redefinir'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def educacao_keyboard():
    keyboard = [
        ['💡 Dica do Dia', '📚 Glossário'],
        ['🎓 Módulos Educativos', '🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def saude_financeira_keyboard():
    keyboard = [
        ['📊 Ver Métricas Detalhadas', '🧠 Recomendações IA'],
        ['📈 Análise Detalhada com IA', '🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def analise_detalhada_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Ver Métricas", callback_data="analise_metricas")],
        [InlineKeyboardButton("🎯 Metas Sugeridas", callback_data="analise_metas")],
        [InlineKeyboardButton("🧠 Recomendações IA", callback_data="analise_recomendacoes")],
        [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="analise_voltar")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== CALENDÁRIO ==========
class Calendar:
    @staticmethod
    def create_calendar(year=None, month=None, view='month'):
        """
        Cria calendário com diferentes views
        view: 'month' (padrão), 'year' (seleção de ano), 'decade' (seleção de década)
        """
        now = datetime.datetime.now()
        if year is None: 
            year = now.year
        if month is None: 
            month = now.month

        if view == 'month':
            return Calendar.create_month_calendar(year, month)
        elif view == 'year':
            return Calendar.create_year_calendar(year)
        elif view == 'decade':
            return Calendar.create_decade_calendar(year)

    @staticmethod
    def create_month_calendar(year=None, month=None):
        """Cria o calendário mensal padrão"""
        now = datetime.datetime.now()
        if year is None: 
            year = now.year
        if month is None: 
            month = now.month

        if month < 1:
            month = 12
            year -= 1
        if month > 12:
            month = 1
            year += 1

        keyboard = []
        month_name = calendar.month_name[month]
        header = f"{month_name} {year}"
        
        # Cabeçalho com navegação - agora o header é clicável para mudar para view de ano
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"CAL_PREV_MONTH_{year}_{month}"),
            InlineKeyboardButton(header, callback_data=f"CAL_VIEW_YEAR_{year}"),
            InlineKeyboardButton("▶️", callback_data=f"CAL_NEXT_MONTH_{year}_{month}")
        ])

        # Dias da semana
        week_days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        keyboard.append([InlineKeyboardButton(d, callback_data="CAL_IGNORE") for d in week_days])

        # Dias do mês
        cal = calendar.Calendar(firstweekday=6)  # Domingo como primeiro dia
        month_days = cal.monthdayscalendar(year, month)
        for week in month_days:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="CAL_IGNORE"))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=f"CAL_DAY_{year}_{month:02d}_{day:02d}"))
            keyboard.append(row)

        # Botões auxiliares
        keyboard.append([
            InlineKeyboardButton("📅 Hoje", callback_data="CAL_TODAY"),
            InlineKeyboardButton("⌨️ Digitar", callback_data="CAL_MANUAL")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_year_calendar(year=None):
        """Cria calendário de seleção de ano"""
        now = datetime.datetime.now()
        if year is None: 
            year = now.year

        keyboard = []
        
        # Cabeçalho com navegação de década - ano é clicável para mudar para view de década
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"CAL_PREV_YEAR_{year}"),
            InlineKeyboardButton(f"{year}", callback_data=f"CAL_VIEW_DECADE_{year}"),
            InlineKeyboardButton("▶️", callback_data=f"CAL_NEXT_YEAR_{year}")
        ])

        # Meses em português
        months_ptbr = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        
        # Grid 4x3 para os meses
        for i in range(0, 12, 4):
            row = []
            for j in range(4):
                month_num = i + j + 1
                month_name = months_ptbr[i + j]
                if month_num == now.month and year == now.year:
                    month_name = f"•{month_name}•"  # Destaca o mês atual
                row.append(InlineKeyboardButton(month_name, callback_data=f"CAL_SELECT_MONTH_{year}_{month_num:02d}"))
            keyboard.append(row)

        # Botão voltar
        keyboard.append([
            InlineKeyboardButton("↩️ Voltar", callback_data=f"CAL_VIEW_MONTH_{year}_{now.month:02d}")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_decade_calendar(year=None):
        """Cria calendário de seleção de década"""
        now = datetime.datetime.now()
        if year is None: 
            year = now.year

        # Calcular década atual (ex: 2020-2029)
        decade_start = (year // 10) * 10
        decade_end = decade_start + 9
        
        keyboard = []
        
        # Cabeçalho com navegação de década
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"CAL_PREV_DECADE_{decade_start}"),
            InlineKeyboardButton(f"{decade_start}-{decade_end}", callback_data="CAL_IGNORE"),
            InlineKeyboardButton("▶️", callback_data=f"CAL_NEXT_DECADE_{decade_start}")
        ])

        # Anos da década (3x4 grid)
        years = []
        for y in range(decade_start - 1, decade_end + 2):  # Inclui anos das décadas adjacentes
            if y == decade_start - 1:
                years.append("")  # Espaço vazio
            elif y == decade_end + 1:
                years.append("")  # Espaço vazio
            else:
                years.append(y)
        
        # Organizar em grid 4x3
        for i in range(0, 12, 4):
            row = []
            for j in range(4):
                year_num = years[i + j]
                if year_num == "":
                    row.append(InlineKeyboardButton(" ", callback_data="CAL_IGNORE"))
                else:
                    is_current = (year_num == now.year)
                    display_text = f"•{year_num}•" if is_current else str(year_num)
                    row.append(InlineKeyboardButton(display_text, callback_data=f"CAL_SELECT_YEAR_{year_num}"))
            keyboard.append(row)

        # Botão voltar
        keyboard.append([
            InlineKeyboardButton("↩️ Voltar", callback_data=f"CAL_VIEW_YEAR_{now.year}")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        try:
            # ========== AÇÕES BÁSICAS ==========
            if data == "CAL_TODAY":
                today = datetime.datetime.now().strftime('%d/%m/%Y')
                return await Calendar.handle_date_selection(update, context, today)

            if data == "CAL_MANUAL":
                await query.message.reply_text(
                    "📅 DIGITE A DATA\n\nFormatos aceitos:\n• DD/MM/AAAA\n• DDMMAAAA\n• 'hoje' para data atual",
                    reply_markup=ReplyKeyboardRemove()
                )
                return DATA_GASTO

            if data.startswith("CAL_DAY_"):
                parts = data.split('_')
                year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
                selected_date = f"{day:02d}/{month:02d}/{year}"
                return await Calendar.handle_date_selection(update, context, selected_date)

            # ========== MUDANÇA DE VIEW ==========
            if data.startswith("CAL_VIEW_"):
                parts = data.split('_')
                view_type = parts[2]
                year = int(parts[3])
                
                if view_type == "YEAR":
                    await query.edit_message_reply_markup(
                        reply_markup=Calendar.create_year_calendar(year)
                    )
                elif view_type == "DECADE":
                    await query.edit_message_reply_markup(
                        reply_markup=Calendar.create_decade_calendar(year)
                    )
                elif view_type == "MONTH":
                    month = int(parts[4]) if len(parts) > 4 else 1
                    await query.edit_message_reply_markup(
                        reply_markup=Calendar.create_calendar(year, month, 'month')
                    )
                return DATA_GASTO

            # ========== SELEÇÃO DE MÊS/ANO ==========
            if data.startswith("CAL_SELECT_MONTH_"):
                parts = data.split('_')
                year, month = int(parts[3]), int(parts[4])
                await query.edit_message_reply_markup(
                    reply_markup=Calendar.create_calendar(year, month, 'month')
                )
                return DATA_GASTO

            if data.startswith("CAL_SELECT_YEAR_"):
                parts = data.split('_')
                year = int(parts[3])
                await query.edit_message_reply_markup(
                    reply_markup=Calendar.create_year_calendar(year)
                )
                return DATA_GASTO

            # ========== NAVEGAÇÃO MENSAL ==========
            if data.startswith("CAL_PREV_MONTH_") or data.startswith("CAL_NEXT_MONTH_"):
                parts = data.split('_')
                year, month = int(parts[3]), int(parts[4])
                
                if data.startswith("CAL_PREV_MONTH_"):
                    month -= 1
                    if month < 1:
                        month, year = 12, year - 1
                else:
                    month += 1
                    if month > 12:
                        month, year = 1, year + 1
                
                try:
                    await query.edit_message_reply_markup(
                        reply_markup=Calendar.create_calendar(year, month, 'month')
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=query.from_user.id,
                        text="📅 Navegação do calendário:",
                        reply_markup=Calendar.create_calendar(year, month, 'month')
                    )
                return DATA_GASTO

            # ========== NAVEGAÇÃO ANUAL ==========
            if data.startswith("CAL_PREV_YEAR_") or data.startswith("CAL_NEXT_YEAR_"):
                parts = data.split('_')
                year = int(parts[3])
                
                if data.startswith("CAL_PREV_YEAR_"):
                    year -= 1
                else:
                    year += 1
                
                await query.edit_message_reply_markup(
                    reply_markup=Calendar.create_year_calendar(year)
                )
                return DATA_GASTO

            # ========== NAVEGAÇÃO DE DÉCADA ==========
            if data.startswith("CAL_PREV_DECADE_") or data.startswith("CAL_NEXT_DECADE_"):
                parts = data.split('_')
                decade_start = int(parts[3])
                
                if data.startswith("CAL_PREV_DECADE_"):
                    decade_start -= 10
                else:
                    decade_start += 10
                
                await query.edit_message_reply_markup(
                    reply_markup=Calendar.create_decade_calendar(decade_start)
                )
                return DATA_GASTO

            # ========== IGNORAR ==========
            if data == "CAL_IGNORE":
                return DATA_GASTO

            return DATA_GASTO

        except Exception as e:
            logger.error(f"Erro no calendário: {e}")
            await query.message.reply_text("❌ Erro ao processar seleção.", reply_markup=gastos_keyboard())
            return ConversationHandler.END

    @staticmethod
    async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
        """Processa a seleção final da data"""
        query = update.callback_query
        user_id = context.user_data.get('user_id', query.from_user.id)
        
        required_keys = ['tipo_gasto', 'categoria', 'valor_gasto']
        if any(k not in context.user_data for k in required_keys):
            await query.message.reply_text("❌ Dados incompletos. Comece novamente.", reply_markup=gastos_keyboard())
            return ConversationHandler.END

        tipo_gasto = context.user_data['tipo_gasto']
        categoria = context.user_data['categoria']
        valor = context.user_data['valor_gasto']
        descricao = f"{categoria} - {tipo_gasto}"

        success = db.add_transaction(user_id, tipo_gasto, categoria, categoria, valor, descricao, date_str)

        if success:
            try:
                await query.edit_message_text(f"✅ Data selecionada: {date_str}")
            except Exception:
                pass

            await query.message.reply_text(
                f"🎉 GASTO REGISTRADO!\n\n"
                f"📋 Detalhes:\n"
                f"• 🏷️ Tipo: {tipo_gasto.upper()}\n"
                f"• 📂 Categoria: {categoria}\n"
                f"• 💰 Valor: R$ {valor:,.2f}\n"
                f"• 📅 Data: {date_str}\n\n"
                f"❓ Continuar adicionando gastos?",
                reply_markup=sim_nao_keyboard()
            )
            return CONTINUAR_GASTOS
        else:
            await query.message.reply_text("❌ Erro ao registrar gasto.", reply_markup=gastos_keyboard())
            return ConversationHandler.END

class MonthYearCalendar:
    @staticmethod
    def create_month_year_calendar(year=None):
        now = datetime.datetime.now()
        year = year or now.year
        keyboard = []
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"MY_PREV_{year}"),
            InlineKeyboardButton(f"{year}", callback_data="MY_IGNORE"),
            InlineKeyboardButton("▶️", callback_data=f"MY_NEXT_{year}")
        ])
        
        months_ptbr = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        for i in range(0, 12, 4):
            row = []
            for j in range(4):
                month_num = i + j + 1
                month_name = months_ptbr[i + j]
                if month_num == now.month and year == now.year:
                    month_name = f"•{month_name}•"
                row.append(InlineKeyboardButton(month_name, callback_data=f"MY_MONTH_{year}_{month_num:02d}"))
            keyboard.append(row)
        
        # BOTÕES CORRETOS - INCLUINDO "DIGITAR"
        keyboard.append([
            InlineKeyboardButton("📅 Este Mês", callback_data=f"MY_MONTH_{now.year}_{now.month:02d}"),
            InlineKeyboardButton("⌨️ Digitar", callback_data="MY_MANUAL")
        ])
        keyboard.append([
            InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="MY_BACK")
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        try:
            # CALLBACKS PARA EXTRATO
            if data == "EXTRATO_SHOW_CALENDAR":
                await query.edit_message_text(
                    "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver o extrato detalhado:",
                    reply_markup=MonthYearCalendar.create_month_year_calendar()
                )
                return EXTRATO_MES
                    
            elif data == "EXTRATO_BACK":
                try:
                    await query.edit_message_text("🏠 Voltando ao Menu", reply_markup=None)
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem: {e}")
                
                await context.bot.send_message(
                    query.from_user.id,
                    "🏠 MENU PRINCIPAL", 
                    reply_markup=main_keyboard()
                )
                return ConversationHandler.END
            
            # BOTÃO "VOLTAR AO MENU" DO CALENDÁRIO
            elif data == "MY_BACK":
                try:
                    await query.edit_message_text("🏠 Voltando ao Menu", reply_markup=None)
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem: {e}")
                
                await context.bot.send_message(
                    query.from_user.id,
                    "🏠 MENU PRINCIPAL", 
                    reply_markup=main_keyboard()
                )
                return ConversationHandler.END

            # BOTÃO "DIGITAR" - CORRIGIDO
            elif data == "MY_MANUAL":
                try:
                    await query.edit_message_text(
                        "⌨️ **DIGITE O MÊS E ANO**\n\n"
                        "📋 **Formatos aceitos:**\n"
                        "• **MM/AAAA** (ex: 03/2024)\n"
                        "• **MMAAAA** (ex: 032024)\n\n"
                        "💡 **Exemplos:**\n"
                        "• Março de 2024 → 03/2024 ou 032024\n"
                        "• Dezembro de 2023 → 12/2023 ou 122023\n\n"
                        "Digite o mês e ano no formato desejado:",
                        reply_markup=None
                    )
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem para entrada manual: {e}")
                    # Fallback: enviar nova mensagem
                    await context.bot.send_message(
                        query.from_user.id,
                        "⌨️ **DIGITE O MÊS E ANO**\n\n"
                        "📋 **Formatos aceitos:**\n"
                        "• **MM/AAAA** (ex: 03/2024)\n"
                        "• **MMAAAA** (ex: 032024)\n\n"
                        "💡 **Exemplos:**\n"
                        "• Março de 2024 → 03/2024 ou 032024\n"
                        "• Dezembro de 2023 → 12/2023 ou 122023\n\n"
                        "Digite o mês e ano no formato desejado:",
                        reply_markup=ReplyKeyboardRemove()
                    )
                
                return EXTRATO_MES
            
            # NAVEGAÇÃO ANO ANTERIOR
            elif data.startswith("MY_PREV_"):
                year = int(data.split('_')[2]) - 1
                await query.edit_message_reply_markup(reply_markup=MonthYearCalendar.create_month_year_calendar(year))
                return EXTRATO_MES
            
            # NAVEGAÇÃO PRÓXIMO ANO
            elif data.startswith("MY_NEXT_"):
                year = int(data.split('_')[2]) + 1
                await query.edit_message_reply_markup(reply_markup=MonthYearCalendar.create_month_year_calendar(year))
                return EXTRATO_MES
            
            # SELEÇÃO DE MÊS PARA EXTRATO
            elif data.startswith("MY_MONTH_"):
                parts = data.split('_')
                year, month = int(parts[2]), int(parts[3])
                
                try:
                    await query.edit_message_text("📊 Gerando extrato...")
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem: {e}")
                
                await MonthYearCalendar.show_month_extrato(query, context, year, month)
                return EXTRATO_MES
                
        except Exception as e:
            logger.error(f"Erro no calendário do extrato: {e}")
            await query.message.reply_text("❌ Erro ao processar seleção.", reply_markup=main_keyboard())
            return ConversationHandler.END
            
    @staticmethod        
    async def show_month_extrato(update_or_query, context, year: int, month: int):
        """Mostra o extrato detalhado do mês selecionado"""
        try:
            # Determinar o tipo de entrada de forma mais robusta
            user_id = None
            message_obj = None
            is_callback = False
            
            # Caso 1: É uma CallbackQuery (seleção no calendário)
            if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
                query = update_or_query.callback_query
                user_id = query.from_user.id
                message_obj = query.message
                is_callback = True
                
            # Caso 2: É um Update com message (entrada manual)
            elif hasattr(update_or_query, 'message') and update_or_query.message:
                user_id = update_or_query.message.from_user.id
                message_obj = update_or_query.message
                is_callback = False
                
            # Caso 3: É uma CallbackQuery direta
            elif hasattr(update_or_query, 'from_user'):
                user_id = update_or_query.from_user.id
                message_obj = update_or_query.message if hasattr(update_or_query, 'message') else None
                is_callback = True
                
            else:
                # Fallback: tentar obter user_id do contexto
                if context and context.user_data:
                    user_id = context.user_data.get('user_id')
                if not user_id:
                    raise ValueError("Não foi possível determinar o usuário")

            # Buscar todas as transações do mês
            transactions = db.get_monthly_transactions(user_id, month, year)
            user_data = db.get_user_data(user_id)
            nickname = user_data['nickname'] if user_data else 'Usuário'
            
            meses_ptbr = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            month_name = meses_ptbr[month-1]
            
            response = f"📊 **EXTRATO DETALHADO - {month_name}/{year}**\n\n"
            response += f"👤 **Usuário:** {nickname}\n\n"
            
            if not transactions:
                response += "📝 Nenhuma transação registrada neste mês."
            else:
                # Agrupar por tipo e categoria
                transacoes_por_tipo = {'fixo': {}, 'flexivel': {}}
                total_fixo = 0
                total_flexivel = 0
                
                for transacao in transactions:
                    tipo = transacao['tipo']
                    categoria = transacao['categoria']
                    valor = transacao['valor']
                    
                    if categoria not in transacoes_por_tipo[tipo]:
                        transacoes_por_tipo[tipo][categoria] = []
                    
                    transacoes_por_tipo[tipo][categoria].append(transacao)
                    
                    if tipo == 'fixo':
                        total_fixo += valor
                    else:
                        total_flexivel += valor
                
                total_geral = total_fixo + total_flexivel
                
                # Gastos Fixos
                if transacoes_por_tipo['fixo']:
                    response += "🏠 **GASTOS FIXOS**\n"
                    for categoria, transacoes in transacoes_por_tipo['fixo'].items():
                        total_categoria = sum(t['valor'] for t in transacoes)
                        response += f"• {categoria}: R$ {total_categoria:,.2f}\n"
                    
                    response += f"📌 **Total Fixo:** R$ {total_fixo:,.2f}\n\n"
                
                # Gastos Flexíveis
                if transacoes_por_tipo['flexivel']:
                    response += "🛍️ **GASTOS FLEXÍVEIS**\n"
                    for categoria, transacoes in transacoes_por_tipo['flexivel'].items():
                        total_categoria = sum(t['valor'] for t in transacoes)
                        response += f"• {categoria}: R$ {total_categoria:,.2f}\n"
                    
                    response += f"📌 **Total Flexível:** R$ {total_flexivel:,.2f}\n\n"
                
                # Resumo Geral
                response += f"🎯 **RESUMO DO MÊS**\n"
                response += f"💰 **Total Gasto:** R$ {total_geral:,.2f}\n"
                
                if user_data and user_data.get('salario_liquido') and user_data['salario_liquido'] > 0:
                    salario = user_data['salario_liquido']
                    saldo = salario - total_geral
                    percentual = (total_geral / salario * 100) if salario > 0 else 0
                    
                    response += f"💵 **Salário:** R$ {salario:,.2f}\n"
                    response += f"⚖️ **Saldo:** R$ {saldo:,.2f}\n"
                    response += f"📈 **Comprometido:** {percentual:.1f}%\n"
                    
                    # Análise de saúde
                    if percentual <= 60:
                        response += "✅ **Situação:** Saudável\n"
                    elif percentual <= 85:
                        response += "⚠️ **Situação:** Atenção\n"
                    else:
                        response += "🚨 **Situação:** Crítico\n"
                
                response += f"\n📋 **Total de transações:** {len(transactions)}"

            # Botões de navegação
            keyboard = [
                [InlineKeyboardButton("📅 Ver Outro Mês", callback_data="EXTRATO_SHOW_CALENDAR")],
                [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="EXTRATO_BACK")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Enviar resposta baseada no tipo de entrada
            if is_callback:
                # Para callbacks, editar a mensagem existente
                try:
                    if len(response) <= 4000:
                        await update_or_query.edit_message_text(
                            text=response, 
                            reply_markup=reply_markup, 
                            parse_mode='Markdown'
                        )
                    else:
                        # Dividir mensagem longa
                        parte1 = response[:4000]
                        parte2 = response[4000:]
                        await update_or_query.edit_message_text(parte1, reply_markup=reply_markup, parse_mode='Markdown')
                        await context.bot.send_message(user_id, parte2, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem: {e}")
                    # Fallback: enviar nova mensagem
                    await context.bot.send_message(user_id, response, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # Para mensagens normais, enviar nova mensagem
                if len(response) <= 4000:
                    await message_obj.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    parte1 = response[:4000]
                    parte2 = response[4000:]
                    await message_obj.reply_text(parte1, reply_markup=reply_markup, parse_mode='Markdown')
                    await context.bot.send_message(user_id, parte2, parse_mode='Markdown')
                        
        except Exception as e:
            logger.error(f"Erro ao gerar extrato mensal: {e}")
            
            error_message = "❌ Erro ao carregar extrato."
            
            # Determinar user_id para mensagem de erro de forma segura
            try:
                user_id = None
                if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
                    user_id = update_or_query.callback_query.from_user.id
                elif hasattr(update_or_query, 'message') and update_or_query.message:
                    user_id = update_or_query.message.from_user.id
                elif hasattr(update_or_query, 'from_user'):
                    user_id = update_or_query.from_user.id
                elif context and context.user_data:
                    user_id = context.user_data.get('user_id')
                    
                if not user_id:
                    logger.error("Não foi possível obter user_id para enviar mensagem de erro")
                    return
                    
            except Exception as user_error:
                logger.error(f"Erro ao obter user_id: {user_error}")
                return

            keyboard = [
                [InlineKeyboardButton("📅 Tentar Novamente", callback_data="EXTRATO_SHOW_CALENDAR")],
                [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="EXTRATO_BACK")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await context.bot.send_message(user_id, error_message, reply_markup=reply_markup)
            except Exception as send_error:
                logger.error(f"Erro ao enviar mensagem de erro: {send_error}")

# ========== HANDLERS PRINCIPAIS ==========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operação cancelada.", reply_markup=main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id
    
    if db.user_exists(user_id):
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname']
        await update.message.reply_text(
            f"👋 Olá, {nickname}! Que bom te ver de volta!\n\n"
            f"Estou aqui para te ajudar a:\n"
            f"• 💸 Controlar seus gastos\n"
            f"• 📈 Melhorar sua saúde financeira\n"
            f"• 🎓 Aprender sobre finanças\n\n"
            f"O que gostaria de fazer hoje?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 Bem-vindo ao Edu - Seu Assistente Financeiro!\n\n"
            "Vamos começar! Qual o seu nome?"
        )
        return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nickname = update.message.text.strip()
    if not nickname:
        await update.message.reply_text("❌ Por favor, digite um nome válido.")
        return GET_NAME
    
    context.user_data['nickname'] = nickname
    await update.message.reply_text(
        f"Prazer, {nickname}!\n\n"
        f"💰 Vamos configurar seu perfil financeiro.\n"
        f"Qual o valor do seu salário líquido mensal?\n"
        f"(Ex.: 1500,00)",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_SALARY

async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        salario_liquido = float(salary_text)
        
        if salario_liquido <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return GET_SALARY
        
        user_id = context.user_data['user_id']
        nickname = context.user_data['nickname']
        
        # Adicionar usuário
        success = db.add_user(user_id, nickname, salario_liquido)
        if not success:
            await update.message.reply_text("❌ Erro ao salvar dados.")
            return GET_SALARY        
        await update.message.reply_text(f"🎉 Perfil criado com sucesso, {nickname}!")
        
        # Educação financeira
        await update.message.reply_text(
            "💡 Educação Financeira: Tipos de Gastos\n\n"
            "🏠 GASTOS FIXOS: despesas regulares e previsíveis\n"
            "🛍️ GASTOS FLEXÍVEIS: despesas variáveis"
        )
        
        # Adicionar salário principal
        db.add_salary(user_id, "Salário Principal", salario_liquido, principal=True)
        
        await update.message.reply_text(
            "💰 SALÁRIO PRINCIPAL CONFIGURADO!\n\n"
            f"• 📝 Origem: Salário Principal\n"
            f"• 💰 Valor: R$ {salario_liquido:,.2f}\n\n"
            "💡 Você pode adicionar mais salários extras em 'Gastos / Rendas' → 'Salário'",
            reply_markup=tipo_gasto_keyboard()
        )
        
        return TIPO_GASTO
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 1500,00")
        return GET_SALARY

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /menu"""
    await update.message.reply_text(
        "🏠 **MENU PRINCIPAL**\n\n"
        "O que você gostaria de fazer?",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END
    
async def ajuda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /ajuda com mensagem formatada corretamente"""
    try:
        # Mensagem de ajuda com Markdown corrigido
        help_text = """
🤖 *COMANDOS DISPONÍVEIS*

*📊 Gestão Financeira*
/start - Iniciar o bot
/menu - Menu principal
/ajuda - Esta mensagem de ajuda
/salario - Definir seu salário
/gastos - Adicionar gastos
/resumo - Ver resumo financeiro
/analise - Análise da saúde financeira
/metas - Gerenciar metas financeiras 

*💡 Educação Financeira*
/dicas - Dicas personalizadas
/aprender - Conteúdo educacional
/ia_analise - Análise detalhada com IA
/recomendacoes - Recomendações personalizadas

*⚙️ Configurações*
/config - Configurações do usuário
/limpar - Limpar dados
/sobre - Sobre o bot

*💬 Suporte*
/feedback - Enviar feedback
/duvidas - Tirar dúvidas

*Dicas de uso:*
• Use /salario para definir sua renda mensal
• Adicione gastos com /gastos
• Consulte /resumo para ver seu panorama
• Use /analise para ver sua saúde financeira
• Explore /aprender para conteúdo educativo

*Suporte:* Contate o desenvolvedor em caso de problemas.
        """.strip()

        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2',
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Erro no handler de ajuda: {e}")
        # Fallback sem formatação Markdown
        fallback_text = """
🤖 COMANDOS DISPONÍVEIS

📊 Gestão Financeira
/start - Iniciar o bot
/menu - Menu principal
/ajuda - Esta mensagem de ajuda
/salario - Definir seu salário
/gastos - Adicionar gastos
/resumo - Ver resumo financeiro
/analise - Análise da saúde financeira
/metas - Gerenciar metas financeiras

💡 Educação Financeira
/dicas - Dicas personalizadas
/aprender - Conteúdo educacional
/ia_analise - Análise detalhada com IA
/recomendacoes - Recomendações personalizadas

⚙️ Configurações
/config - Configurações do usuário
/limpar - Limpar dados
/sobre - Sobre o bot

💬 Suporte
/feedback - Enviar feedback
/duvidas - Tirar dúvidas

Dicas de uso:
• Use /salario para definir sua renda mensal
• Adicione gastos com /gastos
• Consulte /resumo para ver seu panorama
• Use /analise para ver sua saúde financeira
• Explore /aprender para conteúdo educativo

Suporte: Contate o desenvolvedor em caso de problemas.
        """.strip()
        
        await update.message.reply_text(
            fallback_text,
            reply_markup=ReplyKeyboardRemove()
        )
    
# ========== HANDLERS PARA SALÁRIO ==========

async def salario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para gerenciar salários"""
    logger.info("💰 Menu de salários acessado")
    await update.message.reply_text(
        "💰 GERENCIAR SALÁRIOS\n\n"
        "Escolha uma opção:",
        reply_markup=ReplyKeyboardMarkup([
            ['💵 Adicionar Salário', '✏️ Alterar Salários'],
            ['📊 Consultar Salários', '🏠 Voltar ao Menu']
        ], resize_keyboard=True)
    )
    return ConversationHandler.END
    
async def add_salary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de adicionar salário"""
    await update.message.reply_text(
        "💵 ADICIONAR SALÁRIO\n\n"
        "📝 Qual a fonte/origem deste salário?\n"
        "(Ex: Empresa XPTO, Freelance, etc.)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_SALARY_ORIGIN

async def add_salary_origin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origem = update.message.text.strip()
    if not origem:
        await update.message.reply_text("❌ Por favor, digite uma origem válida.")
        return ADD_SALARY_ORIGIN
    
    context.user_data['salary_origin'] = origem
    await update.message.reply_text(
        f"💰 Qual o valor do salário da {origem}?\n"
        f"(Ex: 2500,00)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_SALARY_VALUE

async def add_salary_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor_text = update.message.text.replace(',', '.').strip()
        valor = float(valor_text)
        
        if valor <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return ADD_SALARY_VALUE
        
        user_id = update.effective_user.id
        origem = context.user_data['salary_origin']
        
        # Verificar se é o primeiro salário (será o principal)
        salaries = db.get_salaries(user_id)
        is_principal = len(salaries) == 0
        
        success = db.add_salary(user_id, origem, valor, is_principal)
        
        if success:
            if is_principal:
                message = (
                    f"✅ SALÁRIO PRINCIPAL ADICIONADO!\n\n"
                    f"📋 Detalhes:\n"
                    f"• 📝 Fonte/Origem: {origem}\n"
                    f"• 💰 Valor: R$ {valor:,.2f}\n"
                    f"• 🎯 Status: Salário Principal\n\n"
                    f"💡 Este é seu salário principal. Você pode adicionar mais salários extras."
                )
            else:
                message = (
                    f"✅ SALÁRIO ADICIONADO!\n\n"
                    f"📋 Detalhes:\n"
                    f"• 📝 Fonte/Origem: {origem}\n"
                    f"• 💰 Valor: R$ {valor:,.2f}\n"
                    f"• 📊 Status: Salário Extra"
                )
            
            await update.message.reply_text(message, reply_markup=gastos_keyboard())
        else:
            await update.message.reply_text("❌ Erro ao adicionar salário.", reply_markup=gastos_keyboard())
        
        # Limpar dados temporários
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex: 2500,00)")
        return ADD_SALARY_VALUE

async def consultar_salarios_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para consultar todos os salários"""
    user_id = update.effective_user.id
    
    # Verificar se o usuário existe
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    salaries = db.get_salaries(user_id)
    
    if not salaries:
        await update.message.reply_text(
            "💰 NENHUM SALÁRIO CADASTRADO\n\n"
            "Você ainda não cadastrou nenhum salário.\n"
            "Use '💵 Adicionar Salário' para cadastrar seu primeiro salário.",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    total = sum(salary['valor'] for salary in salaries)
    
    response = "💰 EXTRATO DE SALÁRIOS\n\n"
    
    for i, salary in enumerate(salaries, 1):
        principal_indicator = " 🎯" if salary['principal'] else ""
        status = "⭐ PRINCIPAL" if salary['principal'] else "📊 EXTRA"
        
        response += f"{i}. {salary['origem']}{principal_indicator}\n"
        response += f"   💰 R$ {salary['valor']:,.2f}\n"
        response += f"   📝 {status}\n"
        
        # Formatar data de criação
        try:
            data_obj = datetime.datetime.strptime(salary['data_criacao'], '%Y-%m-%d %H:%M:%S')
            data_formatada = data_obj.strftime('%d/%m/%Y')
            response += f"   📅 Cadastrado em: {data_formatada}\n"
        except:
            response += f"   📅 Cadastrado em: {salary['data_criacao']}\n"
        
        response += "\n"
    
    response += f"💵 TOTAL MENSAL: R$ {total:,.2f}\n\n"
    response += "💡 Use '✏️ Alterar Salários' para editar ou excluir salários extras."
    
    await update.message.reply_text(response, reply_markup=gastos_keyboard())
    return ConversationHandler.END

async def alterar_salarios_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para alterar salários"""
    user_id = update.effective_user.id
    salaries = db.get_salaries(user_id)
    
    if not salaries:
        await update.message.reply_text(
            "💰 NENHUM SALÁRIO CADASTRADO\n\n"
            "Você ainda não cadastrou nenhum salário.\n"
            "Use '💵 Adicionar Salário' para cadastrar.",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    # Criar keyboard com os salários
    keyboard = []
    for salary in salaries:
        principal_indicator = " 🎯" if salary['principal'] else ""
        button_text = f"{salary['origem']}{principal_indicator} - R$ {salary['valor']:,.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_salary_{salary['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_edit_salary")])
    
    await update.message.reply_text(
        "✏️ ALTERAR SALÁRIOS\n\n"
        "Selecione o salário que deseja alterar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_SALARY_SELECT

async def edit_salary_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção do salário para edição"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_edit_salary":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "💰 GERENCIAR SALÁRIOS",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("edit_salary_"):
        salary_id = int(data.split('_')[2])
        context.user_data['selected_salary_id'] = salary_id
        
        # Buscar informações do salário
        user_id = query.from_user.id
        salaries = db.get_salaries(user_id)
        selected_salary = None
        
        for salary in salaries:
            if salary['id'] == salary_id:
                selected_salary = salary
                break
        
        if selected_salary:
            # Criar opções baseadas no tipo de salário
            keyboard = []
            
            if selected_salary['principal']:
                keyboard.append([InlineKeyboardButton("✏️ Renomear Origem", callback_data="edit_origin")])
                keyboard.append([InlineKeyboardButton("💰 Alterar Valor", callback_data="edit_value")])
            else:
                keyboard.append([InlineKeyboardButton("✏️ Renomear Origem", callback_data="edit_origin")])
                keyboard.append([InlineKeyboardButton("💰 Alterar Valor", callback_data="edit_value")])
                keyboard.append([InlineKeyboardButton("🎯 Tornar Principal", callback_data="make_principal")])
                keyboard.append([InlineKeyboardButton("🗑️ Excluir Salário", callback_data="delete_salary")])
            
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_action")])
            
            principal_text = " (PRINCIPAL)" if selected_salary['principal'] else ""
            
            await query.edit_message_text(
                f"✏️ EDITAR SALÁRIO\n\n"
                f"📝 Origem: {selected_salary['origem']}{principal_text}\n"
                f"💰 Valor: R$ {selected_salary['valor']:,.2f}\n\n"
                f"Escolha uma ação:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return EDIT_SALARY_ACTION
    
    await query.edit_message_text("❌ Erro ao selecionar salário.")
    return ConversationHandler.END

async def edit_salary_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a ação selecionada para o salário"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    salary_id = context.user_data.get('selected_salary_id')
    
    if data == "cancel_action":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "💰 GERENCIAR SALÁRIOS",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    if data == "edit_origin":
        await query.edit_message_text(
            "✏️ RENOMEAR ORIGEM\n\n"
            "Digite o novo nome para a origem deste salário:"
        )
        return EDIT_SALARY_ORIGIN
    
    elif data == "edit_value":
        await query.edit_message_text(
            "💰 ALTERAR VALOR\n\n"
            "Digite o novo valor para este salário:\n"
            "(Ex: 3000,00)"
        )
        return EDIT_SALARY_VALUE
    
    elif data == "make_principal":
        user_id = query.from_user.id
        success = db.set_principal_salary(salary_id, user_id)  # ← corrigido (antes podia usar tornar_principal)
        
        if success:
            await query.edit_message_text(
                "✅ SALÁRIO DEFINIDO COMO PRINCIPAL!\n\n"
                "Este salário agora é seu salário principal.",
                reply_markup=gastos_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao definir salário principal.",
                reply_markup=gastos_keyboard()
            )
        return ConversationHandler.END
    
    elif data == "delete_salary":
        success = db.delete_salary(salary_id)  # ← corrigido (antes podia usar excluir_salario)
        
        if success:
            await query.edit_message_text(
                "✅ SALÁRIO EXCLUÍDO!\n\n"
                "O salário foi removido com sucesso.",
                reply_markup=gastos_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Não é possível excluir o salário principal.\n"
                "Apenas salários extras podem ser excluídos.",
                reply_markup=gastos_keyboard()
            )
        return ConversationHandler.END
    
    return ConversationHandler.END

async def edit_salary_origin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a edição da origem do salário"""
    new_origin = update.message.text.strip()
    salary_id = context.user_data.get('selected_salary_id')
    
    if not new_origin:
        await update.message.reply_text("❌ Origem inválida. Digite novamente:")
        return EDIT_SALARY_ORIGIN
    
    success = db.update_salary(salary_id, origem=new_origin)
    
    if success:
        await update.message.reply_text(
            f"✅ ORIGEM ALTERADA!\n\n"
            f"Novo nome: {new_origin}",
            reply_markup=gastos_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Erro ao alterar origem.",
            reply_markup=gastos_keyboard()
        )
    
    # Limpar dados temporários
    context.user_data.clear()
    return ConversationHandler.END

async def edit_salary_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a edição do valor do salário"""
    try:
        valor_text = update.message.text.replace(',', '.').strip()
        new_value = float(valor_text)
        salary_id = context.user_data.get('selected_salary_id')
        
        if new_value <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Digite novamente:")
            return EDIT_SALARY_VALUE
        
        success = db.update_salary(salary_id, valor=new_value)
        
        if success:
            await update.message.reply_text(
                f"✅ VALOR ALTERADO!\n\n"
                f"Novo valor: R$ {new_value:,.2f}",
                reply_markup=gastos_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao alterar valor.",
                reply_markup=gastos_keyboard()
            )
        
        # Limpar dados temporários
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex: 3000,00)")
        return EDIT_SALARY_VALUE

# ========== HANDLERS PARA RENDAS EXTRAS ==========

async def renda_extra_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para gerenciar rendas extras"""
    await update.message.reply_text(
        "💵 GERENCIAR RENDAS EXTRAS\n\n"
        "Escolha uma opção:",
        reply_markup=ReplyKeyboardMarkup([
            ['💵 Adicionar Renda Extra', '✏️ Alterar Rendas Extras'],
            ['📊 Consultar Rendas Extras', '🏠 Voltar ao Menu']
        ], resize_keyboard=True)
    )
    return ConversationHandler.END

async def add_extra_income_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de adicionar renda extra"""
    await update.message.reply_text(
        "💵 ADICIONAR RENDA EXTRA\n\n"
        "📝 Qual a fonte/origem desta renda extra?\n"
        "(Ex: Freelance, Bico, Investimentos, etc.)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_EXTRA_INCOME_ORIGIN

async def add_extra_income_origin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origem = update.message.text.strip()
    if not origem:
        await update.message.reply_text("❌ Por favor, digite uma origem válida.")
        return ADD_EXTRA_INCOME_ORIGIN
    
    context.user_data['extra_income_origin'] = origem
    await update.message.reply_text(
        f"💰 Qual o valor da renda extra de {origem}?\n"
        f"(Ex: 500,00)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_EXTRA_INCOME_VALUE

async def add_extra_income_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor_text = update.message.text.replace(',', '.').strip()
        valor = float(valor_text)
        
        if valor <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return ADD_EXTRA_INCOME_VALUE
        
        user_id = update.effective_user.id
        origem = context.user_data['extra_income_origin']
        
        success = db.add_extra_income(user_id, origem, valor)
        
        if success:
            message = (
                f"✅ RENDA EXTRA ADICIONADA!\n\n"
                f"📋 Detalhes:\n"
                f"• 📝 Fonte/Origem: {origem}\n"
                f"• 💰 Valor: R$ {valor:,.2f}\n"
            )
            
            await update.message.reply_text(message, reply_markup=gastos_keyboard())
        else:
            await update.message.reply_text("❌ Erro ao adicionar renda extra.", reply_markup=gastos_keyboard())
        
        # Limpar dados temporários
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex: 500,00)")
        return ADD_EXTRA_INCOME_VALUE

async def consultar_rendas_extras_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para consultar todas as rendas extras"""
    user_id = update.effective_user.id
    
    # Verificar se o usuário existe
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    incomes = db.get_extra_incomes(user_id)
    
    if not incomes:
        await update.message.reply_text(
            "💵 NENHUMA RENDA EXTRA CADASTRADA\n\n"
            "Você ainda não cadastrou nenhuma renda extra.\n"
            "Use '💵 Adicionar Renda Extra' para cadastrar sua primeira renda extra.",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    total = sum(income['valor'] for income in incomes)
    
    response = "💵 EXTRATO DE RENDAS EXTRAS\n\n"
    
    for i, income in enumerate(incomes, 1):
        response += f"{i}. 📝 {income['origem']}\n"
        response += f"   💰 R$ {income['valor']:,.2f}\n"
        
        # Formatar data de criação
        try:
            data_obj = datetime.datetime.strptime(income['data_criacao'], '%Y-%m-%d %H:%M:%S')
            data_formatada = data_obj.strftime('%d/%m/%Y')
            response += f"   📅 Cadastrado em: {data_formatada}\n"
        except:
            response += f"   📅 Cadastrado em: {income['data_criacao']}\n"
        
        response += "\n"
    
    response += f"💵 TOTAL DE RENDAS EXTRAS: R$ {total:,.2f}\n\n"
    response += "💡 Use '✏️ Alterar Rendas Extras' para editar ou excluir."
    
    await update.message.reply_text(response, reply_markup=gastos_keyboard())
    return ConversationHandler.END

async def alterar_rendas_extras_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para alterar rendas extras"""
    user_id = update.effective_user.id
    incomes = db.get_extra_incomes(user_id)
    
    if not incomes:
        await update.message.reply_text(
            "💵 NENHUMA RENDA EXTRA CADASTRADA\n\n"
            "Você ainda não cadastrou nenhuma renda extra.\n"
            "Use '💵 Adicionar Renda Extra' para cadastrar.",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    # Criar keyboard com as rendas extras
    keyboard = []
    for income in incomes:
        button_text = f"{income['origem']} - R$ {income['valor']:,.2f}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_extra_income_{income['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_edit_extra_income")])
    
    await update.message.reply_text(
        "✏️ ALTERAR RENDAS EXTRAS\n\n"
        "Selecione a renda extra que deseja alterar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_EXTRA_INCOME_SELECT

async def edit_extra_income_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção da renda extra para edição"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_edit_extra_income":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "💵 GERENCIAR RENDAS EXTRAS",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("edit_extra_income_"):
        income_id = int(data.split('_')[3])
        context.user_data['selected_extra_income_id'] = income_id
        
        # Buscar informações da renda extra
        user_id = query.from_user.id
        incomes = db.get_extra_incomes(user_id)
        selected_income = None
        
        for income in incomes:
            if income['id'] == income_id:
                selected_income = income
                break
        
        if selected_income:
            # Criar opções
            keyboard = [
                [InlineKeyboardButton("✏️ Renomear Origem", callback_data="edit_extra_origin")],
                [InlineKeyboardButton("💰 Alterar Valor", callback_data="edit_extra_value")],
                [InlineKeyboardButton("🗑️ Excluir Renda Extra", callback_data="delete_extra_income")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_extra_action")]
            ]
            
            await query.edit_message_text(
                f"✏️ EDITAR RENDA EXTRA\n\n"
                f"📝 Origem: {selected_income['origem']}\n"
                f"💰 Valor: R$ {selected_income['valor']:,.2f}\n\n"
                f"Escolha uma ação:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return EDIT_EXTRA_INCOME_ACTION
    
    await query.edit_message_text("❌ Erro ao selecionar renda extra.")
    return ConversationHandler.END

async def edit_extra_income_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a ação selecionada para a renda extra"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    income_id = context.user_data.get('selected_extra_income_id')
    
    if data == "cancel_extra_action":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "💵 GERENCIAR RENDAS EXTRAS",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
    
    if data == "edit_extra_origin":
        await query.edit_message_text(
            "✏️ RENOMEAR ORIGEM\n\n"
            "Digite o novo nome para a origem desta renda extra:"
        )
        return EDIT_EXTRA_INCOME_ORIGIN
    
    elif data == "edit_extra_value":
        await query.edit_message_text(
            "💰 ALTERAR VALOR\n\n"
            "Digite o novo valor para esta renda extra:\n"
            "(Ex: 600,00)"
        )
        return EDIT_EXTRA_INCOME_VALUE
    
    elif data == "delete_extra_income":
        success = db.delete_extra_income(income_id)
        
        if success:
            await query.edit_message_text(
                "✅ RENDA EXTRA EXCLUÍDA!\n\n"
                "A renda extra foi removida com sucesso.",
                reply_markup=gastos_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao excluir renda extra.",
                reply_markup=gastos_keyboard()
            )
        return ConversationHandler.END
    
    return ConversationHandler.END

async def edit_extra_income_origin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a edição da origem da renda extra"""
    new_origin = update.message.text.strip()
    income_id = context.user_data.get('selected_extra_income_id')
    
    if not new_origin:
        await update.message.reply_text("❌ Origem inválida. Digite novamente:")
        return EDIT_EXTRA_INCOME_ORIGIN
    
    success = db.update_extra_income(income_id, origem=new_origin)
    
    if success:
        await update.message.reply_text(
            f"✅ ORIGEM ALTERADA!\n\n"
            f"Novo nome: {new_origin}",
            reply_markup=gastos_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Erro ao alterar origem.",
            reply_markup=gastos_keyboard()
        )
    
    # Limpar dados temporários
    context.user_data.clear()
    return ConversationHandler.END

async def edit_extra_income_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a edição do valor da renda extra"""
    try:
        valor_text = update.message.text.replace(',', '.').strip()
        new_value = float(valor_text)
        income_id = context.user_data.get('selected_extra_income_id')
        
        if new_value <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Digite novamente:")
            return EDIT_EXTRA_INCOME_VALUE
        
        success = db.update_extra_income(income_id, valor=new_value)
        
        if success:
            await update.message.reply_text(
                f"✅ VALOR ALTERADO!\n\n"
                f"Novo valor: R$ {new_value:,.2f}",
                reply_markup=gastos_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao alterar valor.",
                reply_markup=gastos_keyboard()
            )
        
        # Limpar dados temporários
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex: 600,00)")
        return EDIT_EXTRA_INCOME_VALUE

# ========== REGISTRO DE GASTOS ==========
async def adicionar_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    context.user_data['user_id'] = user_id
    
    # CORREÇÃO: Mostrar o menu de gastos corretamente
    await update.message.reply_text(
        "🧮 GASTOS E RENDAS\n\nO que você gostaria de fazer?",
        reply_markup=gastos_keyboard()  # ← Este é o keyboard correto
    )
    return TIPO_GASTO

async def iniciar_registro_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    context.user_data['user_id'] = user_id
    text = update.message.text
    
    if 'Gastos Fixos' in text:
        context.user_data['tipo_gasto'] = 'fixo'
        await update.message.reply_text(
            "🏠 CATEGORIAS DE GASTOS FIXOS\n\nSelecione a categoria:",
            reply_markup=categorias_fixas_keyboard()
        )
        return CATEGORIA_FIXA
        
    elif 'Gastos Flexíveis' in text:
        context.user_data['tipo_gasto'] = 'flexivel'
        await update.message.reply_text(
            "🛍️ CATEGORIAS DE GASTOS FLEXÍVEIS\n\nSelecione a categoria:",
            reply_markup=categorias_flexiveis_keyboard()
        )
        return CATEGORIA_FLEXIVEL
        
    elif 'Gastos do Mês' in text:
        await update.message.reply_text(
            "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver as estatísticas:",
            reply_markup=MonthYearCalendar.create_month_year_calendar()
        )
        return EXTRATO_MES
        
    elif 'Suas Categorias' in text:
        await update.message.reply_text(
            "📂 SUAS CATEGORIAS\n\nGerencie suas categorias personalizadas:",
            reply_markup=suas_categorias_keyboard()
        )
        return SUAS_CATEGORIAS
        
    elif 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=gastos_keyboard())
        return ConversationHandler.END

async def tipo_gasto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'Gastos Fixos' in text:
        context.user_data['tipo_gasto'] = 'fixo'
        await update.message.reply_text("🏠 Selecione a categoria:", reply_markup=categorias_fixas_keyboard())
        return CATEGORIA_FIXA
        
    elif 'Gastos Flexíveis' in text:
        context.user_data['tipo_gasto'] = 'flexivel'
        await update.message.reply_text("🛍️ Selecione a categoria:", reply_markup=categorias_flexiveis_keyboard())
        return CATEGORIA_FLEXIVEL
        
    # CORREÇÃO: Adicionar tratamento para Salário e Renda extra
    elif 'Salário' in text:
        return await salario_handler(update, context)
        
    elif 'Renda extra' in text:
        return await renda_extra_handler(update, context)
        
    elif 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=gastos_keyboard())
        return TIPO_GASTO

# Alias para o conversation handler
tipo_gasto_gastos_conv_handler = tipo_gasto_handler

async def categoria_fixa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if text == 'Outros...':
        await update.message.reply_text(
            "🏠 OUTROS GASTOS FIXOS\n\nEscolha uma opção:",
            reply_markup=outros_fixos_keyboard()
        )
        return OUTROS_FIXOS
    
    # Verificar se a categoria existe nas categorias fixas
    if text not in config.CATEGORIAS_FIXAS and text != 'Outros...':
        await update.message.reply_text("❌ Categoria inválida. Selecione uma opção válida:", reply_markup=categorias_fixas_keyboard())
        return CATEGORIA_FIXA
    
    context.user_data['categoria'] = text
    await update.message.reply_text(
        f"🏠 {text.upper()}\n\n💰 Qual o valor deste gasto?",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def categoria_flexivel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if text == 'Outros...':
        await update.message.reply_text(
            "🛍️ OUTROS GASTOS FLEXÍVEIS\n\nEscolha uma opção:",
            reply_markup=outros_flexiveis_keyboard()
        )
        return OUTROS_FLEXIVEIS
    
    # Verificar se a categoria existe nas categorias flexíveis
    if text not in config.CATEGORIAS_FLEXIVEIS and text != 'Outros...':
        await update.message.reply_text("❌ Categoria inválida. Selecione uma opção válida:", reply_markup=categorias_flexiveis_keyboard())
        return CATEGORIA_FLEXIVEL
    
    context.user_data['categoria'] = text
    await update.message.reply_text(
        f"🛍️ {text.upper()}\n\n💰 Qual o valor deste gasto?",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def outros_flexiveis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = context.user_data['user_id']
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Minhas categorias' in text:
        custom_cats = db.get_custom_categories(user_id, 'flexivel')
        if not custom_cats:
            await update.message.reply_text("📝 Você ainda não tem categorias personalizadas.", reply_markup=outros_flexiveis_keyboard())
            return OUTROS_FLEXIVEIS
        await update.message.reply_text("📂 SUAS CATEGORIAS FLEXÍVEIS", reply_markup=minhas_categorias_keyboard(user_id))
        return MINHAS_CATEGORIAS
        
    if 'Adicionar novo' in text:
        await update.message.reply_text("➕ Nova categoria flexível. Qual o nome?", reply_markup=ReplyKeyboardRemove())
        return NOVA_CATEGORIA_OUTROS
    
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=outros_flexiveis_keyboard())
    return OUTROS_FLEXIVEIS

async def outros_fixos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = context.user_data['user_id']
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Minhas categorias' in text:
        custom_cats = db.get_custom_categories(user_id, 'fixo')
        if not custom_cats:
            await update.message.reply_text("📝 Você ainda não tem categorias personalizadas.", reply_markup=outros_fixos_keyboard())
            return OUTROS_FIXOS
        await update.message.reply_text("📂 SUAS CATEGORIAS FIXAS", reply_markup=minhas_categorias_fixas_keyboard(user_id))
        return MINHAS_CATEGORIAS_FIXAS
        
    if 'Adicionar novo' in text:
        await update.message.reply_text("➕ Nova categoria fixa. Qual o nome?", reply_markup=ReplyKeyboardRemove())
        return NOVA_CATEGORIA_OUTROS_FIXOS
    
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=outros_fixos_keyboard())
    return OUTROS_FIXOS

async def minhas_categorias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = context.user_data['user_id']
    
    if 'Voltar' in text:
        await update.message.reply_text("🛍️ OUTROS FLEXÍVEIS", reply_markup=outros_flexiveis_keyboard())
        return OUTROS_FLEXIVEIS
        
    custom_cats = db.get_custom_categories(user_id, 'flexivel')
    if text in custom_cats:
        context.user_data['categoria'] = text
        await update.message.reply_text(f"🛍️ {text}\n💰 Qual o valor deste gasto?", reply_markup=ReplyKeyboardRemove())
        return VALOR_GASTO
    
    await update.message.reply_text("❌ Selecione uma categoria válida:", reply_markup=minhas_categorias_keyboard(user_id))
    return MINHAS_CATEGORIAS

async def minhas_categorias_fixas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = context.user_data['user_id']
    
    if 'Voltar' in text:
        await update.message.reply_text("🏠 OUTROS FIXOS", reply_markup=outros_fixos_keyboard())
        return OUTROS_FIXOS
        
    custom_cats = db.get_custom_categories(user_id, 'fixo')
    if text in custom_cats:
        context.user_data['categoria'] = text
        await update.message.reply_text(f"🏠 {text}\n💰 Qual o valor deste gasto?", reply_markup=ReplyKeyboardRemove())
        return VALOR_GASTO
    
    await update.message.reply_text("❌ Selecione uma categoria válida:", reply_markup=minhas_categorias_fixas_keyboard(user_id))
    return MINHAS_CATEGORIAS_FIXAS

async def nova_categoria_flexivel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nova_categoria = update.message.text.strip()
    user_id = context.user_data['user_id']
    
    if not nova_categoria:
        await update.message.reply_text("❌ Nome inválido.")
        return NOVA_CATEGORIA_FLEXIVEL
    
    success = db.add_custom_category(user_id, 'flexivel', nova_categoria)
    if not success:
        await update.message.reply_text("❌ Erro ao criar categoria.")
        return NOVA_CATEGORIA_FLEXIVEL
    
    context.user_data['categoria'] = nova_categoria
    await update.message.reply_text(
        f"✅ NOVA CATEGORIA CRIADA: {nova_categoria.upper()}\n\n💰 Qual o valor deste gasto?",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def nova_categoria_fixa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nova_categoria = update.message.text.strip()
    user_id = context.user_data['user_id']
    
    if not nova_categoria:
        await update.message.reply_text("❌ Nome inválido.")
        return NOVA_CATEGORIA_FIXA
    
    success = db.add_custom_category(user_id, 'fixo', nova_categoria)
    if not success:
        await update.message.reply_text("❌ Erro ao criar categoria.")
        return NOVA_CATEGORIA_FIXA
    
    context.user_data['categoria'] = nova_categoria
    await update.message.reply_text(
        f"✅ NOVA CATEGORIA CRIADA: {nova_categoria.upper()}\n\n💰 Qual o valor deste gasto?",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def nova_categoria_outros_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await nova_categoria_flexivel_handler(update, context)

async def nova_categoria_outros_fixos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await nova_categoria_fixa_handler(update, context)

async def valor_gasto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return VALOR_GASTO
        
        context.user_data['valor_gasto'] = amount
        await update.message.reply_text(
            "📅 SELECIONE A DATA\n\nEscolha a data do gasto:",
            reply_markup=Calendar.create_calendar()
        )
        return DATA_GASTO
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 150,00")
        return VALOR_GASTO

async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    
    if text == 'hoje':
        date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    else:
        date_str = parse_date_input(text)
        if not date_str or not validate_date(date_str):
            await update.message.reply_text(
                "❌ Formato de data inválido!\n"
                "Formatos aceitos: DD/MM/AAAA ou DDMMAAAA\n"
                "Ex.: 15/03/2024 ou 15032024\n"
                "Ou use 'hoje'."
            )
            return DATA_GASTO
    
    return await process_date_selection(update, context, date_str)
    
async def handle_month_year_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada manual de mês/ano para extrato"""
    logger.info(f"handle_month_year_input chamado com texto: {update.message.text}")
    
    text = update.message.text.strip()
    
    # Remover espaços e caracteres não numéricos, exceto barra
    clean_text = ''.join(c for c in text if c.isdigit() or c == '/')
    
    try:
        # Tentar parsear como MM/AAAA
        if '/' in clean_text:
            parts = clean_text.split('/')
            if len(parts) == 2:
                month_str, year_str = parts
                if len(month_str) == 2 and len(year_str) == 4:
                    month = int(month_str)
                    year = int(year_str)
                else:
                    raise ValueError("Formato inválido")
            else:
                raise ValueError("Formato inválido")
        
        # Tentar parsear como MMAAAA (6 dígitos)
        elif len(clean_text) == 6:
            month = int(clean_text[0:2])
            year = int(clean_text[2:6])
        
        else:
            raise ValueError("Formato inválido")
        
        # Validar mês e ano
        if not (1 <= month <= 12):
            await update.message.reply_text(
                "❌ **Mês inválido!**\n\n"
                "O mês deve estar entre 01 e 12.\n\n"
                "💡 **Exemplos válidos:**\n"
                "• Março → 03/2024 ou 032024\n"
                "• Dezembro → 12/2023 ou 122023\n\n"
                "Digite novamente:"
            )
            return EXTRATO_MES
        
        if not (2020 <= year <= 2100):
            await update.message.reply_text(
                "❌ **Ano inválido!**\n\n"
                "O ano deve estar entre 2020 e 2100.\n\n"
                "💡 **Exemplos válidos:**\n"
                "• 2024 → 03/2024 ou 032024\n"
                "• 2023 → 12/2023 ou 122023\n\n"
                "Digite novamente:"
            )
            return EXTRATO_MES
        
        logger.info(f"Processando extrato para {month}/{year}")
        # Mostrar extrato do mês selecionado - passar o update corretamente
        await MonthYearCalendar.show_month_extrato(update, context, year, month)
        return ConversationHandler.END  # Terminar a conversação após mostrar extrato
        
    except (ValueError, IndexError) as e:
        logger.error(f"Erro ao processar entrada manual: {e}")
        await update.message.reply_text(
            "❌ **Formato inválido!**\n\n"
            "📋 **Use um destes formatos:**\n"
            "• **MM/AAAA** (ex: 03/2024)\n"
            "• **MMAAAA** (ex: 032024)\n\n"
            "💡 **Exemplos:**\n"
            "• Março de 2024 → 03/2024 ou 032024\n"
            "• Dezembro de 2023 → 12/2023 ou 122023\n\n"
            "Digite o mês e ano novamente:"
        )
        return EXTRATO_MES

async def process_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
    user_id = context.user_data['user_id']
    
    required_keys = ['tipo_gasto', 'categoria', 'valor_gasto']
    if any(k not in context.user_data for k in required_keys):
        await update.message.reply_text("❌ Dados incompletos. Comece novamente.", reply_markup=gastos_keyboard())
        return ConversationHandler.END

    tipo_gasto = context.user_data['tipo_gasto']
    categoria = context.user_data['categoria']
    valor = context.user_data['valor_gasto']
    descricao = f"{categoria} - {tipo_gasto}"

    success = db.add_transaction(user_id, tipo_gasto, categoria, categoria, valor, descricao, date_str)

    if success:
        await update.message.reply_text(
            f"🎉 GASTO REGISTRADO!\n\n"
            f"📋 Detalhes:\n"
            f"• 🏷️ Tipo: {tipo_gasto.upper()}\n"
            f"• 📂 Categoria: {categoria}\n"
            f"• 💰 Valor: R$ {valor:,.2f}\n"
            f"• 📅 Data: {date_str}\n\n"
            f"❓ Continuar adicionando gastos?",
            reply_markup=sim_nao_keyboard()
        )
        return CONTINUAR_GASTOS
    else:
        await update.message.reply_text("❌ Erro ao registrar gasto.", reply_markup=gastos_keyboard())
        return ConversationHandler.END

def parse_date_input(date_str):
    """Converte entrada de data para formato DD/MM/AAAA"""
    try:
        # Remove qualquer caractere não numérico
        clean_str = ''.join(c for c in date_str if c.isdigit())
        
        if len(clean_str) == 8:
            # Formato DDMMAAAA
            day = clean_str[0:2]
            month = clean_str[2:4]
            year = clean_str[4:8]
            return f"{day}/{month}/{year}"
        elif len(clean_str) == 6:
            # Formato DDMMAA (assume século 20 para anos < 50, 21 para anos >= 50)
            day = clean_str[0:2]
            month = clean_str[2:4]
            year_part = clean_str[4:6]
            year = f"20{year_part}" if int(year_part) >= 50 else f"19{year_part}"
            return f"{day}/{month}/{year}"
        else:
            return None
    except Exception:
        return None

def validate_date(date_str):
    """Valida se a data está no formato correto e é válida"""
    try:
        day, month, year = map(int, date_str.split('/'))
        
        # Verifica se os valores são razoáveis
        if not (1 <= month <= 12):
            return False
        if not (1 <= day <= 31):
            return False
        if not (1900 <= year <= 2100):
            return False
            
        # Verificação básica de dias por mês
        if month in [4, 6, 9, 11] and day > 30:
            return False
        elif month == 2:
            # Verificação simples para fevereiro (não considera anos bissextos)
            if day > 29:
                return False
                
        return True
    except Exception:
        return False
        
async def continuar_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'SIM' in text:
        await update.message.reply_text(
            "💰 ADICIONAR NOVO GASTO\n\nQual o tipo de gasto?",
            reply_markup=tipo_gasto_keyboard()
        )
        return TIPO_GASTO
        
    elif 'NÃO' in text or 'NAO' in text:
        user_id = context.user_data['user_id']
        nickname = db.get_user_nickname(user_id)
        expenses = db.get_monthly_expenses(user_id)
        
        total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
        total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
        total_geral = total_fixo + total_flexivel
        
        user_data = db.get_user_data(user_id)
        salario = user_data['salario_liquido'] if user_data else 0
        saldo = salario - total_geral
        
        response = f"📊 **RESUMO DOS SEUS GASTOS - {nickname}**\n\n"
        
        if total_fixo:
            response += "🏠 **GASTOS FIXOS:**\n"
            for cat, subs in expenses['fixo'].items():
                for sub, val in subs.items():
                    response += f"• {cat}: R$ {val:,.2f}\n"
            response += f"📌 **Total Fixo:** R$ {total_fixo:,.2f}\n\n"
            
        if total_flexivel:
            response += "🛍️ **GASTOS FLEXÍVEIS:**\n"
            for cat, subs in expenses['flexivel'].items():
                for sub, val in subs.items():
                    response += f"• {cat}: R$ {val:,.2f}\n"
            response += f"📌 **Total Flexível:** R$ {total_flexivel:,.2f}\n\n"
            
        response += f"🎯 **TOTAL GASTO:** R$ {total_geral:,.2f}\n\n"
        response += f"💵 **Seu salário:** R$ {salario:,.2f}\n"
        response += f"• ⚖️ **Saldo disponível:** R$ {saldo:,.2f}\n\n"
        
        if saldo >= 0:
            response += "✅ Situação: Positiva - Você está gastando menos do que ganha!\n\n"
        else:
            response += "⚠️ Situação: Atenção - Você está gastando mais do que ganha.\n\n"
            
        response += "💡 Com esses valores podemos analisar a sua saúde financeira.\n\nO que deseja fazer agora?"
        
        await update.message.reply_text(response, reply_markup=saude_financeira_keyboard())
        return RESUMO_GASTOS
        
    else:
        await update.message.reply_text("❌ Por favor, selecione SIM ou NÃO:", reply_markup=sim_nao_keyboard())
        return CONTINUAR_GASTOS

# ========== SUAS CATEGORIAS ==========
async def suas_categorias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 SUAS CATEGORIAS\n\nGerencie suas categorias personalizadas:",
        reply_markup=suas_categorias_keyboard()
    )
    return SUAS_CATEGORIAS

async def suas_categorias_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Fixas' in text:
        custom_cats = db.get_custom_categories(user_id, 'fixo')
        if not custom_cats:
            await update.message.reply_text(
                "📝 Você ainda não tem categorias fixas personalizadas.\n"
                "Crie em: Gastos Fixos → Outros... → Adicionar novo",
                reply_markup=suas_categorias_keyboard()
            )
            return SUAS_CATEGORIAS
        await update.message.reply_text(
            "🏠 SUAS CATEGORIAS FIXAS\n\nSuas categorias personalizadas:",
            reply_markup=categorias_fixas_keyboard_with_delete(user_id)
        )
        return CATEGORIAS_FIXAS
        
    if 'Flexíveis' in text:
        custom_cats = db.get_custom_categories(user_id, 'flexivel')
        if not custom_cats:
            await update.message.reply_text(
                "📝 Você ainda não tem categorias flexíveis personalizadas.\n"
                "Crie em: Gastos Flexíveis → Outros... → Adicionar novo",
                reply_markup=suas_categorias_keyboard()
            )
            return SUAS_CATEGORIAS
        await update.message.reply_text(
            "🛍️ SUAS CATEGORIAS FLEXÍVEIS\n\nSuas categorias personalizadas:",
            reply_markup=categorias_flexiveis_keyboard_with_delete(user_id)
        )
        return CATEGORIAS_FLEXIVEIS
        
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=suas_categorias_keyboard())
    return SUAS_CATEGORIAS

async def categorias_fixas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Voltar para Suas Categorias' in text:
        await update.message.reply_text("📂 SUAS CATEGORIAS", reply_markup=suas_categorias_keyboard())
        return SUAS_CATEGORIAS
        
    if 'Excluir Categoria' in text:
        custom_cats = db.get_custom_categories(user_id, 'fixo')
        if not custom_cats:
            await update.message.reply_text("❌ Nenhuma categoria para excluir.", reply_markup=categorias_fixas_keyboard_with_delete(user_id))
            return CATEGORIAS_FIXAS
            
        context.user_data['excluindo_tipo'] = 'fixo'
        await update.message.reply_text(
            "🗑️ EXCLUIR CATEGORIA FIXA\n\nSelecione a categoria:",
            reply_markup=categorias_excluir_keyboard(user_id, 'fixo')
        )
        return SELECIONAR_CATEGORIA_EXCLUIR
    
    # Permitir que o usuário selecione uma categoria para ver detalhes
    if text.startswith('📂 '):
        categoria = text[3:]
        custom_cats = db.get_custom_categories(user_id, 'fixo')
        if categoria in custom_cats:
            # Mostrar estatísticas da categoria
            gastos_categoria = db.get_category_expenses(user_id, 'fixo', categoria)
            total_gasto = sum(gasto['valor'] for gasto in gastos_categoria) if gastos_categoria else 0
            
            await update.message.reply_text(
                f"📊 **ESTATÍSTICAS DA CATEGORIA**\n\n"
                f"🏠 **Categoria:** {categoria}\n"
                f"💰 **Total Gasto:** R$ {total_gasto:,.2f}\n"
                f"📅 **Número de Gastos:** {len(gastos_categoria)}\n\n"
                f"Use '🗑️ Excluir Categoria' para remover esta categoria.",
                reply_markup=categorias_fixas_keyboard_with_delete(user_id)
            )
            return CATEGORIAS_FIXAS
        
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=categorias_fixas_keyboard_with_delete(user_id))
    return CATEGORIAS_FIXAS

async def categorias_flexiveis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Voltar para Suas Categorias' in text:
        await update.message.reply_text("📂 SUAS CATEGORIAS", reply_markup=suas_categorias_keyboard())
        return SUAS_CATEGORIAS
        
    if 'Excluir Categoria' in text:
        custom_cats = db.get_custom_categories(user_id, 'flexivel')
        if not custom_cats:
            await update.message.reply_text("❌ Nenhuma categoria para excluir.", reply_markup=categorias_flexiveis_keyboard_with_delete(user_id))
            return CATEGORIAS_FLEXIVEIS
            
        context.user_data['excluindo_tipo'] = 'flexivel'
        await update.message.reply_text(
            "🗑️ EXCLUIR CATEGORIA FLEXÍVEL\n\nSelecione a categoria:",
            reply_markup=categorias_excluir_keyboard(user_id, 'flexivel')
        )
        return SELECIONAR_CATEGORIA_EXCLUIR
    
    # Permitir que o usuário selecione uma categoria para ver detalhes
    if text.startswith('📂 '):
        categoria = text[3:]
        custom_cats = db.get_custom_categories(user_id, 'flexivel')
        if categoria in custom_cats:
            # Mostrar estatísticas da categoria
            gastos_categoria = db.get_category_expenses(user_id, 'flexivel', categoria)
            total_gasto = sum(gasto['valor'] for gasto in gastos_categoria) if gastos_categoria else 0
            
            await update.message.reply_text(
                f"📊 **ESTATÍSTICAS DA CATEGORIA**\n\n"
                f"🛍️ **Categoria:** {categoria}\n"
                f"💰 **Total Gasto:** R$ {total_gasto:,.2f}\n"
                f"📅 **Número de Gastos:** {len(gastos_categoria)}\n\n"
                f"Use '🗑️ Excluir Categoria' para remover esta categoria.",
                reply_markup=categorias_flexiveis_keyboard_with_delete(user_id)
            )
            return CATEGORIAS_FLEXIVEIS
        
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=categorias_flexiveis_keyboard_with_delete(user_id))
    return CATEGORIAS_FLEXIVEIS

async def selecionar_categoria_excluir_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'excluindo_tipo' not in context.user_data:
        await update.message.reply_text("❌ Erro: Tipo não definido.", reply_markup=suas_categorias_keyboard())
        return SUAS_CATEGORIAS
        
    tipo = context.user_data['excluindo_tipo']
    tipo_texto = "Fixas" if tipo == 'fixo' else "Flexíveis"
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if f'Voltar para Categorias {tipo_texto}' in text:
        if tipo == 'fixo':
            await update.message.reply_text("🏠 SUAS CATEGORIAS FIXAS", reply_markup=categorias_fixas_keyboard_with_delete(user_id))
            return CATEGORIAS_FIXAS
        else:
            await update.message.reply_text("🛍️ SUAS CATEGORIAS FLEXÍVEIS", reply_markup=categorias_flexiveis_keyboard_with_delete(user_id))
            return CATEGORIAS_FLEXIVEIS
            
    if text.startswith('🗑️ '):
        categoria = text[3:]
        context.user_data['categoria_excluir'] = categoria
        
        # Mostrar estatísticas antes de excluir
        gastos_categoria = db.get_category_expenses(user_id, tipo, categoria)
        total_gasto = sum(gasto['valor'] for gasto in gastos_categoria) if gastos_categoria else 0
        num_gastos = len(gastos_categoria)
        
        await update.message.reply_text(
            f"🚨 CONFIRMAR EXCLUSÃO\n\n"
            f"🗑️ **Categoria:** {categoria}\n"
            f"📊 **Tipo:** {tipo_texto}\n"
            f"💰 **Total Gasto:** R$ {total_gasto:,.2f}\n"
            f"📅 **Número de Gastos:** {num_gastos}\n\n"
            f"⚠️ **ATENÇÃO:** A exclusão NÃO afeta os {num_gastos} gastos já registrados.\n"
            f"Eles permanecerão no seu histórico, mas sem esta categoria.\n\n"
            f"Tem certeza que deseja EXCLUIR esta categoria?",
            reply_markup=confirmar_exclusao_categoria_keyboard()
        )
        return CONFIRMAR_EXCLUSAO_CATEGORIA
        
    await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=categorias_excluir_keyboard(user_id, tipo))
    return SELECIONAR_CATEGORIA_EXCLUIR

async def confirmar_exclusao_categoria_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'SIM' in text or 'SIM, Excluir' in text:
        categoria = context.user_data.pop('categoria_excluir', None)
        tipo = context.user_data.pop('excluindo_tipo', None)
        
        if not categoria or not tipo:
            await update.message.reply_text("❌ Dados não encontrados.", reply_markup=suas_categorias_keyboard())
            return SUAS_CATEGORIAS
            
        success = db.delete_custom_category(user_id, tipo, categoria)
        if success:
            await update.message.reply_text(
                f"✅ Categoria '{categoria}' excluída com sucesso!\n\n"
                f"📝 Os gastos registrados com esta categoria permanecem no seu histórico.",
                reply_markup=suas_categorias_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao excluir categoria.\n"
                "Tente novamente ou verifique se a categoria existe.",
                reply_markup=suas_categorias_keyboard()
            )
        return SUAS_CATEGORIAS
        
    if 'NÃO' in text or 'NAO' in text or 'NÃO, Cancelar' in text:
        context.user_data.pop('categoria_excluir', None)
        context.user_data.pop('excluindo_tipo', None)
        await update.message.reply_text(
            "✅ Exclusão cancelada.\n"
            "Sua categoria foi mantida.",
            reply_markup=suas_categorias_keyboard()
        )
        return SUAS_CATEGORIAS
        
    await update.message.reply_text("❌ Confirme SIM ou NÃO:", reply_markup=confirmar_exclusao_categoria_keyboard())
    return CONFIRMAR_EXCLUSAO_CATEGORIA

# ========== CONFIRMAÇÕES ==========
async def confirm_gasto_outros_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    
    if 'SIM' in text:
        categoria = context.user_data.get('categoria')
        if not categoria:
            await update.message.reply_text("❌ Categoria não encontrada.")
            return ConversationHandler.END
        await update.message.reply_text(f"🛍️ {categoria}\n💰 Qual o valor?", reply_markup=ReplyKeyboardRemove())
        return VALOR_GASTO
        
    if 'NÃO' in text or 'NAO' in text:
        await update.message.reply_text("✅ Tudo bem. Voltando.", reply_markup=gastos_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text("❌ Responda SIM ou NÃO.")
    return CONFIRM_GASTO_OUTROS

async def confirm_gasto_outros_fixos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    
    if 'SIM' in text:
        categoria = context.user_data.get('categoria')
        if not categoria:
            await update.message.reply_text("❌ Categoria não encontrada.")
            return ConversationHandler.END
        await update.message.reply_text(f"🏠 {categoria}\n💰 Qual o valor?", reply_markup=ReplyKeyboardRemove())
        return VALOR_GASTO
        
    if 'NÃO' in text or 'NAO' in text:
        await update.message.reply_text("✅ Tudo bem. Voltando.", reply_markup=gastos_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text("❌ Responda SIM ou NÃO.")
    return CONFIRM_GASTO_OUTROS_FIXOS

# ========== SALÁRIOS ==========
AGUARDANDO_FONTE_SALARIO, AGUARDANDO_VALOR_SALARIO = range(2)

async def salarios_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu de gerenciamento de salários"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💵 Adicionar Salário", callback_data="adicionar_salario")],
        [InlineKeyboardButton("✏️ Alterar Salários", callback_data="alterar_salarios")],
        [InlineKeyboardButton("📊 Consultar Salários", callback_data="consultar_salarios")],
        [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="voltar_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="💰 *Menu de Salários*\n\nEscolha uma opção:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def adicionar_salario_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de adicionar salário"""
    query = update.callback_query
    await query.answer()
    
    # Verificar se já tem salário principal
    user_id = update.effective_user.id
    salarios = db.get_salaries(user_id)  # ← corrigido
    tem_principal = any(salario['principal'] for salario in salarios)
    
    context.user_data['adicionando_salario'] = True
    context.user_data['eh_principal'] = not tem_principal
    
    mensagem = "💰 *Adicionar Salário*\n\n"
    if not tem_principal:
        mensagem += "📝 Este será seu *salário principal*.\n\n"
    
    mensagem += "Por favor, digite a *fonte/origem* deste salário:\n\n"
    mensagem += "Exemplos:\n• Salário CLT\n• Freelance\n• Investimentos\n• Aluguel"
    
    await query.edit_message_text(
        text=mensagem,
        parse_mode='Markdown'
    )
    
    return AGUARDANDO_FONTE_SALARIO

async def receber_fonte_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a fonte do salário e pede o valor"""
    fonte = update.message.text.strip()
    
    if len(fonte) < 2:
        await update.message.reply_text("❌ Por favor, digite uma fonte válida (mínimo 2 caracteres).")
        return AGUARDANDO_FONTE_SALARIO
    
    context.user_data['fonte_salario'] = fonte
    
    mensagem = f"✅ Fonte: *{fonte}*\n\n"
    mensagem += "Agora digite o *valor* do salário:\n\n"
    mensagem += "Exemplos:\n• 2500.00\n• 1.500,00\n• R$ 3000"
    
    await update.message.reply_text(
        text=mensagem,
        parse_mode='Markdown'
    )
    
    return AGUARDANDO_VALOR_SALARIO

async def receber_valor_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o valor do salário e salva no banco"""
    try:
        valor_texto = update.message.text.strip()
        
        # Limpar e converter o valor
        valor_texto = valor_texto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        valor = float(valor_texto)
        
        if valor <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return AGUARDANDO_VALOR_SALARIO
        
        user_id = update.effective_user.id
        fonte = context.user_data['fonte_salario']
        eh_principal = context.user_data['eh_principal']
        
        # Salvar no banco
        db.add_salary(user_id, fonte, valor, eh_principal)  # ← corrigido
        
        # Limpar dados temporários
        context.user_data.pop('fonte_salario', None)
        context.user_data.pop('eh_principal', None)
        context.user_data.pop('adicionando_salario', None)
        
        # Mostrar confirmação
        mensagem = f"✅ *Salário adicionado com sucesso!*\n\n"
        mensagem += f"💼 *Fonte:* {fonte}\n"
        mensagem += f"💰 *Valor:* R$ {valor:,.2f}\n"
        
        if eh_principal:
            mensagem += f"⭐ *Salário Principal*\n\n"
        
        await update.message.reply_text(
            text=mensagem,
            parse_mode='Markdown'
        )
        
        # Mostrar extrato atualizado
        await mostrar_extrato_salarios(update, context, user_id)
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Valor inválido. Por favor, digite um valor numérico.\n\n"
            "Exemplos: 2500.00, 1.500,00, R$ 3000"
        )
        return AGUARDANDO_VALOR_SALARIO

async def mostrar_extrato_salarios(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
    """Mostra o extrato completo de salários"""
    if not user_id:
        user_id = update.effective_user.id
    
    salarios = db.get_salaries(user_id)  # ← corrigido
    
    if not salarios:
        mensagem = "📊 *Extrato de Salários*\n\n"
        mensagem += "❌ Nenhum salário cadastrado.\n\n"
        mensagem += "Use a opção *💵 Adicionar Salário* para cadastrar seu primeiro salário."
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text=mensagem, parse_mode='Markdown')
        else:
            await update.message.reply_text(text=mensagem, parse_mode='Markdown')
        return
    
    mensagem = "📊 *Extrato de Salários*\n\n"
    total = 0
    
    for salario in salarios:
        emoji = "⭐" if salario['principal'] else "📌"
        mensagem += f"{emoji} *{salario['fonte']}*: R$ {salario['valor']:,.2f}\n"
        total += salario['valor']
    
    mensagem += f"\n💎 *Total:* R$ {total:,.2f}"
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text=mensagem, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=mensagem, parse_mode='Markdown')

async def consultar_salarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para consultar salários"""
    query = update.callback_query
    await query.answer()
    
    await mostrar_extrato_salarios(update, context)

async def alterar_salarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu para alterar salários existentes"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    salaries = db.get_salaries(user_id)
    
    if not salarios:
        await query.edit_message_text(
            text="❌ Nenhum salário cadastrado para alterar.",
            parse_mode='Markdown'
        )
        return
    
    keyboard = []
    for salario in salarios:
        emoji = "⭐" if salario['principal'] else "📌"
        texto_botao = f"{emoji} {salario['fonte']} - R$ {salario['valor']:,.2f}"
        callback_data = f"editar_salario_{salario['id']}"
        keyboard.append([InlineKeyboardButton(texto_botao, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="salarios_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="✏️ *Alterar Salários*\n\nSelecione o salário que deseja editar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def editar_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu de edição para um salário específico"""
    query = update.callback_query
    await query.answer()
    
    salario_id = int(query.data.replace('editar_salario_', ''))
    user_id = update.effective_user.id
    
    # Buscar informações do salário
    salaries = db.get_salaries(user_id)
    salario = next((s for s in salarios if s['id'] == salario_id), None)
    
    if not salario:
        await query.edit_message_text("❌ Salário não encontrado.")
        return
    
    context.user_data['editando_salario_id'] = salario_id
    
    mensagem = f"✏️ *Editando Salário*\n\n"
    mensagem += f"💼 *Fonte:* {salario['fonte']}\n"
    mensagem += f"💰 *Valor:* R$ {salario['valor']:,.2f}\n"
    
    if salario['principal']:
        mensagem += "⭐ *Salário Principal*\n\n"
        mensagem += "O salário principal não pode ser excluído."
    
    keyboard = [
        [InlineKeyboardButton("✏️ Alterar Fonte", callback_data=f"alterar_fonte_{salario_id}")],
        [InlineKeyboardButton("💵 Alterar Valor", callback_data=f"alterar_valor_{salario_id}")],
    ]
    
    if not salario['principal']:
        keyboard.append([InlineKeyboardButton("⭐ Tornar Principal", callback_data=f"tornar_principal_{salario_id}")])
        keyboard.append([InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_salario_{salario_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="alterar_salarios")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=mensagem,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def excluir_salario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para excluir salário"""
    query = update.callback_query
    await query.answer()
    
    salario_id = int(query.data.replace('excluir_salario_', ''))
    
    if db.delete_salary(salario_id):  # ← corrigido
        await query.edit_message_text(
            text="✅ Salário excluído com sucesso!",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            text="❌ Não é possível excluir o salário principal.",
            parse_mode='Markdown'
        )

async def tornar_principal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para tornar um salário o principal"""
    query = update.callback_query
    await query.answer()
    
    salario_id = int(query.data.replace('tornar_principal_', ''))
    user_id = update.effective_user.id
    
    db.set_principal_salary(salario_id, user_id)  # ← corrigido (antes podia usar tornar_principal)
    
    await query.edit_message_text(
        text="✅ Salário definido como principal!",
        parse_mode='Markdown'
    )

# Adicione também os handlers para alterar fonte e valor (serão similares aos de adicionar)

async def cancelar_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela o processo de adição/edição de salário"""
    context.user_data.clear()
    
    if update.message:
        await update.message.reply_text(
            "❌ Operação cancelada.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

# ========== EXTRATO DETALHADO ==========
async def extrato_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Meu Extrato - Agora com seleção de mês"""
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar.")
        return ConversationHandler.END
        
    await update.message.reply_text(
        "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver o extrato detalhado:",
        reply_markup=MonthYearCalendar.create_month_year_calendar()
    )
    return EXTRATO_MES

# ========== RESUMO E ANÁLISE ==========
async def resumo_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o resumo financeiro (mantido para compatibilidade)"""
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar.")
        return ConversationHandler.END
        
    user_data = db.get_user_data(user_id)
    expenses = db.get_monthly_expenses(user_id)
    
    total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
    total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
    total_geral = total_fixo + total_flexivel
    
    salario = user_data['salario_liquido'] if user_data else 0
    saldo = salario - total_geral
    percentual = (total_geral / salario * 100) if salario > 0 else 0
    
    response = f"📊 **RESUMO FINANCEIRO - {user_data['nickname']}**\n\n"
    response += f"🏠 **Gastos Fixos:** R$ {total_fixo:,.2f}\n"
    response += f"🛍️ **Gastos Flexíveis:** R$ {total_flexivel:,.2f}\n"
    response += f"💰 **Total Gasto:** R$ {total_geral:,.2f}\n\n"
    response += f"💵 **Salário:** R$ {salario:,.2f}\n"
    response += f"⚖️ **Saldo:** R$ {saldo:,.2f}\n"
    response += f"📈 **Comprometido:** {percentual:.1f}%\n\n"
    
    if percentual <= 60:
        response += "✅ **Situação:** Saudável\n"
        response += "💡 **Dica:** Continue mantendo esse controle!"
    elif percentual <= 85:
        response += "⚠️ **Situação:** Atenção\n"
        response += "💡 **Dica:** Revise seus gastos flexíveis."
    else:
        response += "🚨 **Situação:** Crítico\n"
        response += "💡 **Dica:** Priorize gastos essenciais e reveja seu orçamento."
        
    await update.message.reply_text(response, reply_markup=main_keyboard())
    return ConversationHandler.END

async def saude_financeira_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 SAÚDE FINANCEIRA\n\nAnalise sua situação e receba recomendações:",
        reply_markup=saude_financeira_keyboard()
    )
    return ConversationHandler.END

async def analise_detalhada_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        await update.message.reply_text("🤖 Gerando análise detalhada...")
        analise = await coach.finance_coach.get_detailed_analysis(user_id)
        await update.message.reply_text(
            f"📈 ANÁLISE DETALHADA\n\n{analise}",
            reply_markup=analise_detalhada_inline_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await update.message.reply_text("❌ Erro na análise.", reply_markup=saude_financeira_keyboard())
    return ConversationHandler.END

async def ver_metricas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await analise_detalhada_handler(update, context)

async def recomendacoes_ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        await update.message.reply_text("🤖 Gerando recomendações...")
        recomendacoes = await coach.finance_coach.get_personalized_recommendations(user_id)
        await update.message.reply_text(
            f"🧠 RECOMENDAÇÕES IA\n\n{recomendacoes}",
            reply_markup=saude_financeira_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro nas recomendações: {e}")
        await update.message.reply_text("❌ Erro nas recomendações.", reply_markup=saude_financeira_keyboard())
    return ConversationHandler.END

async def analise_detalhada_ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await analise_detalhada_handler(update, context)

# ========== CONFIGURAÇÕES ==========
async def edit_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar.")
        return ConversationHandler.END
        
    user_data = db.get_user_data(user_id)
    await update.message.reply_text(
        f"✏️ EDITAR PERFIL\n\n"
        f"📝 Nome atual: {user_data['nickname']}\n"
        f"💰 Salário atual: R$ {user_data['salario_liquido']:,.2f}\n\n"
        f"Digite seu novo nome:",
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_NAME

async def edit_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("❌ Nome inválido. Digite novamente:")
        return EDIT_NAME
        
    user_id = update.effective_user.id
    db.update_user_nickname(user_id, new_name)
    await update.message.reply_text(
        f"✅ Nome alterado para: {new_name}",
        reply_markup=config_keyboard()
    )
    return ConversationHandler.END
    

async def edit_salary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar.")
        return ConversationHandler.END
        
    user_data = db.get_user_data(user_id)
    await update.message.reply_text(
        f"💰 ALTERAR SALÁRIO\n\n"
        f"Salário atual: R$ {user_data['salario_liquido']:,.2f}\n\n"
        f"Digite o novo valor do seu salário líquido:",
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_SALARY


async def edit_salary_process_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        new_salary = float(salary_text)
        
        if new_salary <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return EDIT_SALARY
            
        user_id = update.effective_user.id
        db.update_user_salary(user_id, new_salary)
        await update.message.reply_text(
            f"✅ Salário alterado para: R$ {new_salary:,.2f}",
            reply_markup=config_keyboard()
        )
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 1500,00")
        return EDIT_SALARY

async def reset_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 REDEFINIR DADOS\n\n"
        "⚠️ ATENÇÃO: Esta ação irá:\n"
        "• ❌ Excluir TODOS os seus gastos\n"
        "• ❌ Excluir TODOS os seus objetivos\n"
        "• ❌ Manter apenas seu perfil básico\n\n"
        "Tem certeza que deseja continuar?",
        reply_markup=sim_nao_keyboard()
    )
    return CONFIRM_RESET

async def confirm_reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'SIM' in text:
        user_id = update.effective_user.id
        db.reset_user_data(user_id)
        await update.message.reply_text(
            "✅ DADOS REDEFINIDOS!\n\n"
            "Todos os seus gastos e objetivos foram excluídos.\n"
            "Seu perfil básico foi mantido.",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
        
    elif 'NÃO' in text or 'NAO' in text:
        await update.message.reply_text(
            "✅ Operação cancelada.\n"
            "Seus dados foram preservados.",
            reply_markup=config_keyboard()
        )
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Confirme SIM ou NÃO:", reply_markup=sim_nao_keyboard())
        return CONFIRM_RESET

# ========== OBJETIVOS ==========
async def objetivos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 OBJETIVOS FINANCEIROS\n\nGerencie suas metas financeiras:",
        reply_markup=objetivos_keyboard()
    )
    return ConversationHandler.END

async def add_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 ADICIONAR OBJETIVO\n\n"
        "Escolha o tipo de objetivo:",
        reply_markup=ReplyKeyboardMarkup([
            ['💰 Economia Mensal', '🎯 Meta Específica'],
            ['🏠 Voltar ao Menu']
        ], resize_keyboard=True)
    )
    return GOAL_TYPE

async def goal_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    if 'Economia Mensal' in text:
        context.user_data['goal_type'] = 'economia_mensal'
    elif 'Meta Específica' in text:
        context.user_data['goal_type'] = 'meta_especifica'
    else:
        await update.message.reply_text("❌ Tipo inválido. Selecione uma opção:", reply_markup=update.message.reply_markup)
        return GOAL_TYPE
    
    await update.message.reply_text(
        "📝 DESCRIÇÃO DO OBJETIVO\n\n"
        "Descreva seu objetivo:\n"
        "(Ex: Viagem para a praia, Novo celular, Reserva de emergência)",
        reply_markup=ReplyKeyboardRemove()
    )
    return GOAL_DESCRIPTION

async def goal_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()
    if not description:
        await update.message.reply_text("❌ Descrição inválida. Digite novamente:")
        return GOAL_DESCRIPTION
        
    context.user_data['goal_description'] = description
    
    if context.user_data['goal_type'] == 'economia_mensal':
        await update.message.reply_text(
            "💰 VALOR DA ECONOMIA\n\n"
            "Qual valor você quer economizar por mês?\n"
            "(Ex: 300,00)",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "🎯 VALOR DA META\n\n"
            "Qual o valor total da sua meta?\n"
            "(Ex: 2000,00)",
            reply_markup=ReplyKeyboardRemove()
        )
    return GOAL_TARGET

async def goal_target_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_text = update.message.text.replace(',', '.').strip()
        target = float(target_text)
        
        if target <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return GOAL_TARGET
            
        context.user_data['goal_target'] = target
        
        if context.user_data['goal_type'] == 'economia_mensal':
            # Para economia mensal, não precisa de prazo
            user_id = update.effective_user.id
            success = db.add_goal(
                user_id,
                context.user_data['goal_description'],
                'economia_mensal',
                target,
                None  # Sem prazo para economia mensal
            )
            
            if success:
                await update.message.reply_text(
                    f"✅ OBJETIVO CRIADO!\n\n"
                    f"📝 {context.user_data['goal_description']}\n"
                    f"💰 Economia mensal: R$ {target:,.2f}\n"
                    f"📊 Tipo: Economia Mensal",
                    reply_markup=objetivos_keyboard()
                )
            else:
                await update.message.reply_text("❌ Erro ao criar objetivo.", reply_markup=objetivos_keyboard())
            
            return ConversationHandler.END
        else:
            # Para meta específica, pedir prazo
            await update.message.reply_text(
                "📅 PRAZO DA META\n\n"
                "Escolha a data limite para atingir sua meta:",
                reply_markup=Calendar.create_calendar()
            )
            return GOAL_DEADLINE_CALENDAR
            
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 300,00")
        return GOAL_TARGET

async def goal_deadline_manual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    
    if text == 'hoje':
        date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    else:
        date_str = parse_date_input(text)
        if not date_str or not validate_date(date_str):
            await update.message.reply_text(
                "❌ Formato de data inválido!\n"
                "Formatos aceitos: DD/MM/AAAA ou DDMMAAAA\n"
                "Ex.: 15/03/2024 ou 15032024\n"
                "Ou use 'hoje'."
            )
            return GOAL_DEADLINE
    
    return await process_goal_creation(update, context, date_str)

async def goal_deadline_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data.startswith("CAL_DAY_"):
            parts = query.data.split('_')
            year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
            date_str = f"{day:02d}/{month:02d}/{year}"
            
            await query.edit_message_text(f"✅ Data selecionada: {date_str}")
            return await process_goal_creation(update, context, date_str)
            
        else:
            # Outras ações do calendário
            await Calendar.handle_callback(update, context)
            return GOAL_DEADLINE_CALENDAR
            
    except Exception as e:
        logger.error(f"Erro no calendário de objetivos: {e}")
        await query.message.reply_text("❌ Erro ao selecionar data.", reply_markup=objetivos_keyboard())
        return ConversationHandler.END

async def process_goal_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, deadline: str):
    user_id = update.effective_user.id
    
    success = db.add_goal(
        user_id,
        context.user_data['goal_description'],
        'meta_especifica',
        context.user_data['goal_target'],
        deadline
    )
    
    if success:
        await update.message.reply_text(
            f"✅ OBJETIVO CRIADO!\n\n"
            f"📝 {context.user_data['goal_description']}\n"
            f"💰 Valor: R$ {context.user_data['goal_target']:,.2f}\n"
            f"📅 Prazo: {deadline}\n"
            f"📊 Tipo: Meta Específica",
            reply_markup=objetivos_keyboard()
        )
    else:
        await update.message.reply_text("❌ Erro ao criar objetivo.", reply_markup=objetivos_keyboard())
    
    return ConversationHandler.END

async def meus_objetivos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goals = db.get_user_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "🎯 MEUS OBJETIVOS\n\n"
            "Você ainda não tem objetivos cadastrados.\n"
            "Use '🎯 Adicionar Objetivo' para criar seu primeiro objetivo.",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    response = "🎯 MEUS OBJETIVOS\n\n"
    
    for i, goal in enumerate(goals, 1):
        progresso = goal['progresso'] or 0
        porcentagem = (progresso / goal['valor_meta']) * 100 if goal['valor_meta'] > 0 else 0
        
        if goal['tipo'] == 'economia_mensal':
            response += f"{i}. 💰 {goal['descricao']}\n"
            response += f"   📊 Economia mensal: R$ {goal['valor_meta']:,.2f}\n"
            response += f"   📈 Progresso: R$ {progresso:,.2f} ({porcentagem:.1f}%)\n"
        else:
            response += f"{i}. 🎯 {goal['descricao']}\n"
            response += f"   💰 Meta: R$ {goal['valor_meta']:,.2f}\n"
            response += f"   📈 Progresso: R$ {progresso:,.2f} ({porcentagem:.1f}%)\n"
            if goal['prazo']:
                response += f"   📅 Prazo: {goal['prazo']}\n"
        
        # Barra de progresso
        barras = int(porcentagem / 10)
        barra_progresso = "🟩" * barras + "⬜" * (10 - barras)
        response += f"   {barra_progresso} {porcentagem:.1f}%\n\n"
    
    await update.message.reply_text(response, reply_markup=objetivos_keyboard())
    return ConversationHandler.END

async def update_goal_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goals = db.get_user_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "📊 ATUALIZAR PROGRESSO\n\n"
            "Você ainda não tem objetivos cadastrados.",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    keyboard = []
    for goal in goals:
        progresso = goal['progresso'] or 0
        porcentagem = (progresso / goal['valor_meta']) * 100 if goal['valor_meta'] > 0 else 0
        
        button_text = f"{goal['descricao']} - {porcentagem:.1f}%"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"goal_{goal['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_update")])
    
    await update.message.reply_text(
        "📊 ATUALIZAR PROGRESSO\n\n"
        "Selecione o objetivo que deseja atualizar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_GOAL

async def handle_goal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_update":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if query.data.startswith("goal_"):
        goal_id = int(query.data.replace('goal_', ''))
        context.user_data['selected_goal_id'] = goal_id
        
        # Buscar informações do objetivo
        goals = db.get_user_goals(query.from_user.id)
        selected_goal = None
        
        for goal in goals:
            if goal['id'] == goal_id:
                selected_goal = goal
                break
        
        if selected_goal:
            progresso = selected_goal['progresso'] or 0
            porcentagem = (progresso / selected_goal['valor_meta']) * 100 if selected_goal['valor_meta'] > 0 else 0
            
            await query.edit_message_text(
                f"📊 ATUALIZAR PROGRESSO\n\n"
                f"🎯 {selected_goal['descricao']}\n"
                f"💰 Meta: R$ {selected_goal['valor_meta']:,.2f}\n"
                f"📈 Progresso atual: R$ {progresso:,.2f} ({porcentagem:.1f}%)\n\n"
                f"Digite o novo valor do progresso:\n"
                f"(Ex: 500,00)",
                reply_markup=ReplyKeyboardRemove()
            )
            return UPDATE_GOAL_PROGRESS
    
    await query.edit_message_text("❌ Erro ao selecionar objetivo.")
    return ConversationHandler.END

async def update_goal_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        progress_text = update.message.text.replace(',', '.').strip()
        new_progress = float(progress_text)
        
        if new_progress < 0:
            await update.message.reply_text("❌ O valor não pode ser negativo.")
            return UPDATE_GOAL_PROGRESS
        
        goal_id = context.user_data.get('selected_goal_id')
        success = db.update_goal_progress(goal_id, new_progress)
        
        if success:
            await update.message.reply_text(
                f"✅ PROGRESSO ATUALIZADO!\n\n"
                f"Novo valor: R$ {new_progress:,.2f}",
                reply_markup=objetivos_keyboard()
            )
        else:
            await update.message.reply_text("❌ Erro ao atualizar progresso.", reply_markup=objetivos_keyboard())
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 500,00")
        return UPDATE_GOAL_PROGRESS

async def delete_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goals = db.get_user_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "🗑️ EXCLUIR OBJETIVO\n\n"
            "Você ainda não tem objetivos cadastrados.",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    keyboard = []
    for goal in goals:
        progresso = goal['progresso'] or 0
        porcentagem = (progresso / goal['valor_meta']) * 100 if goal['valor_meta'] > 0 else 0
        
        button_text = f"{goal['descricao']} - {porcentagem:.1f}%"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_goal_{goal['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete")])
    
    await update.message.reply_text(
        "🗑️ EXCLUIR OBJETIVO\n\n"
        "Selecione o objetivo que deseja excluir:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_GOAL_DELETE

async def handle_goal_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_delete":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if query.data.startswith("delete_goal_"):
        goal_id = int(query.data.replace('delete_goal_', ''))
        context.user_data['selected_goal_id'] = goal_id
        
        # Buscar informações do objetivo
        goals = db.get_user_goals(query.from_user.id)
        selected_goal = None
        
        for goal in goals:
            if goal['id'] == goal_id:
                selected_goal = goal
                break
        
        if selected_goal:
            keyboard = [
                [InlineKeyboardButton("✅ SIM, Excluir", callback_data=f"confirm_delete_{goal_id}")],
                [InlineKeyboardButton("❌ NÃO, Cancelar", callback_data="cancel_confirm_delete")]
            ]
            
            await query.edit_message_text(
                f"🗑️ CONFIRMAR EXCLUSÃO\n\n"
                f"Tem certeza que deseja excluir este objetivo?\n\n"
                f"🎯 {selected_goal['descricao']}\n"
                f"💰 Meta: R$ {selected_goal['valor_meta']:,.2f}\n"
                f"📈 Progresso: R$ {selected_goal['progresso'] or 0:,.2f}\n\n"
                f"⚠️ Esta ação não pode ser desfeita!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CONFIRM_DELETE_GOAL
    
    await query.edit_message_text("❌ Erro ao selecionar objetivo.")
    return ConversationHandler.END

async def handle_confirm_delete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_confirm_delete":
        await query.edit_message_text("❌ Exclusão cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if query.data.startswith("confirm_delete_"):
        goal_id = int(query.data.replace('confirm_delete_', ''))
        success = db.delete_goal(goal_id)
        
        if success:
            await query.edit_message_text(
                "✅ OBJETIVO EXCLUÍDO!\n\n"
                "O objetivo foi removido com sucesso.",
                reply_markup=objetivos_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao excluir objetivo.",
                reply_markup=objetivos_keyboard()
            )
    
    return ConversationHandler.END

# ========== EDUCAÇÃO FINANCEIRA ==========
async def educacao_financeira_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 EDUCAÇÃO FINANCEIRA\n\n"
        "Aprenda sobre finanças e melhore sua saúde financeira:",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def dica_do_dia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dica = coach.get_daily_tip()
    await update.message.reply_text(
        f"💡 DICA DO DIA\n\n{dica}",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def glossario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 GLOSSÁRIO FINANCEIRO\n\n"
        "Em desenvolvimento...",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def modulos_educativos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 MÓDULOS EDUCATIVOS\n\n"
        "Em desenvolvimento...",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def handle_modulos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("modulo_"):
        modulo_id = data.replace("modulo_", "")
        # Implementar lógica dos módulos aqui
        await query.edit_message_text(
            f"🎓 Módulo {modulo_id}\n\nEm desenvolvimento...",
            reply_markup=educacao_keyboard()
        )
    return ConversationHandler.END

# ========== HANDLER PRINCIPAL ==========
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal para todas as mensagens do menu"""
    user_id = update.effective_user.id
    
    # Verificar se o usuário existe
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    text = update.message.text
    
    # Mapeamento dos handlers principais - ADICIONAR ESTAS LINHAS:
    if text == '💰 Salário':
        return await salario_handler(update, context)
    elif text == '💵 Renda extra':
        return await renda_extra_handler(update, context)
    
    # Mapeamento dos handlers principais
    handlers = {
        '🧮 Gastos / Rendas': adicionar_gastos_handler,
        '🧾 Meu Extrato': extrato_gastos_handler,
        '📈 Saúde Financeira': saude_financeira_handler,
        '🎓 Educação Financeira': educacao_financeira_handler,
        '🎯 Objetivos': objetivos_handler,
        '⚙️ Configurações': lambda u, c: u.message.reply_text("⚙️ CONFIGURAÇÕES", reply_markup=config_keyboard()),
        '❓ Ajuda': ajuda_handler,
        
        # Submenus de Gastos
        '🏦 Gastos Fixos': iniciar_registro_gasto,
        '🛍️ Gastos Flexíveis': iniciar_registro_gasto,
        '💰 Salário': salario_handler,
        '💵 Renda extra': renda_extra_handler,
        
        # Submenus de Saúde Financeira
        '📊 Ver Métricas Detalhadas': ver_metricas_handler,
        '🧠 Recomendações IA': recomendacoes_ia_handler,
        '📈 Análise Detalhada com IA': analise_detalhada_ia_handler,
        
        # Submenus de Educação
        '💡 Dica do Dia': dica_do_dia_handler,
        '📚 Glossário': glossario_handler,
        '🎓 Módulos Educativos': modulos_educativos_handler,
        
        # Submenus de Configurações
        '✏️ Editar Perfil': edit_profile_handler,
        '''
        '💰 Alterar Salário': edit_salary_handler,
        '''
        '🔄 Redefinir': reset_data_handler,
        
        # Submenus de Objetivos
        '🎯 Adicionar Objetivo': add_goal_handler,
        '📊 Atualizar Progresso': update_goal_progress_handler,
        '🗑️ Excluir Objetivo': delete_goal_handler,
        '📋 Meus Objetivos': meus_objetivos_handler,
        
        # Voltar ao Menu
        '🏠 Voltar ao Menu': lambda u, c: u.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard()),
    }
    
    if text in handlers:
        return await handlers[text](update, context)
    else:
        await update.message.reply_text(
            "❌ Comando não reconhecido.\n\n"
            "Use o menu abaixo para navegar:",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END

# ========== HANDLERS DE CALLBACK ==========
async def handle_analise_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    try:
        if data == "analise_metricas":
            user_data = db.get_user_data(user_id)
            expenses = db.get_monthly_expenses(user_id)
            
            total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
            total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
            total_geral = total_fixo + total_flexivel
            
            salario = user_data['salario_liquido'] if user_data else 0
            saldo = salario - total_geral
            percentual = (total_geral / salario * 100) if salario > 0 else 0
            
            response = f"📊 **MÉTRICAS DETALHADAS**\n\n"
            response += f"• 💵 Salário: R$ {salario:,.2f}\n"
            response += f"• 🏠 Fixos: R$ {total_fixo:,.2f}\n"
            response += f"• 🛍️ Flexíveis: R$ {total_flexivel:,.2f}\n"
            response += f"• 💰 Total: R$ {total_geral:,.2f}\n"
            response += f"• ⚖️ Saldo: R$ {saldo:,.2f}\n"
            response += f"• 📈 Comprometido: {percentual:.1f}%\n\n"
            
            # Análise adicional
            if total_fixo > 0 and total_flexivel > 0:
                proporcao_fixo = (total_fixo / total_geral) * 100
                proporcao_flex = (total_flexivel / total_geral) * 100
                response += f"📊 **Distribuição:**\n"
                response += f"• Fixos: {proporcao_fixo:.1f}%\n"
                response += f"• Flexíveis: {proporcao_flex:.1f}%\n"
            
            await query.edit_message_text(response, reply_markup=analise_detalhada_inline_keyboard())
            
        elif data == "analise_metas":
            await query.edit_message_text("🤖 Gerando metas sugeridas...")
            metas = await coach.finance_coach.get_suggested_goals(user_id)
            await query.edit_message_text(
                f"🎯 **METAS SUGERIDAS**\n\n{metas}",
                reply_markup=analise_detalhada_inline_keyboard()
            )
            
        elif data == "analise_recomendacoes":
            await query.edit_message_text("🤖 Gerando recomendações...")
            recomendacoes = await coach.finance_coach.get_personalized_recommendations(user_id)
            await query.edit_message_text(
                f"🧠 **RECOMENDAÇÕES IA**\n\n{recomendacoes}",
                reply_markup=analise_detalhada_inline_keyboard()
            )
            
        elif data == "analise_voltar":
            await query.edit_message_text("🏠 Voltando ao Menu Principal")
            await context.bot.send_message(
                user_id, 
                "🏠 MENU PRINCIPAL", 
                reply_markup=main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Erro no callback de análise: {e}")
        await query.edit_message_text("❌ Erro ao processar solicitação.", reply_markup=analise_detalhada_inline_keyboard())
        
async def voltar_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para voltar ao menu principal"""
    await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
    return ConversationHandler.END
    
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela operação via callback"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Operação cancelada.")
    await context.bot.send_message(
        query.from_user.id,
        "🏠 MENU PRINCIPAL",
        reply_markup=main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END