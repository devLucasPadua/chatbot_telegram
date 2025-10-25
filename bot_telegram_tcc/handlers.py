from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
import database as db
import datetime
import calendar
import logging
import re

# Estados da conversa
GET_NAME, MAIN_MENU, GET_SALARY, GET_SALARY_DATE, GET_SALARY_DESC, GET_EXPENSE, GET_EXPENSE_DATE, GET_EXPENSE_DESC, GET_CREDIT, GET_CREDIT_DATE, GET_CREDIT_DESC, CONFIRM_DATE = range(12)

def main_keyboard():
    """Teclado principal do bot"""
    keyboard = [
        ['💰 Inserir Salário', '💸 Inserir Gasto'],
        ['💳 Inserir Crédito', '📊 Extrato']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Escolha uma opção...")

def date_confirmation_keyboard():
    """Teclado para confirmação de data"""
    keyboard = [
        ['✅ Sim, está correto', '❌ Não, corrigir']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def generate_calendar_inline(view='month', year=None, month=None):
    """Gera calendário com teclado inline para navegação silenciosa"""
    now = datetime.datetime.now()
    
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # Configurar calendário para começar no domingo (padrão brasileiro)
    cal = calendar.Calendar(firstweekday=6)  # 6 = domingo
    
    keyboard = []
    
    if view == 'month':
        # Visualização de dias do mês
        month_name = calendar.month_name[month]
        header = f"📅 {month_name} {year}"
        
        # Gerar o calendário do mês começando no domingo
        month_days = cal.monthdayscalendar(year, month)
        
        # Header com navegação
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"nav_month_{year}_{month-1}"),
            InlineKeyboardButton(header, callback_data=f"nav_year_{year}"),
            InlineKeyboardButton("▶️", callback_data=f"nav_month_{year}_{month+1}")
        ])
        
        # Dias da semana
        week_days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in week_days])
        
        # Dias do mês
        for week in month_days:
            week_buttons = []
            for day in week:
                if day == 0:
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    week_buttons.append(InlineKeyboardButton(
                        str(day), 
                        callback_data=f"select_{year}_{month}_{day}"
                    ))
            keyboard.append(week_buttons)
        
        # Botão Hoje
        keyboard.append([
            InlineKeyboardButton("✅ Hoje", callback_data="select_today")
        ])
        
        # Botão para digitar data manualmente
        keyboard.append([
            InlineKeyboardButton("⌨️ Digitar Data", callback_data="manual_date_input")
        ])
        
    elif view == 'year':
        # Visualização de meses do ano
        header = f"📅 {year}"
        
        # Header com navegação
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"nav_year_{year-1}"),
            InlineKeyboardButton(header, callback_data=f"nav_decade_{year}"),
            InlineKeyboardButton("▶️", callback_data=f"nav_year_{year+1}")
        ])
        
        # Organizar meses em 4 linhas de 3
        months = list(calendar.month_name)[1:]
        for i in range(0, 12, 3):
            row = []
            for j in range(3):
                if i + j < 12:
                    month_num = i + j + 1
                    month_abbr = calendar.month_abbr[month_num]
                    row.append(InlineKeyboardButton(
                        month_abbr, 
                        callback_data=f"nav_month_{year}_{month_num}"
                    ))
            keyboard.append(row)
        
    elif view == 'decade':
        # Visualização de anos (década)
        start_year = (year // 10) * 10
        end_year = start_year + 9
        header = f"📅 {start_year}-{end_year}"
        
        # Header com navegação
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"nav_decade_{start_year-10}"),
            InlineKeyboardButton(header, callback_data=f"nav_year_{year}"),
            InlineKeyboardButton("▶️", callback_data=f"nav_decade_{start_year+10}")
        ])
        
        # Organizar anos em 4 colunas
        years = list(range(start_year, start_year + 12))
        for i in range(0, 12, 4):
            row = []
            for j in range(4):
                if i + j < len(years):
                    row.append(InlineKeyboardButton(
                        str(years[i + j]), 
                        callback_data=f"nav_year_{years[i + j]}"
                    ))
            keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def parse_date_input(date_text):
    """Converte entrada de data para formato DD/MM/AAAA"""
    # Remove espaços e caracteres especiais
    date_text = re.sub(r'[^\d/]', '', date_text.strip())
    
    # Se tem 8 dígitos (sem barras)
    if len(date_text) == 8 and date_text.isdigit():
        day = date_text[0:2]
        month = date_text[2:4]
        year = date_text[4:8]
        return f"{day}/{month}/{year}"
    
    # Se tem 10 caracteres com barras
    elif len(date_text) == 10 and date_text.count('/') == 2:
        parts = date_text.split('/')
        if len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
            return date_text
    
    return None

def validate_date(date_str):
    """Valida se a data é válida"""
    try:
        day, month, year = map(int, date_str.split('/'))
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

async def handle_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks do calendário inline"""
    query = update.callback_query
    await query.answer()  # Responde ao callback para remover o loading
    
    data = query.data
    user_id = query.from_user.id
    
    # Determina qual tipo de transação estamos processando baseado no user_data
    transaction_type = context.user_data.get('current_transaction_type')
    
    if data == "ignore":
        return None
    
    elif data == "select_today":
        # Seleciona data atual
        date = datetime.datetime.now().strftime('%d/%m/%Y')
        return await process_date_selection(context, transaction_type, date, query)
    
    elif data == "manual_date_input":
        # Solicita entrada manual de data
        await query.edit_message_text("📅 **Digite a data manualmente**")
        await query.message.reply_text(
            "⌨️ **Digite a data**\n\n"
            "Formato: DD/MM/AAAA\n"
            "Exemplos:\n"
            "• 15/03/2024\n"
            "• 15032024\n"
            "• 05122023\n\n"
            "Ou use:\n"
            "• 'hoje' para data atual\n"
            "• 'ontem' para data de ontem"
        )
        # Retorna o estado atual (GET_SALARY_DATE, GET_EXPENSE_DATE, ou GET_CREDIT_DATE)
        # que agora também aceita entrada manual via MessageHandler
        return None
    
    elif data.startswith("select_"):
        # Seleciona uma data específica
        parts = data.split('_')
        if len(parts) == 4:
            year = int(parts[1])
            month = int(parts[2])
            day = int(parts[3])
            date = f"{day:02d}/{month:02d}/{year}"
            return await process_date_selection(context, transaction_type, date, query)
    
    elif data.startswith("nav_"):
        # Navegação entre visualizações
        parts = data.split('_')
        nav_type = parts[1]
        
        if nav_type == "month":
            year = int(parts[2])
            month = int(parts[3])
            # Ajusta se mês for 0 ou 13
            if month == 0:
                month = 12
                year -= 1
            elif month == 13:
                month = 1
                year += 1
            
            await query.edit_message_reply_markup(
                reply_markup=generate_calendar_inline('month', year, month)
            )
        
        elif nav_type == "year":
            year = int(parts[2])
            await query.edit_message_reply_markup(
                reply_markup=generate_calendar_inline('year', year)
            )
        
        elif nav_type == "decade":
            year = int(parts[2])
            await query.edit_message_reply_markup(
                reply_markup=generate_calendar_inline('decade', year)
            )
    
    return None

async def process_date_selection(context: ContextTypes.DEFAULT_TYPE, transaction_type: str, date: str, query=None):
    """Processa a seleção final da data e pede confirmação"""
    # Armazena a data temporariamente
    context.user_data['tentative_date'] = date
    context.user_data['current_transaction_type'] = transaction_type
    
    if query:
        await query.edit_message_text(f"📅 Data selecionada: {date}")
        await query.message.reply_text(
            f"**Confirme a data:**\n\n"
            f"📅 {date}\n\n"
            f"Esta é a data correta?",
            reply_markup=date_confirmation_keyboard()
        )
    else:
        # Para entrada manual
        await context.bot.send_message(
            chat_id=context._chat_id,
            text=f"**Confirme a data:**\n\n"
                 f"📅 {date}\n\n"
                 f"Esta é a data correta?",
            reply_markup=date_confirmation_keyboard()
        )
    
    return CONFIRM_DATE

async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada manual de data"""
    text = update.message.text.strip().lower()
    transaction_type = context.user_data.get('current_transaction_type')
    
    # Palavras especiais
    if text == 'hoje':
        date = datetime.datetime.now().strftime('%d/%m/%Y')
    elif text == 'ontem':
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d/%m/%Y')
    else:
        # Tenta parsear a data
        date = parse_date_input(text)
        if not date:
            await update.message.reply_text(
                "❌ **Formato de data inválido!**\n\n"
                "Por favor, digite a data no formato:\n"
                "• DD/MM/AAAA (com barras)\n"
                "• DDMMAAAA (sem barras)\n\n"
                "Exemplos:\n"
                "• 15/03/2024\n"
                "• 15032024\n"
                "• 05122023\n\n"
                "Ou use 'hoje' para data atual"
            )
            return None
        
        # Valida a data
        if not validate_date(date):
            await update.message.reply_text(
                "❌ **Data inválida!**\n\n"
                "A data que você digitou não existe.\n"
                "Por favor, verifique e digite novamente:"
            )
            return None
    
    return await process_date_selection(context, transaction_type, date)

async def handle_date_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a confirmação da data"""
    text = update.message.text
    transaction_type = context.user_data.get('current_transaction_type')
    date = context.user_data.get('tentative_date')
    
    if text == '✅ Sim, está correto' and date:
        # Confirma a data e avança para a descrição
        if transaction_type == 'salary':
            context.user_data['salary_date'] = date
            await update.message.reply_text(
                "📝 **Fonte do Salário**\n\n"
                "Digite a fonte/origem deste salário:\n"
                "Ex: Empresa XYZ, Freelance, CLT, etc.",
                reply_markup=ReplyKeyboardRemove()
            )
            return GET_SALARY_DESC
        
        elif transaction_type == 'expense':
            context.user_data['expense_date'] = date
            await update.message.reply_text(
                "📝 **Motivo do Gasto**\n\n"
                "Digite o motivo desta despesa:\n"
                "Ex: Aluguel, Supermercado, Transporte, Lazer, etc.",
                reply_markup=ReplyKeyboardRemove()
            )
            return GET_EXPENSE_DESC
        
        elif transaction_type == 'credit':
            context.user_data['credit_date'] = date
            await update.message.reply_text(
                "📝 **Fonte do Crédito**\n\n"
                "Digite a origem deste crédito:\n"
                "Ex: Investimentos, Bônus, Reembolso, etc.",
                reply_markup=ReplyKeyboardRemove()
            )
            return GET_CREDIT_DESC
    
    elif text == '❌ Não, corrigir':
        # Volta para a seleção de data
        await update.message.reply_text(
            "🔄 Vamos tentar novamente.\n\n"
            "Use o calendário abaixo ou digite a data manualmente:",
            reply_markup=generate_calendar_inline('month')
        )
        
        if transaction_type == 'salary':
            return GET_SALARY_DATE
        elif transaction_type == 'expense':
            return GET_EXPENSE_DATE
        elif transaction_type == 'credit':
            return GET_CREDIT_DATE
    
    else:
        await update.message.reply_text(
            "Por favor, use os botões para confirmar ou corrigir a data.",
            reply_markup=date_confirmation_keyboard()
        )
        return CONFIRM_DATE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa com verificação pelo ID único do Telegram"""
    user_id = update.effective_user.id
    
    # Verifica se o ID do usuário já está cadastrado
    if db.user_exists(user_id):
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname']
        
        # Mensagem de boas-vindas personalizada para usuário cadastrado
        await update.message.reply_text(
            f"👋 Olá, {nickname}!\n\n"
            f"Que bom ver você de volta! 😊\n\n"
            f"Vamos continuar organizando suas finanças:",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    else:
        # Novo usuário - inicia processo de cadastro
        await update.message.reply_text(
            "👋 Olá! Sou seu assistente financeiro pessoal.\n\n"
            "Parece que é sua primeira vez aqui! 😊\n\n"
            "**Como você gostaria de ser chamado?**"
        )
        return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe e salva o nome do usuário (apenas para novos usuários)"""
    nickname = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not nickname:
        await update.message.reply_text("❌ Por favor, digite um nome válido.")
        return GET_NAME
    
    # Registra o novo usuário no banco de dados
    db.add_user(user_id, nickname)
    
    # Mensagem de confirmação do cadastro
    await update.message.reply_text(
        f"✅ **Cadastro realizado com sucesso!**\n\n"
        f"👋 A partir de agora, você será chamado de: **{nickname}**\n\n"
        f"Vamos começar a organizar suas finanças! 💰",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menu principal"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == '💰 Inserir Salário':
        await update.message.reply_text(
            "💰 **Inserir Salário**\n\n"
            "Por favor, digite o valor do salário:\n"
            "Ex: 2500 ou 3500,50\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_SALARY
        
    elif text == '💸 Inserir Gasto':
        await update.message.reply_text(
            "💸 **Inserir Gasto**\n\n"
            "Por favor, digite o valor do gasto:\n"
            "Ex: 150 ou 89,90\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_EXPENSE
        
    elif text == '💳 Inserir Crédito':
        await update.message.reply_text(
            "💳 **Inserir Crédito**\n\n"
            "Por favor, digite o valor do crédito:\n"
            "Ex: 500 ou 750,25\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_CREDIT
        
    elif text == '📊 Extrato':
        transactions = db.get_statement(user_id)
        nickname = db.get_user_nickname(user_id)
        balance = db.get_balance(user_id)
        
        if not transactions:
            await update.message.reply_text(
                f"📋 **Extrato - {nickname}**\n\n"
                "📭 Nenhuma transação registrada ainda.\n\n"
                "Use as opções abaixo para fazer sua primeira movimentação!",
                reply_markup=main_keyboard()
            )
        else:
            response = f"📋 **Extrato - {nickname}**\n\n"
            
            for i, t in enumerate(transactions, 1):
                emoji = "💰" if t[0] == 'credit' else "💸"
                tipo = "CRÉDITO" if t[0] == 'credit' else "GASTO"
                valor = f"R$ {t[1]:,.2f}"
                data = t[3]  # Data no formato DD/MM/AAAA
                
                response += f"{emoji} **{tipo}**\n"
                response += f"   Valor: {valor}\n"
                response += f"   Descrição: {t[2]}\n"
                response += f"   Data: {data}\n\n"
            
            response += f"💎 **Saldo Total: R$ {balance:,.2f}**"
            
            await update.message.reply_text(
                response,
                reply_markup=main_keyboard()
            )
    
    return MAIN_MENU

async def handle_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o valor do salário"""
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return GET_SALARY
            
        context.user_data['salary_amount'] = amount
        context.user_data['current_transaction_type'] = 'salary'
        
        # Mostra o calendário inline com opção de digitar manualmente
        await update.message.reply_text(
            "📅 **Selecione a data do salário**\n\n"
            "Use o calendário abaixo ou digite a data manualmente:",
            reply_markup=generate_calendar_inline('month')
        )
        return GET_SALARY_DATE
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "Por favor, digite um valor numérico válido:\n"
            "Ex: 2500 ou 3500,50\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_SALARY

async def handle_salary_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a descrição final do salário"""
    try:
        description = update.message.text.strip()
        if not description:
            await update.message.reply_text("❌ Por favor, digite uma descrição válida:")
            return GET_SALARY_DESC
            
        amount = context.user_data.get('salary_amount')
        date = context.user_data.get('salary_date')
        
        if amount and date:
            user_id = update.effective_user.id
            db.add_transaction(user_id, 'credit', amount, f"Salário: {description}", date)
            
            await update.message.reply_text(
                f"✅ **Salário Registrado!**\n\n"
                f"💰 Valor: R$ {amount:,.2f}\n"
                f"📅 Data: {date}\n"
                f"📝 Fonte: {description}\n\n"
                f"Seu salário foi adicionado com sucesso!",
                reply_markup=main_keyboard()
            )
            # Limpa os dados temporários
            context.user_data.pop('salary_amount', None)
            context.user_data.pop('salary_date', None)
            context.user_data.pop('current_transaction_type', None)
            context.user_data.pop('tentative_date', None)
        else:
            await update.message.reply_text(
                "❌ Ocorreu um erro. Por favor, comece novamente.",
                reply_markup=main_keyboard()
            )
        
        return MAIN_MENU
        
    except Exception as e:
        logging.error(f"Erro em handle_salary_description: {e}")
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado. Por favor, tente novamente.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o valor do gasto"""
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return GET_EXPENSE
            
        context.user_data['expense_amount'] = amount
        context.user_data['current_transaction_type'] = 'expense'
        
        # Mostra o calendário inline com opção de digitar manualmente
        await update.message.reply_text(
            "📅 **Selecione a data do gasto**\n\n"
            "Use o calendário abaixo ou digite a data manualmente:",
            reply_markup=generate_calendar_inline('month')
        )
        return GET_EXPENSE_DATE
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "Por favor, digite um valor numérico válido:\n"
            "Ex: 150 ou 89,90\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_EXPENSE

async def handle_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a descrição final do gasto"""
    try:
        description = update.message.text.strip()
        if not description:
            await update.message.reply_text("❌ Por favor, digite uma descrição válida:")
            return GET_EXPENSE_DESC
            
        amount = context.user_data.get('expense_amount')
        date = context.user_data.get('expense_date')
        
        if amount and date:
            user_id = update.effective_user.id
            db.add_transaction(user_id, 'debit', amount, f"Gasto: {description}", date)
            
            await update.message.reply_text(
                f"✅ **Gasto Registrado!**\n\n"
                f"💸 Valor: R$ {amount:,.2f}\n"
                f"📅 Data: {date}\n"
                f"📝 Motivo: {description}\n\n"
                f"Seu gasto foi registrado com sucesso!",
                reply_markup=main_keyboard()
            )
            # Limpa os dados temporários
            context.user_data.pop('expense_amount', None)
            context.user_data.pop('expense_date', None)
            context.user_data.pop('current_transaction_type', None)
            context.user_data.pop('tentative_date', None)
        else:
            await update.message.reply_text(
                "❌ Ocorreu um erro. Por favor, comece novamente.",
                reply_markup=main_keyboard()
            )
        
        return MAIN_MENU
        
    except Exception as e:
        logging.error(f"Erro em handle_expense_description: {e}")
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado. Por favor, tente novamente.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

async def handle_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o valor do crédito"""
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return GET_CREDIT
            
        context.user_data['credit_amount'] = amount
        context.user_data['current_transaction_type'] = 'credit'
        
        # Mostra o calendário inline com opção de digitar manualmente
        await update.message.reply_text(
            "📅 **Selecione a data do crédito**\n\n"
            "Use o calendário abaixo ou digite a data manualmente:",
            reply_markup=generate_calendar_inline('month')
        )
        return GET_CREDIT_DATE
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "Por favor, digite um valor numérico válido:\n"
            "Ex: 500 ou 750,25\n\n"
            "💡 *Dica: Use o teclado numérico do seu celular*",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_CREDIT

async def handle_credit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a descrição final do crédito"""
    try:
        description = update.message.text.strip()
        if not description:
            await update.message.reply_text("❌ Por favor, digite uma descrição válida:")
            return GET_CREDIT_DESC
            
        amount = context.user_data.get('credit_amount')
        date = context.user_data.get('credit_date')
        
        if amount and date:
            user_id = update.effective_user.id
            db.add_transaction(user_id, 'credit', amount, f"Crédito: {description}", date)
            
            await update.message.reply_text(
                f"✅ **Crédito Adicionado!**\n\n"
                f"💳 Valor: R$ {amount:,.2f}\n"
                f"📅 Data: {date}\n"
                f"📝 Fonte: {description}\n\n"
                f"Seu crédito foi registrado com sucesso!",
                reply_markup=main_keyboard()
            )
            # Limpa os dados temporários
            context.user_data.pop('credit_amount', None)
            context.user_data.pop('credit_date', None)
            context.user_data.pop('current_transaction_type', None)
            context.user_data.pop('tentative_date', None)
        else:
            await update.message.reply_text(
                "❌ Ocorreu um erro. Por favor, comece novamente.",
                reply_markup=main_keyboard()
            )
        
        return MAIN_MENU
        
    except Exception as e:
        logging.error(f"Erro em handle_credit_description: {e}")
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado. Por favor, tente novamente.",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação atual"""
    # Limpa todos os dados temporários
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Operação cancelada.",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# Handlers para comandos do menu
async def salario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /salario"""
    user_id = update.effective_user.id
    
    # Verifica se o usuário está cadastrado
    if not db.user_exists(user_id):
        await update.message.reply_text(
            "❌ Você precisa se cadastrar primeiro. Use /start para começar."
        )
        return
    
    await update.message.reply_text(
        "💰 **Inserir Salário**\n\n"
        "Por favor, digite o valor do salário:\n"
        "Ex: 2500 ou 3500,50\n\n"
        "💡 *Dica: Use o teclado numérico do seu celular*",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_SALARY

async def gasto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /gasto"""
    user_id = update.effective_user.id
    
    # Verifica se o usuário está cadastrado
    if not db.user_exists(user_id):
        await update.message.reply_text(
            "❌ Você precisa se cadastrar primeiro. Use /start para começar."
        )
        return
    
    await update.message.reply_text(
        "💸 **Inserir Gasto**\n\n"
        "Por favor, digite o valor do gasto:\n"
        "Ex: 150 ou 89,90\n\n"
        "💡 *Dica: Use o teclado numérico do seu celular*",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_EXPENSE

async def credito_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /credito"""
    user_id = update.effective_user.id
    
    # Verifica se o usuário está cadastrado
    if not db.user_exists(user_id):
        await update.message.reply_text(
            "❌ Você precisa se cadastrar primeiro. Use /start para começar."
        )
        return
    
    await update.message.reply_text(
        "💳 **Inserir Crédito**\n\n"
        "Por favor, digite o valor do crédito:\n"
        "Ex: 500 ou 750,25\n\n"
        "💡 *Dica: Use o teclado numérico do seu celular*",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_CREDIT

async def extrato_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /extrato"""
    user_id = update.effective_user.id
    
    # Verifica se o usuário está cadastrado
    if not db.user_exists(user_id):
        await update.message.reply_text(
            "❌ Você precisa se cadastrar primeiro. Use /start para começar."
        )
        return
    
    transactions = db.get_statement(user_id)
    nickname = db.get_user_nickname(user_id)
    balance = db.get_balance(user_id)
    
    if not transactions:
        await update.message.reply_text(
            f"📋 **Extrato - {nickname}**\n\n"
            "📭 Nenhuma transação registrada ainda.\n\n"
            "Use as opções abaixo para fazer sua primeira movimentação!",
            reply_markup=main_keyboard()
        )
    else:
        response = f"📋 **Extrato - {nickname}**\n\n"
        
        for i, t in enumerate(transactions, 1):
            emoji = "💰" if t[0] == 'credit' else "💸"
            tipo = "CRÉDITO" if t[0] == 'credit' else "GASTO"
            valor = f"R$ {t[1]:,.2f}"
            data = t[3]  # Data no formato DD/MM/AAAA
            
            response += f"{emoji} **{tipo}**\n"
            response += f"   Valor: {valor}\n"
            response += f"   Descrição: {t[2]}\n"
            response += f"   Data: {data}\n\n"
        
        response += f"💎 **Saldo Total: R$ {balance:,.2f}**"
        
        await update.message.reply_text(
            response,
            reply_markup=main_keyboard()
        )
    
    return MAIN_MENU