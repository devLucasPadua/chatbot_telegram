from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import database as db
import ai_coach
import datetime
import re

# Estados do fluxo - CORRIGIDOS
GET_NAME, GET_SALARY, GET_EXPENSE_TYPE, GET_FIXED_SUBCATEGORY, GET_FLEXIBLE_SUBCATEGORY, GET_NEW_SUBCATEGORY, GET_EXPENSE_VALUE, GET_EXPENSE_DATE, CONTINUE_ADDING, SHOW_SUMMARY, FINANCIAL_HEALTH = range(11)

# Categorias padrão
FIXED_CATEGORIES = ["Moradia", "Serviços", "Educação", "Transporte", "Seguros", "Assinaturas", "Impostos"]
FLEXIBLE_CATEGORIES = ["Alimentação", "Lazer", "Vestuário", "Cuidados", "Manutenção", "Presentes"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo RÁPIDO"""
    user_id = update.effective_user.id
    context.user_data.clear()
    
    # Resposta RÁPIDA sem IA para primeira mensagem
    await update.message.reply_text("👋 Olá! Sou o Edu, seu assistente financeiro.", reply_markup=ReplyKeyboardRemove())
    
    # Vai direto para pedir o nome
    await update.message.reply_text("📝 Qual o seu nome?")
    return GET_NAME

async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o nome RAPIDAMENTE"""
    name = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not name:
        await update.message.reply_text("❌ Digite um nome válido.")
        return GET_NAME
    
    db.add_user(user_id, name)
    context.user_data['name'] = name
    
    # Resposta RÁPIDA sem IA
    await update.message.reply_text(f"👋 Boas-vindas, {name}! Vou ajudar com seu orçamento mensal.")
    return await get_salary(update, context)

async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede salário com resposta RÁPIDA"""
    name = context.user_data.get('name', '')
    await update.message.reply_text(f"💰 {name}, qual seu salário líquido?\nExemplo: 1000,00")
    return GET_SALARY

async def process_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa salário RAPIDAMENTE"""
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        salary = float(salary_text)
        
        if salary <= 0:
            await update.message.reply_text("❌ Valor deve ser > 0. Tente:")
            return GET_SALARY
        
        user_id = update.effective_user.id
        db.update_user_salary(user_id, salary)
        context.user_data['salary'] = salary
        
        # Educação sobre gastos - resposta RÁPIDA
        name = context.user_data.get('name', '')
        await update.message.reply_text(
            f"💡 {name}, vamos entender gastos:\n\n"
            f"🏠 **FIXOS**: Aluguel, internet, escola (valores constantes)\n"
            f"🛍️ **FLEXÍVEIS**: Mercado, lazer, roupas (valores variam)\n\n"
            f"Agora vamos classificar seus gastos...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return await get_expense_type(update, context)
        
    except ValueError:
        await update.message.reply_text("❌ Digite apenas números. Ex: 1500,00")
        return GET_SALARY

async def get_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede tipo de gasto COM BOTÕES"""
    keyboard = [['🏠 FIXO', '🛍️ FLEXÍVEL']]
    await update.message.reply_text(
        "📊 Qual tipo de gasto?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GET_EXPENSE_TYPE

async def process_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa tipo de gasto RAPIDAMENTE"""
    text = update.message.text.upper()
    
    if 'FIXO' in text:
        context.user_data['current_expense_type'] = 'fixed'
        return await get_fixed_subcategory(update, context)
    elif 'FLEX' in text:
        context.user_data['current_expense_type'] = 'flexible'
        return await get_flexible_subcategory(update, context)
    else:
        keyboard = [['🏠 FIXO', '🛍️ FLEXÍVEL']]
        await update.message.reply_text(
            "❌ Escolha uma opção:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return GET_EXPENSE_TYPE

async def get_fixed_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra categorias fixas COM BOTÕES"""
    categories = FIXED_CATEGORIES + ['➕ NOVA']
    keyboard = [categories[i:i+3] for i in range(0, len(categories), 3)]
    
    await update.message.reply_text(
        "🏠 Escolha a categoria FIXA:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GET_FIXED_SUBCATEGORY

async def get_flexible_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra categorias flexíveis COM BOTÕES"""
    categories = FLEXIBLE_CATEGORIES + ['➕ NOVA']
    keyboard = [categories[i:i+3] for i in range(0, len(categories), 3)]
    
    await update.message.reply_text(
        "🛍️ Escolha a categoria FLEXÍVEL:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GET_FLEXIBLE_SUBCATEGORY

async def process_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa categoria RAPIDAMENTE"""
    subcategory = update.message.text.strip()
    
    if 'NOVA' in subcategory.upper():
        await update.message.reply_text("📝 Qual o nome da nova categoria?", reply_markup=ReplyKeyboardRemove())
        return GET_NEW_SUBCATEGORY
    
    context.user_data['current_subcategory'] = subcategory
    return await get_expense_value(update, context)

async def process_new_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa nova categoria RAPIDAMENTE"""
    new_category = update.message.text.strip()
    
    if not new_category:
        await update.message.reply_text("❌ Digite um nome válido.")
        return GET_NEW_SUBCATEGORY
    
    context.user_data['current_subcategory'] = new_category
    return await get_expense_value(update, context)

async def get_expense_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede valor RAPIDAMENTE"""
    await update.message.reply_text("💵 Valor do gasto?\nEx: 150,00")
    return GET_EXPENSE_VALUE

async def process_expense_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa valor RAPIDAMENTE"""
    try:
        value_text = update.message.text.replace(',', '.').strip()
        value = float(value_text)
        
        if value <= 0:
            await update.message.reply_text("❌ Valor deve ser > 0. Tente:")
            return GET_EXPENSE_VALUE
        
        context.user_data['current_value'] = value
        return await get_expense_date(update, context)
        
    except ValueError:
        await update.message.reply_text("❌ Digite apenas números. Ex: 150,00")
        return GET_EXPENSE_VALUE

async def get_expense_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede data COM BOTÕES"""
    keyboard = [['📅 HOJE', '📅 ONTEM'], ['📅 OUTRA DATA']]
    await update.message.reply_text(
        "📅 Data do gasto?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GET_EXPENSE_DATE

async def process_expense_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa data RAPIDAMENTE"""
    date_choice = update.message.text.upper()
    
    if 'HOJE' in date_choice:
        date = datetime.datetime.now().strftime('%d/%m/%Y')
    elif 'ONTEM' in date_choice:
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d/%m/%Y')
    elif 'OUTRA' in date_choice:
        await update.message.reply_text("📅 Digite a data (DD/MM/AAAA):", reply_markup=ReplyKeyboardRemove())
        context.user_data['awaiting_specific_date'] = True
        return GET_EXPENSE_DATE
    else:
        if context.user_data.get('awaiting_specific_date'):
            date = parse_date_input(date_choice)
            if not date:
                await update.message.reply_text("❌ Formato inválido. Use DD/MM/AAAA:")
                return GET_EXPENSE_DATE
            context.user_data['awaiting_specific_date'] = False
        else:
            keyboard = [['📅 HOJE', '📅 ONTEM'], ['📅 OUTRA DATA']]
            await update.message.reply_text(
                "❌ Escolha uma opção:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return GET_EXPENSE_DATE
    
    # Salva transação RAPIDAMENTE
    user_id = update.effective_user.id
    expense_type = context.user_data.get('current_expense_type')
    subcategory = context.user_data.get('current_subcategory')
    value = context.user_data.get('current_value')
    
    db.add_transaction(user_id, expense_type, expense_type, subcategory, value, f"{subcategory}", date)
    
    await update.message.reply_text(
        f"✅ **Adicionado!**\n"
        f"Tipo: {expense_type.upper()}\n"
        f"Categoria: {subcategory}\n"
        f"Valor: R$ {value:,.2f}\n"
        f"Data: {date}",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return await continue_adding(update, context)

async def continue_adding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pergunta se continua COM BOTÕES"""
    keyboard = [['✅ SIM', '❌ NÃO']]
    await update.message.reply_text(
        "🔄 Adicionar mais gastos?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CONTINUE_ADDING

async def process_continue_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa escolha RAPIDAMENTE"""
    choice = update.message.text.upper()
    
    if 'SIM' in choice:
        return await get_expense_type(update, context)
    elif 'NÃO' in choice or 'NAO' in choice:
        return await show_summary(update, context)
    else:
        keyboard = [['✅ SIM', '❌ NÃO']]
        await update.message.reply_text(
            "❌ Escolha SIM ou NÃO:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CONTINUE_ADDING

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra resumo RAPIDAMENTE"""
    user_id = update.effective_user.id
    summary = db.get_transactions_summary(user_id)
    
    # Resumo DIRETO
    summary_text = "📊 **RESUMO DOS GASTOS**\n\n"
    
    if summary['fixed_expenses']:
        summary_text += "🏠 **FIXOS:**\n"
        for cat, val in summary['fixed_expenses'].items():
            summary_text += f"• {cat}: R$ {val:,.2f}\n"
        summary_text += f"**Total: R$ {summary['total_fixed']:,.2f}**\n\n"
    
    if summary['flexible_expenses']:
        summary_text += "🛍️ **FLEXÍVEIS:**\n"
        for cat, val in summary['flexible_expenses'].items():
            summary_text += f"• {cat}: R$ {val:,.2f}\n"
        summary_text += f"**Total: R$ {summary['total_flexible']:,.2f}**\n\n"
    
    summary_text += f"💰 **TOTAL GERAL: R$ {summary['total_expenses']:,.2f}**"
    
    await update.message.reply_text(summary_text)
    
    # Pergunta COM BOTÕES
    keyboard = [['📈 1 - ANALISAR SAÚDE', '❌ 2 - ENCERRAR']]
    await update.message.reply_text(
        "O que deseja fazer?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    
    return SHOW_SUMMARY

async def process_summary_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa escolha RAPIDAMENTE"""
    choice = update.message.text.upper()
    
    if 'ANALISAR' in choice or '1' in choice:
        return await financial_health(update, context)
    elif 'ENCERRAR' in choice or '2' in choice:
        return await end_conversation(update, context)
    else:
        keyboard = [['📈 1 - ANALISAR SAÚDE', '❌ 2 - ENCERRAR']]
        await update.message.reply_text(
            "❌ Escolha uma opção:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SHOW_SUMMARY

async def financial_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Análise RÁPIDA"""
    user_id = update.effective_user.id
    name = context.user_data.get('name', '')
    salary = context.user_data.get('salary', 0)
    summary = db.get_transactions_summary(user_id)
    
    # Análise DIRETA
    if salary > 0:
        spending = summary['total_expenses']
        percentage = (spending / salary) * 100
        available = salary * 0.65 - spending
        
        analysis = f"""
📈 **SAÚDE FINANCEIRA - {name}**

💰 Salário: R$ {salary:,.2f}
💸 Gasto total: R$ {spending:,.2f}
📊 {percentage:.1f}% do salário

💎 **STATUS:** {'✅ SAUDÁVEL' if percentage <= 65 else '⚠️ ATENÇÃO'}

💡 **RECOMENDAÇÃO:** {'Mantenha!' if percentage <= 65 else f'Economize R$ {available:,.2f}'}
"""
    else:
        analysis = "❌ Salário não informado para análise."
    
    await update.message.reply_text(analysis, reply_markup=main_keyboard())
    return ConversationHandler.END

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Encerra RAPIDAMENTE"""
    name = context.user_data.get('name', '')
    await update.message.reply_text(
        f"👋 Até mais, {name}! Volte sempre.",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela RAPIDAMENTE"""
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelado. Use /start para começar novamente.", reply_markup=main_keyboard())
    return ConversationHandler.END

# NOVOS COMANDOS PARA O MENU
async def extrato_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /extrato - mostra extrato completo"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return
    
    transactions = db.get_monthly_transactions(user_id)
    
    if not transactions:
        await update.message.reply_text("📭 Nenhuma transação registrada ainda.\nUse /start para adicionar gastos.")
        return
    
    extrato_text = "📋 **EXTRATO COMPLETO**\n\n"
    
    for i, trans in enumerate(transactions, 1):
        tipo, categoria, subcategoria, valor, data, descricao = trans
        emoji = "🏠" if tipo == 'fixed' else "🛍️"
        tipo_text = "FIXO" if tipo == 'fixed' else "FLEX"
        
        extrato_text += f"{emoji} **{tipo_text}** - {data}\n"
        extrato_text += f"   {subcategoria}: R$ {valor:,.2f}\n\n"
    
    # Adiciona totais
    summary = db.get_transactions_summary(user_id)
    extrato_text += f"💰 **TOTAL: R$ {summary['total_expenses']:,.2f}**"
    
    await update.message.reply_text(extrato_text)

async def resumo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /resumo - mostra resumo financeiro"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Use /start para se cadastrar primeiro.")
        return
    
    user_data = db.get_user_data(user_id)
    summary = db.get_transactions_summary(user_id)
    
    if not summary['total_expenses']:
        await update.message.reply_text("📭 Nenhum gasto registrado ainda.\nUse /start para adicionar gastos.")
        return
    
    resumo_text = "📈 **RESUMO FINANCEIRO**\n\n"
    
    if user_data.get('salary', 0) > 0:
        salary = user_data['salary']
        spending = summary['total_expenses']
        percentage = (spending / salary) * 100
        
        resumo_text += f"💰 **Salário:** R$ {salary:,.2f}\n"
        resumo_text += f"💸 **Gastos totais:** R$ {spending:,.2f}\n"
        resumo_text += f"📊 **Percentual:** {percentage:.1f}%\n\n"
        
        if summary['fixed_expenses']:
            resumo_text += "🏠 **Gastos Fixos:**\n"
            for cat, val in summary['fixed_expenses'].items():
                resumo_text += f"• {cat}: R$ {val:,.2f}\n"
            resumo_text += f"**Total Fixos: R$ {summary['total_fixed']:,.2f}**\n\n"
        
        if summary['flexible_expenses']:
            resumo_text += "🛍️ **Gastos Flexíveis:**\n"
            for cat, val in summary['flexible_expenses'].items():
                resumo_text += f"• {cat}: R$ {val:,.2f}\n"
            resumo_text += f"**Total Flexíveis: R$ {summary['total_flexible']:,.2f}**\n\n"
        
        resumo_text += f"💎 **Status:** {'✅ Saudável' if percentage <= 65 else '⚠️ Atenção'}"
    else:
        resumo_text += "❌ Salário não informado. Use /start para configurar."
    
    await update.message.reply_text(resumo_text)

async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ajuda - mostra ajuda"""
    ajuda_text = """
🤖 **COMANDOS DISPONÍVEIS:**

🎯 /start - Iniciar conversa com o Edu
📊 /extrato - Ver extrato completo de gastos
📈 /resumo - Ver resumo financeiro detalhado
❌ /cancel - Cancelar operação atual
ℹ️ /ajuda - Mostrar esta ajuda

💡 **DICAS:**
• Use /start para cadastrar gastos
• Classifique gastos como FIXOS ou FLEXÍVEIS
• Monitore sua saúde financeira
• Economize pelo menos 35% do seu salário
"""
    await update.message.reply_text(ajuda_text)

def main_keyboard():
    return ReplyKeyboardMarkup([['/start', '/extrato'], ['/resumo', '/ajuda']], resize_keyboard=True)

def parse_date_input(date_text):
    date_text = re.sub(r'[^\d/]', '', date_text.strip())
    
    if len(date_text) == 8 and date_text.isdigit():
        return f"{date_text[0:2]}/{date_text[2:4]}/{date_text[4:8]}"
    elif len(date_text) == 10 and date_text.count('/') == 2:
        parts = date_text.split('/')
        if len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
            return date_text
    return None