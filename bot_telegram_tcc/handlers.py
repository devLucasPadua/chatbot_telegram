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
# Cadastro inicial
GET_NAME, GET_SALARY, TIPO_GASTO = range(3)

# Registro de gastos
CATEGORIA_FIXA, CATEGORIA_FLEXIVEL, NOVA_CATEGORIA_FIXA, NOVA_CATEGORIA_FLEXIVEL = range(3, 7)
VALOR_GASTO, DATA_GASTO, CONTINUAR_GASTOS, RESUMO_GASTOS = range(7, 11)

# Categorias personalizadas
OUTROS_FLEXIVEIS, MINHAS_CATEGORIAS, NOVA_CATEGORIA_OUTROS, CONFIRM_GASTO_OUTROS = range(11, 15)
OUTROS_FIXOS, MINHAS_CATEGORIAS_FIXAS, NOVA_CATEGORIA_OUTROS_FIXOS, CONFIRM_GASTO_OUTROS_FIXOS = range(15, 19)

# Suas categorias
SUAS_CATEGORIAS, CATEGORIAS_FIXAS, CATEGORIAS_FLEXIVEIS = range(19, 22)
SELECIONAR_CATEGORIA_EXCLUIR, CONFIRMAR_EXCLUSAO_CATEGORIA = range(22, 24)

# Configurações
EDIT_NAME, EDIT_SALARY, CONFIRM_RESET = range(24, 27)

# Objetivos
GOAL_TYPE, GOAL_DESCRIPTION, GOAL_TARGET, GOAL_DEADLINE = range(27, 31)
SELECT_GOAL, UPDATE_GOAL_PROGRESS, SELECT_GOAL_DELETE, CONFIRM_DELETE_GOAL = range(31, 35)

# Adicione este novo estado na seção de estados (logo após GOAL_DEADLINE)
GOAL_DEADLINE_CALENDAR = 35  # Ajuste o número conforme necessário

# Gastos do mês
GASTOS_MES = 35

# Educação Financeira
DICA_DIA, GLOSSARIO, MODULOS_EDUCATIVOS = range(36, 39)

# ========== CONFIGURAÇÃO DE LOGGING ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== KEYBOARDS ==========
def main_keyboard():
    keyboard = [
        ['🏠 Registrar Gastos', '📊 Meu Extrato'],  # ALTERADO: Meu Resumo → Meu Extrato
        ['📈 Saúde Financeira', '🎓 Educação Financeira'],
        ['🎯 Objetivos', '⚙️ Configurações'],
        ['❓ Ajuda']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def gastos_keyboard():
    keyboard = [
        ['🏠 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['📅 Gastos do Mês', '📂 Suas Categorias'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def tipo_gasto_keyboard():
    keyboard = [
        ['🏠 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_fixas_keyboard():
    keyboard = []
    categorias = list(config.CATEGORIAS_FIXAS.keys())
    for i in range(0, len(categorias), 2):
        keyboard.append(categorias[i:i+2])
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categorias_flexiveis_keyboard():
    keyboard = []
    categorias = list(config.CATEGORIAS_FLEXIVEIS.keys())
    for i in range(0, len(categorias), 2):
        keyboard.append(categorias[i:i+2])
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
        ['🏠 Fixas', '🛍️ Flexíveis'],
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
        ['✏️ Editar Perfil', '💰 Alterar Salário'],
        ['🔄 Redefinir', '🏠 Voltar ao Menu']
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
    def create_calendar(year=None, month=None):
        now = datetime.datetime.now()
        if year is None: year = now.year
        if month is None: month = now.month

        if month < 1:
            month = 12
            year -= 1
        if month > 12:
            month = 1
            year += 1

        keyboard = []
        month_name = calendar.month_name[month]
        header = f"{month_name} {year}"
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"CAL_PREV_{year}_{month}"),
            InlineKeyboardButton(header, callback_data="CAL_IGNORE"),
            InlineKeyboardButton("▶️", callback_data=f"CAL_NEXT_{year}_{month}")
        ])

        week_days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        keyboard.append([InlineKeyboardButton(d, callback_data="CAL_IGNORE") for d in week_days])

        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)
        for week in month_days:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="CAL_IGNORE"))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=f"CAL_DAY_{year}_{month:02d}_{day:02d}"))
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton("📅 Hoje", callback_data="CAL_TODAY"),
            InlineKeyboardButton("⌨️ Digitar", callback_data="CAL_MANUAL")
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        try:
            if data == "MY_SHOW_CALENDAR":
                await query.edit_message_text(
                    "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver as estatísticas:",
                    reply_markup=MonthYearCalendar.create_month_year_calendar()
                )
                return h.GASTOS_MES
                
            if data == "MY_BACK":
                await query.edit_message_text("🏠 Voltando ao Menu")
                await context.bot.send_message(
                    query.from_user.id,
                    "🏠 REGISTRAR GASTOS", 
                    reply_markup=h.gastos_keyboard()
                )
                return ConversationHandler.END    
                
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

            if data.startswith("CAL_PREV_") or data.startswith("CAL_NEXT_"):
                parts = data.split('_')
                year, month = int(parts[2]), int(parts[3])
                
                if data.startswith("CAL_PREV_"):
                    month -= 1
                    if month < 1:
                        month, year = 12, year - 1
                else:
                    month += 1
                    if month > 12:
                        month, year = 1, year + 1
                
                try:
                    await query.edit_message_reply_markup(reply_markup=Calendar.create_calendar(year, month))
                except Exception:
                    await context.bot.send_message(
                        chat_id=query.from_user.id,
                        text="📅 Navegação do calendário:",
                        reply_markup=Calendar.create_calendar(year, month)
                    )
                return DATA_GASTO

            return DATA_GASTO

        except Exception as e:
            logger.error(f"Erro no calendário mensal: {e}")
            await query.message.reply_text("❌ Erro ao processar seleção.", reply_markup=h.gastos_keyboard())
            return ConversationHandler.END

    @staticmethod
    async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
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
        
        keyboard.append([
            InlineKeyboardButton("🏠 Voltar", callback_data="MY_BACK"),
            InlineKeyboardButton("📅 Este Mês", callback_data=f"MY_MONTH_{now.year}_{now.month:02d}")
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        try:
            # BOTÃO "VER OUTRO MÊS" - VOLTAR AO CALENDÁRIO
            if data == "MY_SHOW_CALENDAR":
                await query.edit_message_text(
                    "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver as estatísticas:",
                    reply_markup=MonthYearCalendar.create_month_year_calendar()
                )
                return GASTOS_MES
            
            # BOTÃO "VOLTAR AO MENU" DAS ESTATÍSTICAS
            elif data == "MY_BACK":
                await query.edit_message_text("🏠 Voltando ao Menu")
                await context.bot.send_message(
                    query.from_user.id,
                    "🏠 REGISTRAR GASTOS", 
                    reply_markup=gastos_keyboard()
                )
                return ConversationHandler.END
            
            # NAVEGAÇÃO ANO ANTERIOR
            elif data.startswith("MY_PREV_"):
                year = int(data.split('_')[2]) - 1
                await query.edit_message_reply_markup(reply_markup=MonthYearCalendar.create_month_year_calendar(year))
                return GASTOS_MES
            
            # NAVEGAÇÃO PRÓXIMO ANO
            elif data.startswith("MY_NEXT_"):
                year = int(data.split('_')[2]) + 1
                await query.edit_message_reply_markup(reply_markup=MonthYearCalendar.create_month_year_calendar(year))
                return GASTOS_MES
            
            # SELEÇÃO DE MÊS ESPECÍFICO
            elif data.startswith("MY_MONTH_"):
                parts = data.split('_')
                year, month = int(parts[2]), int(parts[3])
                await MonthYearCalendar.show_month_stats(query, context, year, month)
                return GASTOS_MES
                
        except Exception as e:
            logger.error(f"Erro no calendário mensal: {e}")
            await query.message.reply_text("❌ Erro ao processar seleção.", reply_markup=gastos_keyboard())
            return ConversationHandler.END

    @staticmethod
    async def show_month_stats(query, context, year: int, month: int):
        user_id = query.from_user.id
        try:
            expenses = db.get_monthly_expenses(user_id, month, year)
            user_data = db.get_user_data(user_id)
            
            total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
            total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
            total_geral = total_fixo + total_flexivel
            
            salario = user_data['salario_liquido'] if user_data else 0
            saldo = salario - total_geral
            percentual_gastos = (total_geral / salario * 100) if salario > 0 else 0
            
            meses_ptbr = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            month_name = meses_ptbr[month-1]
            
            message = f"📊 **{month_name}/{year}**\n\n"
            
            if total_geral > 0:
                message += f"💰 **RESUMO GERAL**\n"
                message += f"• 🏠 Fixos: R$ {total_fixo:,.2f}\n"
                message += f"• 🛍️ Flexíveis: R$ {total_flexivel:,.2f}\n"
                message += f"• 💰 Total: R$ {total_geral:,.2f}\n"
                
                if salario > 0:
                    message += f"• 💵 Salário: R$ {salario:,.2f}\n"
                    message += f"• ⚖️ Saldo: R$ {saldo:,.2f}\n"
                    message += f"• 📈 Comprometido: {percentual_gastos:.1f}%\n\n"
                
                proporcao_fixo = (total_fixo/total_geral)*100
                proporcao_flex = (total_flexivel/total_geral)*100
                bar_len = 10
                bar_fixo = '🟦' * int(proporcao_fixo/100*bar_len)
                bar_flex = '🟩' * int(proporcao_flex/100*bar_len)
                message += f"📊 **DISTRIBUIÇÃO**\n"
                message += f"🏠 Fixos: {bar_fixo} {proporcao_fixo:.1f}%\n"
                message += f"🛍️ Flexíveis: {bar_flex} {proporcao_flex:.1f}%\n"
            else:
                message += f"📝 Nenhum gasto registrado em {month_name}/{year}."
            
            # BOTÕES CORRETOS - "Ver Outro Mês" deve chamar MY_SHOW_CALENDAR
            keyboard = [
                [InlineKeyboardButton("📅 Ver Outro Mês", callback_data="MY_SHOW_CALENDAR")],
                [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="MY_BACK")]
            ]
            
            await query.edit_message_text(
                text=message, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            keyboard = [
                [InlineKeyboardButton("📅 Tentar Novamente", callback_data="MY_SHOW_CALENDAR")],
                [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="MY_BACK")]
            ]
            await query.edit_message_text(
                "❌ Erro ao carregar estatísticas.", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

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
        
        success = db.add_user(user_id, nickname, salario_liquido)
        if not success:
            await update.message.reply_text("❌ Erro ao salvar dados.")
            return GET_SALARY
        
        await update.message.reply_text(f"🎉 Perfil criado com sucesso, {nickname}!")
        await update.message.reply_text(
            "💡 Educação Financeira: Tipos de Gastos\n\n"
            "🏠 GASTOS FIXOS: despesas regulares e previsíveis\n"
            "🛍️ GASTOS FLEXÍVEIS: despesas variáveis"
        )
        await update.message.reply_text(
            "💸 Vamos registrar seu primeiro gasto?",
            reply_markup=tipo_gasto_keyboard()
        )
        return TIPO_GASTO
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número, ex.: 1500,00")
        return GET_SALARY

# ========== REGISTRO DE GASTOS ==========
async def adicionar_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return ConversationHandler.END
    
    context.user_data['user_id'] = user_id
    await update.message.reply_text(
        "💸 REGISTRAR GASTOS\n\nSelecione o tipo de gasto:",
        reply_markup=gastos_keyboard()
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
        return GASTOS_MES
        
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
        
    elif 'Voltar ao Menu' in text:
        await update.message.reply_text("🏠 MENU PRINCIPAL", reply_markup=main_keyboard())
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Selecione uma opção válida:", reply_markup=tipo_gasto_keyboard())
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

# ========== EXTRATO DETALHADO ==========
async def extrato_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Meu Extrato - Lista todos os gastos detalhadamente"""
    user_id = update.effective_user.id
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar.")
        return ConversationHandler.END
        
    # Buscar todas as transações do usuário
    try:
        transactions = db.get_all_transactions(user_id)
        
        if not transactions:
            await update.message.reply_text(
                "📝 **MEU EXTRATO**\n\n"
                "Nenhum gasto registrado até o momento.\n\n"
                "💡 Use '🏠 Registrar Gastos' para adicionar seu primeiro gasto!",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END
        
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname'] if user_data else 'Usuário'
        
        response = f"📊 **EXTRATO COMPLETO - {nickname}**\n\n"
        
        total_geral = 0
        total_fixo = 0
        total_flexivel = 0
        
        # Agrupar transações por mês
        transacoes_por_mes = {}
        for transacao in transactions:
            try:
                data_obj = datetime.datetime.strptime(transacao['data'], '%d/%m/%Y')
                mes_ano = data_obj.strftime('%m/%Y')
                if mes_ano not in transacoes_por_mes:
                    transacoes_por_mes[mes_ano] = []
                transacoes_por_mes[mes_ano].append(transacao)
                
                # Calcular totais
                if transacao['tipo'] == 'fixo':
                    total_fixo += transacao['valor']
                else:
                    total_flexivel += transacao['valor']
                total_geral += transacao['valor']
            except Exception as e:
                logger.error(f"Erro ao processar transação: {e}")
                continue
        
        # Listar transações por mês
        for mes_ano, transacoes_mes in transacoes_por_mes.items():
            mes, ano = mes_ano.split('/')
            meses_ptbr = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            nome_mes = meses_ptbr[int(mes)-1]
            
            response += f"      📅 {nome_mes}/{ano}\n\n"
            
            for transacao in transacoes_mes:
                emoji = "🏠" if transacao['tipo'] == 'fixo' else "🛍️"
                response += f"• {emoji} {transacao['data']} - {transacao['categoria']}: R$ {transacao['valor']:,.2f}\n"
            
            response += "\n"
        
        # Adicionar resumo geral
        response += f"      📋 RESUMO GERAL\n\n"
        response += f"🏠 Gastos Fixos: R$ {total_fixo:,.2f}\n"
        response += f"🛍️ Gastos Flexíveis: R$ {total_flexivel:,.2f}\n"
        response += f"💰 Total Gasto: R$ {total_geral:,.2f}\n\n"
        
        if user_data and user_data['salario_liquido'] and user_data['salario_liquido'] > 0:
            salario = user_data['salario_liquido']
            saldo = salario - total_geral
            percentual = (total_geral / salario * 100) if salario > 0 else 0
            
            response += f"💵 Salário: R$ {salario:,.2f}\n"
            response += f"⚖️ Saldo: R$ {saldo:,.2f}\n"
            response += f"📈 Comprometido: {percentual:.1f}%\n\n"
            
            if percentual <= 60:
                response += "✅ Situação: ** Saudável **\n"
            elif percentual <= 85:
                response += "⚠️ Situação: ** Atenção **\n"
            else:
                response += "🚨 Situação: ** Crítico **\n"
        
        response += f"\n📊 Total de transações: {len(transactions)}"
        
        # Se a mensagem for muito longa, dividir em partes
        if len(response) > 4000:
            parte1 = response[:4000]
            parte2 = response[4000:]
            await update.message.reply_text(parte1, reply_markup=main_keyboard())
            await update.message.reply_text(parte2, reply_markup=main_keyboard())
        else:
            await update.message.reply_text(response, reply_markup=main_keyboard())
        
    except Exception as e:
        logger.error(f"Erro ao gerar extrato: {e}")
        await update.message.reply_text(
            "❌ Erro ao carregar extrato.\n"
            "Tente novamente ou entre em contato com o suporte.",
            reply_markup=main_keyboard()
        )
    
    return ConversationHandler.END

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
                f"🎯 METAS SUGERIDAS\n\n{metas}",
                reply_markup=analise_detalhada_inline_keyboard()
            )
            
        elif data == "analise_recomendacoes":
            await query.edit_message_text("🤖 Gerando recomendações...")
            recs = await coach.finance_coach.get_personalized_recommendations(user_id)
            await query.edit_message_text(
                f"💡 RECOMENDAÇÕES\n\n{recs}",
                reply_markup=analise_detalhada_inline_keyboard()
            )
            
        elif data == "analise_voltar":
            await query.edit_message_text("Voltando ao menu...")
            await context.bot.send_message(
                user_id, 
                "📈 SAÚDE FINANCEIRA", 
                reply_markup=saude_financeira_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Erro no callback: {e}")
        await query.edit_message_text("❌ Erro ao processar.", reply_markup=analise_detalhada_inline_keyboard())

# ========== OBJETIVOS ==========
async def objetivos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 OBJETIVOS FINANCEIROS\n\nGerencie suas metas:",
        reply_markup=objetivos_keyboard()
    )
    return ConversationHandler.END

async def add_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 VAMOS CRIAR SEU OBJETIVO!\n\n"
        
        "Primeiro, qual o TIPO do seu objetivo?\n\n"
        
        "Sugestões:\n"
        "💰 Economia - ex: reserva de emergência\n"
        "📈 Investimento - ex: aplicações\n" 
        "🛒 Compra - ex: celular, móveis\n"
        "🎓 Educação - ex: cursos, faculdade\n"
        "🏠 Moradia - ex: casa, reforma\n"
        "🚗 Transporte - ex: carro, manutenção\n"
        "💊 Saúde - ex: tratamentos, planos\n"
        "✈️ Viagem - ex: férias, passeios\n\n"
        
        "Digite o tipo do seu objetivo:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GOAL_TYPE
    
async def goal_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_type = update.message.text.strip()
    if not goal_type:
        await update.message.reply_text("❌ Tipo de objetivo inválido. Digite novamente:")
        return GOAL_TYPE
        
    context.user_data['goal_type'] = goal_type
    await update.message.reply_text("📝 Descreva o objetivo (ex: 'Reserva de emergência', 'Viagem para praia'):")
    return GOAL_DESCRIPTION

async def goal_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()
    if not description:
        await update.message.reply_text("❌ Descrição inválida. Digite novamente:")
        return GOAL_DESCRIPTION
        
    context.user_data['goal_description'] = description
    await update.message.reply_text("💰 Qual o valor meta? (ex: 1000,00)")
    return GOAL_TARGET

async def goal_target_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_text = update.message.text.replace(',', '.').strip()
        target = float(target_text)
        
        if target <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Digite novamente:")
            return GOAL_TARGET
            
        context.user_data['goal_target'] = target
        
        # Redirecionar para o calendário em vez de pedir entrada manual
        await update.message.reply_text(
            "📅 **SELECIONE O PRAZO DO OBJETIVO**\n\n"
            "Escolha a data limite para alcançar sua meta:",
            reply_markup=Calendar.create_calendar()
        )
        return GOAL_DEADLINE_CALENDAR
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex: 1000,00):")
        return GOAL_TARGET

async def goal_deadline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para selecionar o prazo do objetivo usando calendário"""
    await update.message.reply_text(
        "📅 **SELECIONE O PRAZO DO OBJETIVO**\n\n"
        "Escolha a data limite para alcançar sua meta:",
        reply_markup=Calendar.create_calendar()
    )
    return GOAL_DEADLINE_CALENDAR
    
# Adicione este novo estado na seção de estados (logo após GOAL_DEADLINE)
GOAL_DEADLINE_CALENDAR = 35  # Ajuste o número conforme necessário

async def goal_deadline_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção da data do calendário para objetivos"""
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "CAL_TODAY":
            today = datetime.datetime.now().strftime('%d/%m/%Y')
            return await goal_handle_date_selection(update, context, today)

        if data == "CAL_MANUAL":
            await query.message.reply_text(
                "📅 DIGITE A DATA DO PRAZO\n\nFormatos aceitos:\n• DD/MM/AAAA\n• DDMMAAAA\n• 'hoje' para data atual",
                reply_markup=ReplyKeyboardRemove()
            )
            return GOAL_DEADLINE

        if data.startswith("CAL_DAY_"):
            parts = data.split('_')
            year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
            selected_date = f"{day:02d}/{month:02d}/{year}"
            return await goal_handle_date_selection(update, context, selected_date)

        if data.startswith("CAL_PREV_") or data.startswith("CAL_NEXT_"):
            parts = data.split('_')
            year, month = int(parts[2]), int(parts[3])
            
            if data.startswith("CAL_PREV_"):
                month -= 1
                if month < 1:
                    month, year = 12, year - 1
            else:
                month += 1
                if month > 12:
                    month, year = 1, year + 1
            
            try:
                await query.edit_message_reply_markup(reply_markup=Calendar.create_calendar(year, month))
            except Exception:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text="📅 Navegação do calendário:",
                    reply_markup=Calendar.create_calendar(year, month)
                )
            return GOAL_DEADLINE_CALENDAR

        return GOAL_DEADLINE_CALENDAR

    except Exception as e:
        logger.error(f"Erro no calendário de objetivos: {e}")
        await query.message.reply_text("❌ Erro ao processar data.", reply_markup=objetivos_keyboard())
        return ConversationHandler.END

async def goal_handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
    """Processa a data selecionada para o objetivo"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    goal_type = context.user_data['goal_type']
    description = context.user_data['goal_description']
    target = context.user_data['goal_target']
    
    # Usar a função correta do banco de dados
    success = db.add_goal(user_id, goal_type, description, target, date_str)
    
    if success:
        try:
            await query.edit_message_text(f"✅ Data selecionada: {date_str}")
        except Exception:
            pass

        await query.message.reply_text(
            f"✅ OBJETIVO ADICIONADO!\n\n"
            f"📋 **Detalhes:**\n"
            f"• 🎯 Tipo: {goal_type}\n"
            f"• 📝 Descrição: {description}\n"
            f"• 💰 Meta: R$ {target:,.2f}\n"
            f"• 📅 Prazo: {date_str}\n\n"
            f"💪 Comece a registrar seu progresso!",
            reply_markup=objetivos_keyboard()
        )
    else:
        await query.message.reply_text(
            "❌ Erro ao adicionar objetivo.\n"
            "Tente novamente ou verifique os dados.",
            reply_markup=objetivos_keyboard()
        )
    
    # Limpar dados temporários
    context.user_data.clear()
    return ConversationHandler.END
    
async def goal_deadline_manual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para entrada manual da data do prazo"""
    deadline_input = update.message.text.strip().lower()
    
    # Processar data
    if deadline_input == 'hoje':
        deadline = datetime.datetime.now().strftime('%d/%m/%Y')
    else:
        deadline = parse_date_input(deadline_input)
        if not deadline or not validate_date(deadline):
            await update.message.reply_text(
                "❌ Data inválida!\n\n"
                "Formatos aceitos:\n"
                "• DD/MM/AAAA (ex: 31/12/2024)\n"
                "• DDMMAAAA (ex: 31122024)\n"
                "• 'hoje' para data atual\n\n"
                "Digite novamente:"
            )
            return GOAL_DEADLINE
    
    return await goal_handle_date_selection_manual(update, context, deadline)

async def goal_handle_date_selection_manual(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
    """Processa a data manual para o objetivo"""
    user_id = update.effective_user.id
    
    goal_type = context.user_data['goal_type']
    description = context.user_data['goal_description']
    target = context.user_data['goal_target']
    
    # Usar a função correta do banco de dados
    success = db.add_goal(user_id, goal_type, description, target, date_str)
    
    if success:
        await update.message.reply_text(
            f"✅ OBJETIVO ADICIONADO!\n\n"
            f"📋 **Detalhes:**\n"
            f"• 🎯 Tipo: {goal_type}\n"
            f"• 📝 Descrição: {description}\n"
            f"• 💰 Meta: R$ {target:,.2f}\n"
            f"• 📅 Prazo: {date_str}\n\n"
            f"💪 Comece a registrar seu progresso!",
            reply_markup=objetivos_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Erro ao adicionar objetivo.\n"
            "Tente novamente ou verifique os dados.",
            reply_markup=objetivos_keyboard()
        )
    
    # Limpar dados temporários
    context.user_data.clear()
    return ConversationHandler.END

async def update_goal_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de atualização do progresso de um objetivo"""
    user_id = update.effective_user.id
    goals = db.get_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "❌ Você não tem objetivos cadastrados.\n\n"
            "Use '🎯 Adicionar Objetivo' para criar seu primeiro objetivo.",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    # Criar keyboard inline com objetivos
    keyboard = []
    for goal in goals:
        if not goal['concluido']:
            # CORREÇÃO: Garantir que os valores sejam números
            valor_meta = float(goal['valor_meta']) if goal['valor_meta'] else 0
            valor_atual = float(goal['valor_atual']) if goal['valor_atual'] else 0
            progresso = (valor_atual / valor_meta * 100) if valor_meta > 0 else 0
            button_text = f"{goal['descricao']} - {progresso:.1f}%"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"goal_{goal['id']}")])
    
    if not keyboard:
        await update.message.reply_text(
            "✅ Todos os seus objetivos estão concluídos! 🎉",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="goal_cancel")])
    
    await update.message.reply_text(
        "📊 ATUALIZAR PROGRESSO\n\nSelecione o objetivo que deseja atualizar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_GOAL

async def handle_goal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção de um objetivo para atualização"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "goal_cancel":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("goal_"):
        goal_id = int(data.split('_')[1])
        context.user_data['selected_goal_id'] = goal_id
        
        # Buscar informações do objetivo
        user_id = query.from_user.id
        goals = db.get_goals(user_id)
        selected_goal = None
        
        for goal in goals:
            if goal['id'] == goal_id:
                selected_goal = goal
                break
        
        if selected_goal:
            # CORREÇÃO: Garantir que os valores sejam números
            valor_meta = float(selected_goal['valor_meta']) if selected_goal['valor_meta'] else 0
            valor_atual = float(selected_goal['valor_atual']) if selected_goal['valor_atual'] else 0
            progresso = (valor_atual / valor_meta * 100) if valor_meta > 0 else 0
            
            await query.edit_message_text(
                f"📈 ATUALIZAR PROGRESSO\n\n"
                f"🎯 **Objetivo:** {selected_goal['descricao']}\n"
                f"💰 **Meta:** R$ {valor_meta:,.2f}\n"
                f"📊 **Progresso atual:** R$ {valor_atual:,.2f} ({progresso:.1f}%)\n\n"
                f"💵 Digite o NOVO valor atual (ex.: 500,00):"
            )
            return UPDATE_GOAL_PROGRESS
    
    await query.edit_message_text("❌ Erro ao selecionar objetivo.")
    return ConversationHandler.END

async def update_goal_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Atualiza o valor do progresso do objetivo"""
    try:
        valor_text = update.message.text.replace(',', '.').strip()
        novo_valor = float(valor_text)
        goal_id = context.user_data.get('selected_goal_id')
        
        if not goal_id:
            await update.message.reply_text("❌ Objetivo não encontrado.", reply_markup=objetivos_keyboard())
            return ConversationHandler.END
        
        if novo_valor < 0:
            await update.message.reply_text("❌ O valor não pode ser negativo. Digite novamente:")
            return UPDATE_GOAL_PROGRESS
        
        success = db.update_goal_progress(goal_id, novo_valor)
        
        if success:
            # Buscar informações atualizadas
            user_id = update.effective_user.id
            goals = db.get_goals(user_id)
            updated_goal = None
            
            for goal in goals:
                if goal['id'] == goal_id:
                    updated_goal = goal
                    break
            
            if updated_goal:
                progresso = (updated_goal['valor_atual'] / updated_goal['valor_meta']) * 100 if updated_goal['valor_meta'] > 0 else 0
                
                if updated_goal['concluido']:
                    mensagem = f"🎉 **OBJETIVO CONCLUÍDO!** 🎉\n\n"
                    mensagem += f"✅ {updated_goal['descricao']}\n"
                    mensagem += f"💰 Meta: R$ {updated_goal['valor_meta']:,.2f}\n"
                    mensagem += f"📈 Progresso: 100%\n\n"
                    mensagem += "Parabéns! 🎊"
                else:
                    mensagem = f"✅ PROGRESSO ATUALIZADO!\n\n"
                    mensagem += f"🎯 {updated_goal['descricao']}\n"
                    mensagem += f"💰 Meta: R$ {updated_goal['valor_meta']:,.2f}\n"
                    mensagem += f"📊 Progresso: R$ {updated_goal['valor_atual']:,.2f} ({progresso:.1f}%)\n\n"
                    mensagem += "Continue assim! 💪"
                
                await update.message.reply_text(mensagem, reply_markup=objetivos_keyboard())
            else:
                await update.message.reply_text("✅ Progresso atualizado!", reply_markup=objetivos_keyboard())
        else:
            await update.message.reply_text("❌ Erro ao atualizar progresso.", reply_markup=objetivos_keyboard())
        
        # Limpar dados temporários
        context.user_data.pop('selected_goal_id', None)
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido! Digite um número (ex.: 500,00)")
        return UPDATE_GOAL_PROGRESS

async def delete_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de exclusão de um objetivo"""
    user_id = update.effective_user.id
    goals = db.get_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "❌ Você não tem objetivos cadastrados.",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    # Criar keyboard inline com objetivos
    keyboard = []
    for goal in goals:
        progresso = (goal['valor_atual'] / goal['valor_meta']) * 100 if goal['valor_meta'] > 0 else 0
        status = "✅ " if goal['concluido'] else "📊 "
        button_text = f"{status}{goal['descricao']} - {progresso:.1f}%"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_goal_{goal['id']}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="delete_goal_cancel")])
    
    await update.message.reply_text(
        "🗑️ EXCLUIR OBJETIVO\n\nSelecione o objetivo que deseja excluir:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_GOAL_DELETE

async def handle_goal_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção de um objetivo para exclusão"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "delete_goal_cancel":
        await query.edit_message_text("❌ Operação cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("delete_goal_"):
        goal_id = int(data.split('_')[2])
        context.user_data['goal_to_delete_id'] = goal_id
        
        # Buscar informações do objetivo
        user_id = query.from_user.id
        goals = db.get_goals(user_id)
        selected_goal = None
        
        for goal in goals:
            if goal['id'] == goal_id:
                selected_goal = goal
                break
        
        if selected_goal:
            # CORREÇÃO: Garantir que os valores sejam números
            valor_meta = float(selected_goal['valor_meta']) if selected_goal['valor_meta'] else 0
            valor_atual = float(selected_goal['valor_atual']) if selected_goal['valor_atual'] else 0
            progresso = (valor_atual / valor_meta * 100) if valor_meta > 0 else 0
            status = "CONCLUÍDO" if selected_goal['concluido'] else "EM ANDAMENTO"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ SIM, Excluir", callback_data=f"confirm_delete_{goal_id}"),
                    InlineKeyboardButton("❌ NÃO, Cancelar", callback_data="confirm_delete_cancel")
                ]
            ]
            
            await query.edit_message_text(
                f"🚨 CONFIRMAR EXCLUSÃO\n\n"
                f"🗑️ **Objetivo:** {selected_goal['descricao']}\n"
                f"💰 **Meta:** R$ {valor_meta:,.2f}\n"
                f"📊 **Progresso:** R$ {valor_atual:,.2f} ({progresso:.1f}%)\n"
                f"📈 **Status:** {status}\n\n"
                f"Tem certeza que deseja EXCLUIR este objetivo?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CONFIRM_DELETE_GOAL
    
    await query.edit_message_text("❌ Erro ao selecionar objetivo.")
    return ConversationHandler.END

async def handle_confirm_delete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma e executa a exclusão do objetivo"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "confirm_delete_cancel":
        await query.edit_message_text("✅ Exclusão cancelada.")
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("confirm_delete_"):
        goal_id = int(data.split('_')[2])
        
        # Buscar informações antes de excluir para mostrar na mensagem
        user_id = query.from_user.id
        goals = db.get_goals(user_id)
        goal_to_delete = None
        
        for goal in goals:
            if goal['id'] == goal_id:
                goal_to_delete = goal
                break
        
        success = db.delete_goal(goal_id)
        
        if success:
            if goal_to_delete:
                await query.edit_message_text(
                    f"✅ OBJETIVO EXCLUÍDO\n\n"
                    f"🗑️ **{goal_to_delete['descricao']}**\n"
                    f"💰 Meta: R$ {goal_to_delete['valor_meta']:,.2f}\n\n"
                    f"Objetivo removido com sucesso."
                )
            else:
                await query.edit_message_text("✅ Objetivo excluído com sucesso.")
        else:
            await query.edit_message_text("❌ Erro ao excluir objetivo.")
        
        # Limpar dados temporários
        context.user_data.pop('goal_to_delete_id', None)
        
        await context.bot.send_message(
            query.from_user.id,
            "🎯 OBJETIVOS",
            reply_markup=objetivos_keyboard()
        )
    
    return ConversationHandler.END

async def meus_objetivos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra todos os objetivos do usuário"""
    user_id = update.effective_user.id
    goals = db.get_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "📝 Você ainda não tem objetivos cadastrados.\n\n"
            "Use '🎯 Adicionar Objetivo' para criar seu primeiro objetivo!",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
    
    response = "🎯 **MEUS OBJETIVOS**\n\n"
    
    objetivos_concluidos = 0
    for i, goal in enumerate(goals, 1):
        # CORREÇÃO: Garantir que os valores sejam números
        valor_meta = float(goal['valor_meta']) if goal['valor_meta'] else 0
        valor_atual = float(goal['valor_atual']) if goal['valor_atual'] else 0
        progresso = (valor_atual / valor_meta * 100) if valor_meta > 0 else 0
        status = "✅ CONCLUÍDO" if goal['concluido'] else f"📊 {progresso:.1f}%"
        emoji = "✅" if goal['concluido'] else "🎯"
        
        if goal['concluido']:
            objetivos_concluidos += 1
        
        response += f"{emoji} **{goal['descricao']}**\n"
        response += f"   💰 Meta: R$ {valor_meta:,.2f}\n"
        response += f"   📈 Progresso: R$ {valor_atual:,.2f}\n"
        response += f"   🏷️ Status: {status}\n"
        
        if not goal['concluido'] and valor_meta > 0:
            bar_length = 10
            filled_length = int(bar_length * progresso / 100)
            bar = '🟩' * filled_length + '⬜' * (bar_length - filled_length)
            response += f"   {bar} {progresso:.1f}%\n"
        
        response += "\n"
    
    # Adicionar resumo
    response += f"📊 **Resumo:** {objetivos_concluidos}/{len(goals)} objetivos concluídos\n\n"
    response += "💪 Continue trabalhando em suas metas!"
    
    await update.message.reply_text(response, reply_markup=objetivos_keyboard())
    return ConversationHandler.END

# ========== CONFIGURAÇÕES ==========
async def config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ CONFIGURAÇÕES\n\nGerencie seu perfil:",
        reply_markup=config_keyboard()
    )
    return ConversationHandler.END

async def edit_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    if not user_data:
        await update.message.reply_text("❌ Erro: Dados do usuário não encontrados.", reply_markup=config_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text(
        f"✏️ EDITAR PERFIL\n\nNome atual: {user_data['nickname']}\n\nDigite o novo nome:",
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_NAME

async def edit_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not new_name:
        await update.message.reply_text("❌ Nome inválido. Digite um nome válido:")
        return EDIT_NAME
    
    if len(new_name) < 2:
        await update.message.reply_text("❌ Nome muito curto. Digite um nome com pelo menos 2 caracteres:")
        return EDIT_NAME
    
    if len(new_name) > 50:
        await update.message.reply_text("❌ Nome muito longo. Digite um nome com até 50 caracteres:")
        return EDIT_NAME
    
    # Usar função específica para atualizar nome
    success = db.update_user_name(user_id, new_name)
    
    if success:
        await update.message.reply_text(
            f"✅ Nome alterado para: {new_name}\n\n"
            f"Seu perfil foi atualizado com sucesso!",
            reply_markup=config_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Erro ao alterar nome.\n"
            "Tente novamente ou entre em contato com o suporte.",
            reply_markup=config_keyboard()
        )
    
    return ConversationHandler.END

async def edit_salary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    if not user_data:
        await update.message.reply_text("❌ Erro: Dados do usuário não encontrados.", reply_markup=config_keyboard())
        return ConversationHandler.END
        
    await update.message.reply_text(
        f"💰 ALTERAR SALÁRIO\n\n"
        f"Salário atual: R$ {user_data['salario_liquido']:,.2f}\n\n"
        f"Digite o novo valor do seu salário líquido mensal:\n"
        f"(ex: 2500,00 ou 3500.50)",
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_SALARY

async def edit_salary_process_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        new_salary = float(salary_text)
        user_id = update.effective_user.id
        
        if new_salary <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Digite novamente:")
            return EDIT_SALARY
        
        if new_salary > 1000000:  # Limite razoável de 1 milhão
            await update.message.reply_text("❌ Valor muito alto. Digite um valor válido:")
            return EDIT_SALARY
        
        success = db.update_user_salary(user_id, new_salary)
        
        if success:
            await update.message.reply_text(
                f"✅ Salário alterado para: R$ {new_salary:,.2f}\n\n"
                f"Seu salário foi atualizado com sucesso!\n"
                f"Isso afetará suas análises financeiras.",
                reply_markup=config_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao alterar salário.\n"
                "Tente novamente ou entre em contato com o suporte.",
                reply_markup=config_keyboard()
            )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Valor inválido!\n\n"
            "Digite um número válido:\n"
            "• Ex: 2500,00\n"
            "• Ex: 3500.50\n"
            "• Ex: 1500"
        )
        return EDIT_SALARY

async def reset_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 REDEFINIR DADOS\n\n"
        "⚠️ **ATENÇÃO: Esta ação é IRREVERSÍVEL!**\n\n"
        "Isso irá:\n"
        "• ❌ Excluir TODOS os seus gastos registrados\n"
        "• ❌ Remover TODOS os seus objetivos\n"
        "• ❌ Limpar suas categorias personalizadas\n"
        "• ✅ Manter apenas seu cadastro básico (nome e salário)\n\n"
        "Tem certeza absoluta que deseja continuar?",
        reply_markup=sim_nao_keyboard()
    )
    return CONFIRM_RESET

async def confirm_reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'SIM' in text:
        success = db.reset_user_data(user_id)
        
        if success:
            await update.message.reply_text(
                "✅ **DADOS REDEFINIDOS COM SUCESSO!**\n\n"
                "Todos os seus dados foram limpos:\n"
                "• 📊 Gastos removidos\n"
                "• 🎯 Objetivos excluídos\n"
                "• 📂 Categorias personalizadas limpas\n\n"
                "Seu cadastro básico foi mantido.\n"
                "Você pode começar novamente! 🎉",
                reply_markup=main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao redefinir dados.\n"
                "Tente novamente ou entre em contato com o suporte.",
                reply_markup=config_keyboard()
            )
    else:
        await update.message.reply_text(
            "✅ Operação cancelada.\n"
            "Seus dados estão seguros.",
            reply_markup=config_keyboard()
        )
    
    return ConversationHandler.END

# ========== HANDLER UNIVERSAL PARA VOLTAR ==========
async def voltar_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler universal para voltar ao menu principal"""
    await update.message.reply_text(
        "🏠 **MENU PRINCIPAL**\n\n"
        "O que você gostaria de fazer?",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

# ========== HANDLERS PARA SAÚDE FINANCEIRA ==========
async def ver_metricas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Ver Métricas Detalhadas"""
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    if not user_data:
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start.")
        return ConversationHandler.END
    
    expenses = db.get_monthly_expenses(user_id)
    total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
    total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
    total_geral = total_fixo + total_flexivel
    
    salario = user_data.get('salario_liquido', 0) or 0
    saldo = salario - total_geral
    percentual_gastos = (total_geral / salario * 100) if salario > 0 else 0
    
    # Análise de saúde financeira
    if percentual_gastos <= 60:
        status = "✅ SAUDÁVEL"
        cor = "🟢"
        recomendacao = "Parabéns! Suas finanças estão equilibradas."
    elif percentual_gastos <= 85:
        status = "⚠️ ATENÇÃO"
        cor = "🟡"
        recomendacao = "Revise seus gastos flexíveis."
    else:
        status = "🚨 CRÍTICO"
        cor = "🔴"
        recomendacao = "Priorize gastos essenciais e reveja seu orçamento."
    
    response = (
        f"📊 **MÉTRICAS DETALHADAS - {user_data.get('nickname', 'Usuário')}**\n\n"
        f"• 💵 **Salário Líquido:** R$ {salario:,.2f}\n"
        f"• 🏠 **Gastos Fixos:** R$ {total_fixo:,.2f}\n"
        f"• 🛍️ **Gastos Flexíveis:** R$ {total_flexivel:,.2f}\n"
        f"• 💰 **Total Gasto:** R$ {total_geral:,.2f}\n"
        f"• ⚖️ **Saldo Disponível:** R$ {saldo:,.2f}\n"
        f"• 📈 **Comprometimento:** {percentual_gastos:.1f}%\n\n"
        f"🏥 **SAÚDE FINANCEIRA:** {status} {cor}\n"
        f"💡 **Recomendação:** {recomendacao}"
    )
    
    await update.message.reply_text(response, reply_markup=saude_financeira_keyboard())
    return ConversationHandler.END

async def recomendacoes_ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler otimizado para Recomendações IA"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start.")
        return ConversationHandler.END
    
    # Mensagem imediata de confirmação
    processing_msg = await update.message.reply_text("⚡ Analisando seus dados...")
    
    try:
        # Timeout mais curto para a operação
        recomendacoes = await asyncio.wait_for(
            coach.finance_coach.get_personalized_recommendations(user_id),
            timeout=10.0  # 10 segundos de timeout
        )
        
        response = (
            f"🧠 **RECOMENDAÇÕES PERSONALIZADAS**\n\n"
            f"{recomendacoes}\n\n"
            f"💡 *Baseado na sua situação financeira atual*"
        )
        
        await processing_msg.edit_text(response)
        
    except asyncio.TimeoutError:
        await processing_msg.edit_text(
            "⚡ **RECOMENDAÇÕES RÁPIDAS**\n\n"
            "• 📊 **Controle Orçamentário**: Acompanhe receitas e despesas\n"
            "• 💰 **Reserva de Emergência**: Priorize 3-6 meses de gastos\n"
            "• 🎯 **Metas Claras**: Defina objetivos específicos\n"
            "• 📱 **Automatize Economias**: Transfira automaticamente para poupança\n"
            "• 🔍 **Revise Assinaturas**: Cancele serviços não essenciais\n\n"
            "💡 *Dicas práticas para melhorar suas finanças*",
            reply_markup=saude_financeira_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro nas recomendações: {e}")
        await processing_msg.edit_text(
            "🎯 **DICAS FINANCEIRAS ESSENCIAIS**\n\n"
            "1. **📊 Controle Orçamentário**: Acompanhe receitas e despesas\n"
            "2. **💰 Reserva de Emergência**: Priorize 3-6 meses de gastos\n"
            "3. **🎯 Metas Claras**: Defina objetivos específicos e prazos\n"
            "4. **📚 Educação Contínua**: Aprenda sobre investimentos básicos\n"
            "5. **💳 Evite Dívidas**: Fuja do cartão de crédito rotativo\n\n"
            "💪 Comece por uma dessas ações hoje!",
            reply_markup=saude_financeira_keyboard()
        )
    
    return ConversationHandler.END

async def analise_detalhada_ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler otimizado para Análise Detalhada com IA"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start.")
        return ConversationHandler.END
    
    processing_msg = await update.message.reply_text("📊 Gerando análise...")
    
    try:
        analise = await asyncio.wait_for(
            coach.finance_coach.get_detailed_analysis(user_id),
            timeout=12.0  # 12 segundos para análise
        )
        
        response = (
            f"📈 **ANÁLISE FINANCEIRA DETALHADA**\n\n"
            f"{analise}\n\n"
            f"💎 *Visão geral da sua situação financeira*"
        )
        
        await processing_msg.edit_text(response)
        
    except asyncio.TimeoutError:
        # Análise local rápida como fallback
        user_data = db.get_user_data(user_id)
        expenses = db.get_monthly_expenses(user_id)
        
        total_fixo = sum(sum(v.values()) for v in expenses['fixo'].values()) if expenses['fixo'] else 0
        total_flexivel = sum(sum(v.values()) for v in expenses['flexivel'].values()) if expenses['flexivel'] else 0
        total_geral = total_fixo + total_flexivel
        salario = user_data.get('salario_liquido', 0)
        percentual = (total_geral / salario * 100) if salario > 0 else 0
        
        if percentual <= 60:
            situacao = "🟢 SAUDÁVEL"
            acao = "Mantenha o controle e pense em investimentos"
        elif percentual <= 85:
            situacao = "🟡 ATENÇÃO"
            acao = "Revise gastos flexíveis e estabeleça limites"
        else:
            situacao = "🔴 CRÍTICO"
            acao = "Priorize redução de despesas essenciais"
        
        # Calcular distribuição
        if total_geral > 0:
            proporcao_fixo = (total_fixo / total_geral) * 100
            proporcao_flex = (total_flexivel / total_geral) * 100
        else:
            proporcao_fixo = proporcao_flex = 0
        
        await processing_msg.edit_text(
            f"📊 **ANÁLISE RÁPIDA DO MÊS**\n\n"
            f"• 💵 **Renda Mensal:** R$ {salario:,.2f}\n"
            f"• 🏠 **Gastos Fixos:** R$ {total_fixo:,.2f} ({proporcao_fixo:.1f}%)\n"
            f"• 🛍️ **Gastos Flexíveis:** R$ {total_flexivel:,.2f} ({proporcao_flex:.1f}%)\n"
            f"• 💰 **Total Gasto:** R$ {total_geral:,.2f}\n"
            f"• ⚖️ **Saldo:** R$ {salario - total_geral:,.2f}\n"
            f"• 📈 **Comprometido:** {percentual:.1f}%\n\n"
            f"🏥 **Situação**: {situacao}\n"
            f"🎯 **Ação Recomendada**: {acao}",
            reply_markup=saude_financeira_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await processing_msg.edit_text(
            "📈 **ANÁLISE BÁSICA**\n\n"
            "Para uma análise completa:\n"
            "• 📝 **Registre gastos** regularmente\n"
            "• 💰 **Mantenha salário** atualizado\n"
            "• 🏷️ **Use categorias** específicas\n"
            "• 📊 **Consulte resumo** mensalmente\n\n"
            "💡 **Dica**: Quanto mais dados, melhor a análise!",
            reply_markup=saude_financeira_keyboard()
        )
    
    return ConversationHandler.END

# ========== HANDLERS PARA EDUCAÇÃO FINANCEIRA ==========
async def educacao_financeira_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o menu de Educação Financeira"""
    await update.message.reply_text(
        "🎓 **EDUCAÇÃO FINANCEIRA**\n\n"
        "Aqui você pode aprender e melhorar seus conhecimentos:\n\n"
        "• 💡 **Dica do Dia** - Conselhos práticos e atualizados\n"
        "• 📚 **Glossário** - Conceitos financeiros explicados de forma simples\n"
        "• 🎓 **Módulos Educativos** - Cursos estruturados passo a passo\n\n"
        "✨ **Escolha uma opção para começar sua jornada de aprendizado!**",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def dica_do_dia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Dica do Dia"""
    dicas = [
        "💡 **Dica do Dia**: Estabeleça um orçamento mensal e acompanhe seus gastos regularmente!",
        "💡 **Dica do Dia**: Priorize a criação de uma reserva de emergência com 3-6 meses de despesas essenciais.",
        "💡 **Dica do Dia**: Evite dívidas com juros altos, como cartão de crédito rotativo e cheque especial.",
        "💡 **Dica do Dia**: Invista em educação financeira - é o melhor investimento que você pode fazer!",
        "💡 **Dica do Dia**: Automatize suas economias para não correr o risco de gastar o que deveria guardar.",
        "💡 **Dica do Dia**: Revise suas assinaturas e serviços mensalmente - cancele os não essenciais.",
        "💡 **Dica do Dia**: Estabeleça metas financeiras claras de curto, médio e longo prazo.",
        "💡 **Dica do Dia**: Aprenda sobre investimentos que se adequem ao seu perfil de risco e objetivos.",
        "💡 **Dica do Dia**: Compare preços antes de compras importantes - pequenas economias fazem diferença!",
        "💡 **Dica do Dia**: Separe pelo menos 10% da sua renda para investimentos antes de gastar com outras coisas.",
    ]
    
    import random
    dica = random.choice(dicas)
    
    await update.message.reply_text(
        f"{dica}\n\n"
        f"💭 **Reflexão**: Pequenas ações financeiras consistentes geram grandes resultados no longo prazo!",
        reply_markup=educacao_keyboard()
    )
    return ConversationHandler.END

async def glossario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Glossário Financeiro"""
    glossario = {
        "💰 Orçamento": "Planejamento de como você vai gastar seu dinheiro, considerando receitas e despesas.",
        "🛡️ Reserva de Emergência": "Valor guardado para situações imprevistas como desemprego ou problemas de saúde.",
        "📈 Juros Compostos": "Juros calculados sobre o valor inicial e também sobre os juros acumulados - o 'milagre' dos investimentos.",
        "🏦 CDB": "Certificado de Depósito Bancário - um tipo de investimento de renda fixa.",
        "🇧🇷 Tesouro Direto": "Programa do governo federal para venda de títulos públicos para pessoas físicas.",
        "📊 Ações": "Pedaços de uma empresa que são vendidos na bolsa de valores.",
        "💸 Dividendos": "Parte do lucro de uma empresa que é distribuída aos acionistas.",
        "📉 Inflação": "Aumento geral dos preços de bens e serviços ao longo do tempo.",
        "🏛️ Taxa Selic": "Taxa básica de juros da economia brasileira, definida pelo Banco Central.",
        "⚖️ Asset Allocation": "Distribuição do patrimônio em diferentes classes de investimentos.",
        "💳 Crédito Consignado": "Empréstimo com desconto direto na folha de pagamento, com juros menores.",
        "🏠 FGTS": "Fundo de Garantia do Tempo de Serviço - reserva financeira do trabalhador.",
        "👵 Previdência Privada": "Plano de aposentadoria complementar à previdência social.",
        "📋 Fluxo de Caixa": "Controle de entradas e saídas de dinheiro em um período.",
        "🎯 Meta Financeira": "Objetivo específico com valor e prazo definidos para alcançar algo."
    }
    
    # Dividir o glossário em partes para não exceder o limite do Telegram
    response = "📚 **GLOSSÁRIO FINANCEIRO**\n\n"
    response += "📖 **Conceitos Essenciais:**\n\n"
    
    items = list(glossario.items())
    for i, (termo, definicao) in enumerate(items[:8]):  # Primeira parte
        response += f"• **{termo}**: {definicao}\n\n"
    
    await update.message.reply_text(response, reply_markup=educacao_keyboard())
    
    # Segunda parte do glossário
    response2 = "📚 **GLOSSÁRIO FINANCEIRO**\n\n"
    response2 += "📖 **Mais Conceitos Importantes:**\n\n"
    
    for i, (termo, definicao) in enumerate(items[8:], 1):
        response2 += f"• **{termo}**: {definicao}\n\n"
    
    response2 += "💡 **Continue aprendendo! Conhecimento financeiro é liberdade.**"
    
    await update.message.reply_text(response2, reply_markup=educacao_keyboard())
    return ConversationHandler.END

async def modulos_educativos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Módulos Educativos"""
    modulos = [
        {
            "titulo": "📊 Fundamentos do Orçamento",
            "conteudo": "**Aprenda a criar e manter um orçamento pessoal eficaz:**\n\n"
                       "1. 📝 **Identifique suas receitas e despesas**\n"
                       "2. 🏷️ **Classifique gastos essenciais e não-essenciais**\n"
                       "3. 💰 **Estabeleça limites realistas**\n"
                       "4. 🔄 **Acompanhe e ajuste regularmente**\n\n"
                       "🎯 **Exercício prático**: Liste suas 5 maiores despesas do mês.\n\n"
                       "💡 **Dica**: Use o app para registrar todos os gastos!"
        },
        {
            "titulo": "💰 Como Criar sua Reserva de Emergência",
            "conteudo": "**Guia passo a passo para construir sua segurança financeira:**\n\n"
                       "• 🎯 **Quanto guardar**: 3-6 meses de despesas essenciais\n"
                       "• 🏦 **Onde aplicar**: Fundos conservadores e de fácil acesso\n"
                       "• ⚡ **Como priorizar**: Antes de pensar em outros investimentos\n"
                       "• 🚨 **Quando usar**: Apenas em situações reais de emergência\n\n"
                       "💪 **Meta**: Comece com 1 mês de despesas como primeiro objetivo.\n\n"
                       "🛡️ **Segurança primeiro, depois crescimento!**"
        },
        {
            "titulo": "🎯 Metas Financeiras Inteligentes",
            "conteudo": "**A metodologia SMART para suas metas:**\n\n"
                       "🎯 **S - Específica** (exatamente o que quer)\n"
                       "📏 **M - Mensurável** (valores e prazos claros)\n"
                       "🏆 **A - Atingível** (desafiadora mas realista)\n"
                       "❤️ **R - Relevante** (alinhada com seus valores)\n"
                       "⏰ **T - Temporal** (prazo definido)\n\n"
                       "📝 **Exemplo prático**: \n'Vou economizar R$ 5.000 para entrada de um apartamento em 12 meses'\n\n"
                       "✨ **Escreva sua meta SMART agora!**"
        },
        {
            "titulo": "📈 Introdução aos Investimentos",
            "conteudo": "**Primeiros passos no mundo dos investimentos:**\n\n"
                       "• 🏦 **Renda Fixa vs Renda Variável**\n"
                       "• 🥚 **Diversificação**: Não coloque todos os ovos na mesma cesta\n"
                       "• 👤 **Perfil de Investidor**: Conservador, Moderado ou Arrojado\n"
                       "• 📊 **Juros Compostos**: Seu maior aliado no longo prazo\n\n"
                       "🛡️ **Princípio fundamental**: Só invista no que você entende.\n\n"
                       "💡 **Comece pequeno e aprenda com o tempo!**"
        }
    ]
    
    # Criar keyboard inline com os módulos
    keyboard = []
    for i, modulo in enumerate(modulos, 1):
        keyboard.append([InlineKeyboardButton(modulo["titulo"], callback_data=f"modulo_{i}")])
    
    keyboard.append([InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="modulo_voltar")])
    
    await update.message.reply_text(
        "🎓 **MÓDULOS EDUCATIVOS**\n\n"
        "Escolha um módulo para aprender:\n\n"
        "📚 **Cada módulo contém:**\n"
        "• 📖 Conceitos fundamentais\n"
        "• 💼 Exemplos práticos\n"
        "• 🎯 Exercícios para aplicar\n"
        "• 💡 Dicas de implementação\n\n"
        "✨ **Aprenda no seu ritmo!**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def handle_modulos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos módulos educativos"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    modulos = [
        {
            "titulo": "📊 Fundamentos do Orçamento",
            "conteudo": "**Aprenda a criar e manter um orçamento pessoal eficaz:**\n\n"
                       "1. 📝 **Identifique suas receitas e despesas**\n"
                       "2. 🏷️ **Classifique gastos essenciais e não-essenciais**\n"
                       "3. 💰 **Estabeleça limites realistas**\n"
                       "4. 🔄 **Acompanhe e ajuste regularmente**\n\n"
                       "🎯 **Exercício prático**: Liste suas 5 maiores despesas do mês.\n\n"
                       "💡 **Dica**: Use o app para registrar todos os gastos!"
        },
        {
            "titulo": "💰 Como Criar sua Reserva de Emergência",
            "conteudo": "**Guia passo a passo para construir sua segurança financeira:**\n\n"
                       "• 🎯 **Quanto guardar**: 3-6 meses de despesas essenciais\n"
                       "• 🏦 **Onde aplicar**: Fundos conservadores e de fácil acesso\n"
                       "• ⚡ **Como priorizar**: Antes de pensar em outros investimentos\n"
                       "• 🚨 **Quando usar**: Apenas em situações reais de emergência\n\n"
                       "💪 **Meta**: Comece com 1 mês de despesas como primeiro objetivo.\n\n"
                       "🛡️ **Segurança primeiro, depois crescimento!**"
        },
        {
            "titulo": "🎯 Metas Financeiras Inteligentes",
            "conteudo": "**A metodologia SMART para suas metas:**\n\n"
                       "🎯 **S - Específica** (exatamente o que quer)\n"
                       "📏 **M - Mensurável** (valores e prazos claros)\n"
                       "🏆 **A - Atingível** (desafiadora mas realista)\n"
                       "❤️ **R - Relevante** (alinhada com seus valores)\n"
                       "⏰ **T - Temporal** (prazo definido)\n\n"
                       "📝 **Exemplo prático**: \n'Vou economizar R$ 5.000 para entrada de um apartamento em 12 meses'\n\n"
                       "✨ **Escreva sua meta SMART agora!**"
        },
        {
            "titulo": "📈 Introdução aos Investimentos",
            "conteudo": "**Primeiros passos no mundo dos investimentos:**\n\n"
                       "• 🏦 **Renda Fixa vs Renda Variável**\n"
                       "• 🥚 **Diversificação**: Não coloque todos os ovos na mesma cesta\n"
                       "• 👤 **Perfil de Investidor**: Conservador, Moderado ou Arrojado\n"
                       "• 📊 **Juros Compostos**: Seu maior aliado no longo prazo\n\n"
                       "🛡️ **Princípio fundamental**: Só invista no que você entende.\n\n"
                       "💡 **Comece pequeno e aprenda com o tempo!**"
        }
    ]
    
    if data == "modulo_voltar":
        await query.edit_message_text("🏠 Voltando ao Menu Principal")
        await context.bot.send_message(
            query.from_user.id,
            "🎓 EDUCAÇÃO FINANCEIRA",
            reply_markup=educacao_keyboard()
        )
        return ConversationHandler.END
    
    if data.startswith("modulo_"):
        try:
            modulo_index = int(data.split("_")[1]) - 1
            if 0 <= modulo_index < len(modulos):
                modulo = modulos[modulo_index]
                
                keyboard = [
                    [InlineKeyboardButton("📚 Ver Outros Módulos", callback_data="modulos_lista")],
                    [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="modulo_voltar")]
                ]
                
                await query.edit_message_text(
                    f"**{modulo['titulo']}**\n\n{modulo['conteudo']}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Erro ao carregar módulo. Tente novamente.")

    elif data == "modulos_lista":
        # Recriar a lista de módulos
        keyboard = []
        for i, modulo in enumerate(modulos, 1):
            keyboard.append([InlineKeyboardButton(modulo["titulo"], callback_data=f"modulo_{i}")])
        keyboard.append([InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="modulo_voltar")])
        
        await query.edit_message_text(
            "🎓 **MÓDULOS EDUCATIVOS**\n\nEscolha um módulo para aprender:\n\n"
            "✨ **Aprenda no seu ritmo!**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return ConversationHandler.END

# ========== HANDLERS DE MENU ==========
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'Voltar ao Menu' in text:
        return await voltar_menu_handler(update, context)
    elif 'Registrar Gastos' in text:
        return await adicionar_gastos_handler(update, context)
    elif 'Meu Extrato' in text:  # ALTERADO: Meu Resumo → Meu Extrato
        return await extrato_gastos_handler(update, context)
    elif 'Saúde Financeira' in text:
        return await saude_financeira_handler(update, context)
    elif 'Educação Financeira' in text:
        return await educacao_financeira_handler(update, context)
    elif 'Objetivos' in text:
        return await objetivos_handler(update, context)
    elif 'Configurações' in text:
        return await config_handler(update, context)
    elif 'Ajuda' in text:
        return await ajuda_handler(update, context)
    
    # HANDLERS PARA SAÚDE FINANCEIRA
    elif 'Ver Métricas Detalhadas' in text:
        return await ver_metricas_handler(update, context)
    elif 'Recomendações IA' in text:
        return await recomendacoes_ia_handler(update, context)
    elif 'Análise Detalhada com IA' in text:
        return await analise_detalhada_ia_handler(update, context)
    
    # HANDLERS PARA OBJETIVOS
    elif 'Adicionar Objetivo' in text:
        return await add_goal_handler(update, context)
    elif 'Atualizar Progresso' in text:
        return await update_goal_progress_handler(update, context)
    elif 'Excluir Objetivo' in text:
        return await delete_goal_handler(update, context)
    elif 'Meus Objetivos' in text:
        return await meus_objetivos_handler(update, context)
    
    # HANDLERS PARA EDUCAÇÃO FINANCEIRA
    elif 'Dica do Dia' in text:
        return await dica_do_dia_handler(update, context)
    elif 'Glossário' in text:
        return await glossario_handler(update, context)
    elif 'Módulos Educativos' in text:
        return await modulos_educativos_handler(update, context)
    
    # HANDLERS PARA CONFIGURAÇÕES
    elif 'Editar Perfil' in text:
        return await edit_profile_handler(update, context)
    elif 'Alterar Salário' in text:
        return await edit_salary_handler(update, context)
    elif 'Redefinir' in text:
        return await reset_data_handler(update, context)
    
    # HANDLERS PARA GASTOS
    elif 'Gastos Fixos' in text:
        # Iniciar fluxo de gastos fixos
        context.user_data['user_id'] = update.effective_user.id
        context.user_data['tipo_gasto'] = 'fixo'
        await update.message.reply_text(
            "🏠 CATEGORIAS DE GASTOS FIXOS\n\nSelecione a categoria:",
            reply_markup=categorias_fixas_keyboard()
        )
        return CATEGORIA_FIXA
        
    elif 'Gastos Flexíveis' in text:
        # Iniciar fluxo de gastos flexíveis
        context.user_data['user_id'] = update.effective_user.id
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
        return GASTOS_MES
        
    elif 'Suas Categorias' in text:
        return await suas_categorias_handler(update, context)
    
    else:
        await update.message.reply_text(
            "❌ Comando não reconhecido.\n\n"
            "💡 Use os botões do menu ou digite /ajuda para ver todas as opções disponíveis.",
            reply_markup=main_keyboard()
        )
    
    return ConversationHandler.END

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 **MENU PRINCIPAL**\n\n"
        "Escolha uma opção para começar:",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

async def ajuda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **EDU - SEU ASSISTENTE FINANCEIRO PESSOAL**

🎯 **PRINCIPAIS FUNCIONALIDADES:**

💸 **REGISTRO DE GASTOS**
• 🏠 Gastos Fixos - Despesas regulares (aluguel, contas)
• 🛍️ Gastos Flexíveis - Despesas variáveis (alimentação, lazer)
• 📅 Gastos do Mês - Estatísticas mensais detalhadas
• 📂 Suas Categorias - Gerencie categorias personalizadas

📊 **ANÁLISE FINANCEIRA**
• 📈 Saúde Financeira - Métricas e indicadores
• 🧠 Recomendações IA - Conselhos personalizados
• 🔍 Análise Detalhada - Visão completa da sua situação

🎯 **METAS E OBJETIVOS**
• Adicionar Objetivo - Defina novas metas
• Atualizar Progresso - Acompanhe evolução
• Meus Objetivos - Veja todas as metas
• Excluir Objetivo - Remova objetivos

🎓 **EDUCAÇÃO FINANCEIRA**
• 💡 Dica do Dia - Conselhos práticos diários
• 📚 Glossário - Conceitos explicados
• 🎓 Módulos Educativos - Cursos estruturados

⚙️ **CONFIGURAÇÕES**
• ✏️ Editar Perfil - Alterar nome
• 💰 Alterar Salário - Atualizar renda
• 🔄 Redefinir - Limpar todos os dados

📱 **COMANDOS RÁPIDOS:**
/start - Iniciar o bot
/menu - Mostrar menu principal
/extrato - Ver extrato detalhado  # ALTERADO: /resumo → /extrato
/ajuda - Mostrar esta ajuda

💡 **DICAS IMPORTANTES:**
• ✅ Registre TODOS os gastos para análise precisa
• 🏷️ Use categorias específicas para melhor organização
• 📊 Consulte a saúde financeira semanalmente
• 🎯 Estabeleça metas realistas e alcançáveis
• 🔄 Atualize seu salário quando houver mudanças

🌟 **Lembre-se:** Pequenas ações consistentes geram grandes resultados financeiros!
    """
    await update.message.reply_text(help_text, reply_markup=main_keyboard())
    return ConversationHandler.END

async def gastos_mes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para Gastos do Mês - Versão corrigida"""
    await update.message.reply_text(
        "📅 **SELECIONE O MÊS**\n\nEscolha o mês para ver as estatísticas:",
        reply_markup=MonthYearCalendar.create_month_year_calendar()
    )
    return GASTOS_MES
    
# ========== UTILITÁRIOS ==========
def parse_date_input(date_text: str):
    if not isinstance(date_text, str):
        return None
        
    s = date_text.strip().lower()
    if s == 'hoje':
        return datetime.datetime.now().strftime('%d/%m/%Y')
        
    cleaned = re.sub(r'[^\d/]', '', date_text.strip())
    
    if len(cleaned) == 8 and cleaned.isdigit():
        day, month, year = cleaned[0:2], cleaned[2:4], cleaned[4:8]
        candidate = f"{day}/{month}/{year}"
        return candidate if validate_date(candidate) else None
        
    if len(cleaned) == 10 and cleaned.count('/') == 2:
        parts = cleaned.split('/')
        candidate = f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"
        return candidate if validate_date(candidate) else None
        
    return None

def validate_date(date_str: str):
    try:
        d, m, y = map(int, date_str.split('/'))
        datetime.datetime(y, m, d)
        return True
    except Exception:
        return False

# ========== HANDLERS PARA CONVERSATION ==========
# Handlers que são apenas aliases para o conversation handler
resumo_gastos_handler = resumo_gastos_handler

# Cache simples em memória
_user_data_cache = {}
_cache_timeout = 300  # 5 minutos

def get_cached_user_data(user_id):
    """Obtém dados do usuário com cache"""
    now = datetime.datetime.now().timestamp()
    if user_id in _user_data_cache:
        data, timestamp = _user_data_cache[user_id]
        if now - timestamp < _cache_timeout:
            return data
    
    # Se não está em cache ou expirou, busca no banco
    data = db.get_user_data(user_id)
    _user_data_cache[user_id] = (data, now)
    return data

def get_cached_monthly_expenses(user_id):
    """Obtém gastos mensais com cache"""
    now = datetime.datetime.now().timestamp()
    cache_key = f"expenses_{user_id}"
    
    if cache_key in _user_data_cache:
        data, timestamp = _user_data_cache[cache_key]
        if now - timestamp < _cache_timeout:
            return data
    
    data = db.get_monthly_expenses(user_id)
    _user_data_cache[cache_key] = (data, now)
    return data