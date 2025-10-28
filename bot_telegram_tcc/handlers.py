# handlers.py - VERSÃO COMPLETAMENTE CORRIGIDA
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
import database as db
import datetime
import calendar
import logging
import re
import config
import coach
import io
import csv

# Estados da conversação
GET_NAME, GET_SALARY, TIPO_GASTO, CATEGORIA_FIXA, CATEGORIA_FLEXIVEL, NOVA_CATEGORIA_FIXA, NOVA_CATEGORIA_FLEXIVEL, VALOR_GASTO, DATA_GASTO, CONTINUAR_GASTOS, RESUMO_GASTOS = range(11)

# Novos estados para as novas funcionalidades
EDIT_NAME, EDIT_SALARY, GOAL_TYPE, GOAL_DESCRIPTION, GOAL_TARGET, GOAL_DEADLINE, CONFIRM_RESET = range(11, 18)

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== MENUS PRINCIPAIS ==========

def main_keyboard():
    """Teclado principal atualizado do bot"""
    keyboard = [
        ['💸 Registrar Gastos', '📊 Meu Resumo'],
        ['📈 Saúde Financeira', '🎓 Educação Financeira'],
        ['⚙️ Configurações', '❓ Ajuda']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def gastos_keyboard():
    """Teclado específico para gestão de gastos"""
    keyboard = [
        ['🏠 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['📅 Gastos do Mês', '📋 Categorias'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def educacao_keyboard():
    """Teclado para educação financeira"""
    keyboard = [
        ['💡 Dica do Dia', '📚 Aprender Mais'],
        ['🎯 Meus Objetivos', '📖 Glossário'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def configuracoes_keyboard():
    """Teclado para configurações"""
    keyboard = [
        ['✏️ Editar Perfil', '💰 Alterar Salário'],
        ['📁 Exportar Dados', '🔄 Redefinir'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def ajuda_keyboard():
    """Teclado de ajuda"""
    keyboard = [
        ['📝 Como Usar', '❓ Perguntas Frequentes'],
        ['🐛 Reportar Problema', '💬 Feedback'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def sim_nao_keyboard():
    """Teclado SIM/NÃO"""
    keyboard = [
        ['✅ SIM', '❌ NÃO']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def tipo_gasto_keyboard():
    """Teclado para escolher tipo de gasto"""
    keyboard = [
        ['🏠 Gastos Fixos', '🛍️ Gastos Flexíveis'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def categorias_fixas_keyboard():
    """Teclado com categorias fixas"""
    keyboard = []
    categorias = list(config.CATEGORIAS_FIXAS.keys())
    
    for i in range(0, len(categorias), 2):
        row = categorias[i:i+2]
        keyboard.append(row)
    
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def categorias_flexiveis_keyboard():
    """Teclado com categorias flexíveis"""
    keyboard = []
    categorias = list(config.CATEGORIAS_FLEXIVEIS.keys())
    
    for i in range(0, len(categorias), 2):
        row = categorias[i:i+2]
        keyboard.append(row)
    
    keyboard.append(['🏠 Voltar ao Menu'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def analise_keyboard():
    """Teclado para análise"""
    keyboard = [
        ['📈 Análise Detalhada', '📊 Ver Métricas'],
        ['🎯 Definir Metas', '📋 Recomendações'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def objetivos_keyboard():
    """Teclado para gerenciamento de objetivos"""
    keyboard = [
        ['🎯 Adicionar Objetivo', '📋 Meus Objetivos'],
        ['📊 Atualizar Progresso', '🗑️ Excluir Objetivo'],
        ['🏠 Voltar ao Menu']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def tipos_objetivo_keyboard():
    """Teclado para tipos de objetivos"""
    keyboard = [
        ['💰 Economia', '🏠 Moradia'],
        ['🚗 Veículo', '✈️ Viagem'],
        ['📚 Educação', '🏥 Saúde'],
        ['💼 Investimento', '🎁 Outro']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def confirmacao_keyboard():
    """Teclado para confirmações"""
    keyboard = [
        ['✅ CONFIRMAR', '❌ CANCELAR']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ========== CALENDÁRIO INTERATIVO ==========

class Calendar:
    @staticmethod
    def create_calendar(year=None, month=None):
        """Cria um calendário inline"""
        now = datetime.datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
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
        keyboard.append([InlineKeyboardButton(day, callback_data="CAL_IGNORE") for day in week_days])
        
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)
        
        for week in month_days:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="CAL_IGNORE"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day), 
                        callback_data=f"CAL_DAY_{year}_{month:02d}_{day:02d}"
                    ))
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton("📅 Hoje", callback_data="CAL_TODAY"),
            InlineKeyboardButton("⌨️ Digitar", callback_data="CAL_MANUAL")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks do calendário"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Calendar callback received: {data}")
        
        if data == "CAL_IGNORE":
            return DATA_GASTO
        
        elif data == "CAL_TODAY":
            today = datetime.datetime.now()
            date_str = today.strftime('%d/%m/%Y')
            return await Calendar.finish_selection(update, context, date_str)
        
        elif data == "CAL_MANUAL":
            await query.edit_message_text(
                "⌨️ **Digite a data manualmente**\n\n"
                "💡 **Formatos aceitos:**\n"
                "• DD/MM/AAAA (ex: 15/03/2024)\n"
                "• DDMMAAAA (ex: 15032024)\n"
                "• 'hoje' para data atual"
            )
            return DATA_GASTO
        
        elif data.startswith("CAL_DAY_"):
            parts = data.split('_')
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            date_str = f"{day:02d}/{month:02d}/{year}"
            return await Calendar.finish_selection(update, context, date_str)
        
        elif data.startswith("CAL_PREV_") or data.startswith("CAL_NEXT_"):
            parts = data.split('_')
            action = parts[1]
            current_year = int(parts[2])
            current_month = int(parts[3])
            
            if action == "PREV":
                new_month = current_month - 1
                new_year = current_year
                if new_month < 1:
                    new_month = 12
                    new_year -= 1
            else:
                new_month = current_month + 1
                new_year = current_year
                if new_month > 12:
                    new_month = 1
                    new_year += 1
            
            await query.edit_message_reply_markup(
                reply_markup=Calendar.create_calendar(new_year, new_month)
            )
        
        return DATA_GASTO
    
    @staticmethod
    async def finish_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str):
        """Finaliza a seleção da data"""
        query = update.callback_query
        
        # CORREÇÃO: Obter user_id de forma segura
        user_id = context.user_data.get('user_id')
        if not user_id:
            await query.edit_message_text("❌ Erro: Sessão expirada. Por favor, comece novamente.")
            return ConversationHandler.END
        
        # CORREÇÃO: Verificar se todos os dados necessários estão disponíveis
        required_keys = ['tipo_gasto', 'categoria', 'valor_gasto']
        missing_keys = [key for key in required_keys if key not in context.user_data]
        
        if missing_keys:
            logger.error(f"Dados faltantes no user_data: {missing_keys}")
            await query.edit_message_text("❌ Erro: Dados do gasto não encontrados. Por favor, comece novamente.")
            return ConversationHandler.END
        
        tipo_gasto = context.user_data['tipo_gasto']
        categoria = context.user_data['categoria']
        valor = context.user_data['valor_gasto']
        
        descricao = f"{categoria} - {tipo_gasto}"
        success = db.add_transaction(user_id, tipo_gasto, categoria, categoria, valor, descricao, date_str)
        
        if success:
            await query.edit_message_text(f"✅ **Data selecionada:** {date_str}")
            
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 **GASTO REGISTRADO COM SUCESSO!**\n\n"
                     f"📋 **Detalhes:**\n"
                     f"• 🏷️ Tipo: {tipo_gasto.upper()}\n"
                     f"• 📂 Categoria: {categoria}\n"
                     f"• 💰 Valor: R$ {valor:,.2f}\n"
                     f"• 📅 Data: {date_str}\n\n"
                     f"❓ **Gostaria de continuar adicionando gastos?**",
                reply_markup=sim_nao_keyboard()
            )
            
            return CONTINUAR_GASTOS
        else:
            await query.edit_message_text("❌ Erro ao registrar gasto. Tente novamente.")
            return ConversationHandler.END

# ========== VALIDAÇÃO DE DATAS ==========

def parse_date_input(date_text):
    """Converte texto em data formatada"""
    date_text = re.sub(r'[^\d/]', '', date_text.strip())
    
    if len(date_text) == 8 and date_text.isdigit():
        day = date_text[0:2]
        month = date_text[2:4]
        year = date_text[4:8]
        return f"{day}/{month}/{year}"
    
    elif len(date_text) == 10 and date_text.count('/') == 2:
        parts = date_text.split('/')
        if len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
            return date_text
    
    return None

def validate_date(date_str):
    """Valida se uma data é válida"""
    try:
        day, month, year = map(int, date_str.split('/'))
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

# ========== HANDLERS PRINCIPAIS CORRIGIDOS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversação - CORRIGIDO"""
    user_id = update.effective_user.id
    
    # CORREÇÃO: Sempre inicializar user_data com user_id
    context.user_data['user_id'] = user_id
    
    if db.user_exists(user_id):
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname']
        
        await update.message.reply_text(
            f"👋 Olá, {nickname}! Que bom te ver de volta!\n\n"
            f"💼 **Seu Assistente Financeiro Pessoal**\n\n"
            f"Estou aqui para te ajudar a:\n"
            f"• 💸 Controlar seus gastos\n"
            f"• 📈 Melhorar sua saúde financeira\n"
            f"• 🎓 Aprender sobre finanças\n"
            f"• 🎯 Alcançar seus objetivos\n\n"
            f"**O que gostaria de fazer hoje?**",
            reply_markup=main_keyboard()
        )
        
        try:
            dica = await coach.finance_coach.get_personalized_tip(user_id, "incentivo")
            await update.message.reply_text(f"💡 **Dica do Edu:** {dica}")
        except Exception as e:
            logger.error(f"Erro ao obter dica do coach: {e}")
            dica_fallback = coach.finance_coach.get_quick_tip()
            await update.message.reply_text(f"💡 **Dica do Dia:** {dica_fallback}")
            
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 **Bem-vindo ao Edu - Seu Assistente Financeiro!**\n\n"
            "💼 Estou aqui para te ajudar a:\n"
            "• Controlar gastos e receitas\n"
            "• Melhorar sua saúde financeira\n"
            "• Aprender sobre educação financeira\n"
            "• Alcançar sua independência financeira\n\n"
            "📝 Vamos começar! Qual o seu nome?"
        )
        return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Obtém o nome do usuário - CORRIGIDO"""
    nickname = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not nickname:
        await update.message.reply_text("❌ Por favor, digite um nome válido.")
        return GET_NAME
    
    # CORREÇÃO: Garantir que user_id está no context
    context.user_data['nickname'] = nickname
    context.user_data['user_id'] = user_id
    
    await update.message.reply_text(
        f"👋 Prazer, {nickname}!\n\n"
        f"💰 **Vamos configurar seu perfil financeiro**\n\n"
        f"Para te ajudar da melhor forma, preciso saber:\n\n"
        f"💵 **Qual o valor do seu salário líquido mensal?**\n\n"
        f"📝 Digite apenas o valor, por exemplo:\n"
        f"• 1500,00\n• 2500,50\n• 3200,00",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_SALARY

async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Obtém o salário do usuário - CORRIGIDO"""
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        salario_liquido = float(salary_text)
        
        if salario_liquido <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return GET_SALARY
        
        # CORREÇÃO: Garantir que user_id está disponível
        user_id = context.user_data.get('user_id', update.effective_user.id)
        nickname = context.user_data.get('nickname', 'Usuário')
        
        success = db.add_user(user_id, nickname, salario_liquido)
        
        if not success:
            await update.message.reply_text("❌ Erro ao salvar dados. Tente novamente.")
            return GET_SALARY
        
        await update.message.reply_text(
            f"🎉 **Perfil criado com sucesso, {nickname}!**\n\n"
            f"💼 **Seu Assistente Financeiro Está Pronto!**\n\n"
            f"Agora vou te ajudar a:\n"
            f"• 📊 Controlar seus gastos\n"
            f"• 💰 Economizar dinheiro\n"
            f"• 📈 Melhorar suas finanças\n"
            f"• 🎯 Alcançar seus objetivos\n\n"
            f"💡 **Vamos começar com o básico...**",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await update.message.reply_text(
            "📚 **Educação Financeira: Tipos de Gastos**\n\n"
            "🏠 **GASTOS FIXOS**\n"
            "• São despesas regulares e previsíveis\n"
            "• Valores geralmente constantes\n"
            "• Exemplos: Aluguel, Internet, Escola\n\n"
            "🛍️ **GASTOS FLEXÍVEIS**\n"
            "• São despesas variáveis\n"
            "• Podem ser controladas mais facilmente\n"
            "• Exemplos: Alimentação, Lazer, Roupas",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await update.message.reply_text(
            "🎯 **Entender essa diferença é fundamental!**\n\n"
            "Com essa classificação, você poderá:\n"
            "• Identitar onde cortar gastos\n"
            "• Planejar melhor seu orçamento\n"
            "• Alcançar suas metas financeiras\n\n"
            "💰 **Vamos registrar seu primeiro gasto?**",
            reply_markup=tipo_gasto_keyboard()
        )
        
        return TIPO_GASTO
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "💡 Por favor, digite um valor numérico válido.\n\n"
            "📝 **Exemplos corretos:**\n"
            "• 1500,00\n• 2500,50\n• 3200,00\n\n"
            "💵 Qual o valor do seu salário líquido mensal?"
        )
        return GET_SALARY

# ========== HANDLERS PARA REGISTRAR GASTOS CORRIGIDOS ==========

async def adicionar_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /adicionar - CORRIGIDO"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return
    
    # CORREÇÃO: Inicializar user_data
    context.user_data['user_id'] = user_id
    context.user_data['nickname'] = db.get_user_nickname(user_id)
    
    await update.message.reply_text(
        "💸 **REGISTRAR GASTOS**\n\n"
        "Selecione o tipo de gasto que deseja registrar:",
        reply_markup=gastos_keyboard()
    )

async def iniciar_registro_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o registro de gasto a partir do menu de gastos - CORRIGIDO"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return ConversationHandler.END
    
    # CORREÇÃO CRÍTICA: Inicializar user_data com user_id e nickname
    context.user_data['user_id'] = user_id
    context.user_data['nickname'] = db.get_user_nickname(user_id)
    
    text = update.message.text
    
    if 'Gastos Fixos' in text:
        context.user_data['tipo_gasto'] = 'fixo'
        await update.message.reply_text(
            "🏠 **CATEGORIAS DE GASTOS FIXOS**\n\n"
            "📋 Selecione a categoria do gasto:",
            reply_markup=categorias_fixas_keyboard()
        )
        return CATEGORIA_FIXA
        
    elif 'Gastos Flexíveis' in text:
        context.user_data['tipo_gasto'] = 'flexivel'
        await update.message.reply_text(
            "🛍️ **CATEGORIAS DE GASTOS FLEXÍVEIS**\n\n"
            "📋 Selecione a categoria do gasto:",
            reply_markup=categorias_flexiveis_keyboard()
        )
        return CATEGORIA_FLEXIVEL
    
    else:
        await update.message.reply_text(
            "❌ Por favor, selecione uma opção válida:",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END

async def tipo_gasto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a seleção do tipo de gasto - CORRIGIDO"""
    text = update.message.text
    
    # CORREÇÃO: Garantir que user_id está no context
    if 'user_id' not in context.user_data:
        context.user_data['user_id'] = update.effective_user.id
        context.user_data['nickname'] = db.get_user_nickname(update.effective_user.id)
    
    clean_text = re.sub(r'[^\w\s]', '', text).strip()
    
    if 'Gastos Fixos' in clean_text:
        context.user_data['tipo_gasto'] = 'fixo'
        await update.message.reply_text(
            "🏠 **CATEGORIAS DE GASTOS FIXOS**\n\n"
            "📋 Selecione a categoria do gasto:",
            reply_markup=categorias_fixas_keyboard()
        )
        return CATEGORIA_FIXA
        
    elif 'Gastos Flexíveis' in clean_text:
        context.user_data['tipo_gasto'] = 'flexivel'
        await update.message.reply_text(
            "🛍️ **CATEGORIAS DE GASTOS FLEXÍVEIS**\n\n"
            "📋 Selecione a categoria do gasto:",
            reply_markup=categorias_flexiveis_keyboard()
        )
        return CATEGORIA_FLEXIVEL
    
    elif 'Voltar ao Menu' in clean_text:
        await update.message.reply_text(
            "🏠 **MENU PRINCIPAL**\n\n"
            "O que gostaria de fazer?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            "❌ Por favor, selecione uma opção válida:",
            reply_markup=tipo_gasto_keyboard()
        )
        return TIPO_GASTO

async def categoria_fixa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa categoria fixa selecionada - CORRIGIDO"""
    text = update.message.text
    
    # CORREÇÃO: Garantir que user_id está no context
    if 'user_id' not in context.user_data:
        context.user_data['user_id'] = update.effective_user.id
        context.user_data['nickname'] = db.get_user_nickname(update.effective_user.id)
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text(
            "🏠 **MENU PRINCIPAL**\n\n"
            "O que gostaria de fazer?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    
    categoria = text
    context.user_data['categoria'] = categoria
    
    if categoria == 'Nova_fixo':
        await update.message.reply_text(
            "➕ **NOVA CATEGORIA FIXA**\n\n"
            "📝 Qual o nome da nova categoria?",
            reply_markup=ReplyKeyboardRemove()
        )
        return NOVA_CATEGORIA_FIXA
    else:
        await update.message.reply_text(
            f"🏠 **{categoria.upper()}**\n\n"
            f"💰 Qual o valor deste gasto?\n\n"
            f"📝 **Exemplos:**\n"
            f"• 150,00\n• 89,90\n• 1200,00",
            reply_markup=ReplyKeyboardRemove()
        )
        return VALOR_GASTO

async def categoria_flexivel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa categoria flexível selecionada - CORRIGIDO"""
    text = update.message.text
    
    # CORREÇÃO: Garantir que user_id está no context
    if 'user_id' not in context.user_data:
        context.user_data['user_id'] = update.effective_user.id
        context.user_data['nickname'] = db.get_user_nickname(update.effective_user.id)
    
    if 'Voltar ao Menu' in text:
        await update.message.reply_text(
            "🏠 **MENU PRINCIPAL**\n\n"
            "O que gostaria de fazer?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    
    categoria = text
    context.user_data['categoria'] = categoria
    
    if categoria == 'Nova_flexivel':
        await update.message.reply_text(
            "➕ **NOVA CATEGORIA FLEXÍVEL**\n\n"
            "📝 Qual o nome da nova categoria?",
            reply_markup=ReplyKeyboardRemove()
        )
        return NOVA_CATEGORIA_FLEXIVEL
    else:
        await update.message.reply_text(
            f"🛍️ **{categoria.upper()}**\n\n"
            f"💰 Qual o valor deste gasto?\n\n"
            f"📝 **Exemplos:**\n"
            f"• 150,00\n• 89,90\n• 350,00",
            reply_markup=ReplyKeyboardRemove()
        )
        return VALOR_GASTO

async def nova_categoria_fixa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa nova categoria fixa - CORRIGIDO"""
    nova_categoria = update.message.text.strip()
    
    # CORREÇÃO: Garantir que user_id está disponível
    user_id = context.user_data.get('user_id', update.effective_user.id)
    
    if not nova_categoria:
        await update.message.reply_text("❌ Por favor, digite um nome válido para a categoria.")
        return NOVA_CATEGORIA_FIXA
    
    success = db.add_custom_category(user_id, 'fixo', nova_categoria)
    
    if not success:
        await update.message.reply_text("❌ Erro ao criar categoria. Tente novamente.")
        return NOVA_CATEGORIA_FIXA
    
    context.user_data['categoria'] = nova_categoria
    
    await update.message.reply_text(
        f"✅ **NOVA CATEGORIA CRIADA:** {nova_categoria.upper()}\n\n"
        f"💰 Qual o valor deste gasto?\n\n"
        f"📝 **Exemplos:**\n"
        f"• 150,00\n• 89,90\n• 1200,00",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def nova_categoria_flexivel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa nova categoria flexível - CORRIGIDO"""
    nova_categoria = update.message.text.strip()
    
    # CORREÇÃO: Garantir que user_id está disponível
    user_id = context.user_data.get('user_id', update.effective_user.id)
    
    if not nova_categoria:
        await update.message.reply_text("❌ Por favor, digite um nome válido para a categoria.")
        return NOVA_CATEGORIA_FLEXIVEL
    
    success = db.add_custom_category(user_id, 'flexivel', nova_categoria)
    
    if not success:
        await update.message.reply_text("❌ Erro ao criar categoria. Tente novamente.")
        return NOVA_CATEGORIA_FLEXIVEL
    
    context.user_data['categoria'] = nova_categoria
    
    await update.message.reply_text(
        f"✅ **NOVA CATEGORIA CRIADA:** {nova_categoria.upper()}\n\n"
        f"💰 Qual o valor deste gasto?\n\n"
        f"📝 **Exemplos:**\n"
        f"• 150,00\n• 89,90\n• 350,00",
        reply_markup=ReplyKeyboardRemove()
    )
    return VALOR_GASTO

async def valor_gasto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o valor do gasto - CORRIGIDO"""
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return VALOR_GASTO
        
        context.user_data['valor_gasto'] = amount
        
        await update.message.reply_text(
            "📅 **Qual a data deste gasto?**\n\n"
            "Selecione a data no calendário abaixo:",
            reply_markup=Calendar.create_calendar()
        )
        return DATA_GASTO
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "💡 Por favor, digite um valor numérico válido.\n\n"
            "📝 **Exemplos corretos:**\n"
            "• 150,00\n• 89,90\n• 1200,00\n\n"
            "💰 Qual o valor deste gasto?"
        )
        return VALOR_GASTO

async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada manual de data - CORRIGIDO"""
    text = update.message.text.strip().lower()
    
    if text == 'hoje':
        date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    else:
        date_str = parse_date_input(text)
        if not date_str or not validate_date(date_str):
            await update.message.reply_text(
                "❌ **Formato de data inválido!**\n\n"
                "💡 **Formatos aceitos:**\n"
                "• DD/MM/AAAA (com barras)\n"
                "• DDMMAAAA (sem barras)\n\n"
                "📝 **Exemplos:**\n"
                "• 15/03/2024\n• 15032024\n• 05122023\n\n"
                "🔄 Ou use 'hoje' para data atual"
            )
            return DATA_GASTO
    
    # CORREÇÃO: Garantir que user_id está disponível
    user_id = context.user_data.get('user_id', update.effective_user.id)
    
    # CORREÇÃO: Verificar se todos os dados necessários estão disponíveis
    required_keys = ['tipo_gasto', 'categoria', 'valor_gasto']
    missing_keys = [key for key in required_keys if key not in context.user_data]
    
    if missing_keys:
        logger.error(f"Dados faltantes no user_data: {missing_keys}")
        await update.message.reply_text("❌ Erro: Dados do gasto não encontrados. Por favor, comece novamente.")
        return ConversationHandler.END
    
    tipo_gasto = context.user_data['tipo_gasto']
    categoria = context.user_data['categoria']
    valor = context.user_data['valor_gasto']
    
    descricao = f"{categoria} - {tipo_gasto}"
    success = db.add_transaction(user_id, tipo_gasto, categoria, categoria, valor, descricao, date_str)
    
    if success:
        await update.message.reply_text(
            f"✅ **Data selecionada:** {date_str}\n\n"
            f"🎉 **GASTO REGISTRADO COM SUCESSO!**\n\n"
            f"📋 **Detalhes:**\n"
            f"• 🏷️ Tipo: {tipo_gasto.upper()}\n"
            f"• 📂 Categoria: {categoria}\n"
            f"• 💰 Valor: R$ {valor:,.2f}\n"
            f"• 📅 Data: {date_str}\n\n"
            f"❓ **Gostaria de continuar adicionando gastos?**",
            reply_markup=sim_nao_keyboard()
        )
        
        return CONTINUAR_GASTOS
    else:
        await update.message.reply_text("❌ Erro ao registrar gasto. Tente novamente.")
        return ConversationHandler.END

async def continuar_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa se o usuário quer continuar adicionando gastos - CORRIGIDO"""
    text = update.message.text
    
    if 'SIM' in text:
        await update.message.reply_text(
            "💰 **ADICIONAR NOVO GASTO**\n\n"
            "📋 Qual o tipo de gasto você quer adicionar?",
            reply_markup=tipo_gasto_keyboard()
        )
        return TIPO_GASTO
        
    elif 'NÃO' in text:
        # CORREÇÃO: Obter user_id de forma segura e nickname do banco de dados
        user_id = context.user_data.get('user_id', update.effective_user.id)
        nickname = db.get_user_nickname(user_id)  # Buscar do banco de dados
        
        expenses = db.get_monthly_expenses(user_id)
        
        response = f"📊 **RESUMO DOS SEUS GASTOS - {nickname}**\n\n"
        
        total_fixo = 0
        total_flexivel = 0
        
        if expenses['fixo']:
            response += "🏠 **GASTOS FIXOS:**\n"
            for categoria, subcategorias in expenses['fixo'].items():
                for subcat, valor in subcategorias.items():
                    response += f"• {categoria}: R$ {valor:,.2f}\n"
                    total_fixo += valor
            response += f"📌 **Total Fixo:** R$ {total_fixo:,.2f}\n\n"
        
        if expenses['flexivel']:
            response += "🛍️ **GASTOS FLEXÍVEIS:**\n"
            for categoria, subcategorias in expenses['flexivel'].items():
                for subcat, valor in subcategorias.items():
                    response += f"• {categoria}: R$ {valor:,.2f}\n"
                    total_flexivel += valor
            response += f"📌 **Total Flexível:** R$ {total_flexivel:,.2f}\n\n"
        
        total_geral = total_fixo + total_flexivel
        response += f"🎯 **TOTAL GASTO:** R$ {total_geral:,.2f}\n\n"
        
        user_data = db.get_user_data(user_id)
        salario = user_data['salario_liquido'] if user_data else 0
        saldo = salario - total_geral
        
        response += f"💵 **Seu salário:** R$ {salario:,.2f}\n"
        response += f"💸 **Seus gastos:** R$ {total_geral:,.2f}\n"
        response += f"⚖️ **Saldo disponível:** R$ {saldo:,.2f}\n\n"
        
        if saldo >= 0:
            response += "✅ **Situação:** Positiva - Você está gastando menos do que ganha!\n\n"
        else:
            response += "⚠️ **Situação:** Atenção - Você está gastando mais do que ganha.\n\n"
        
        response += "💡 Com esses valores podemos analisar a sua saúde financeira.\n\n"
        response += "🎯 **O que deseja fazer agora?**"
        
        await update.message.reply_text(response, reply_markup=analise_keyboard())
        return RESUMO_GASTOS
    
    else:
        await update.message.reply_text(
            "❌ Por favor, selecione SIM ou NÃO:",
            reply_markup=sim_nao_keyboard()
        )
        return CONTINUAR_GASTOS

async def resumo_gastos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa ações após o resumo - CORRIGIDO"""
    text = update.message.text
    
    if any(word in text for word in ['Analisar Saúde Financeira', 'Análise Detalhada']):
        # CORREÇÃO: Obter user_id e nickname do banco de dados
        user_id = context.user_data.get('user_id', update.effective_user.id)
        nickname = db.get_user_nickname(user_id)
        
        await update.message.reply_text(
            f"📈 **ANÁLISE DE SAÚDE FINANCEIRA - {nickname}**\n\n"
            f"Nesta fase, vamos entender melhor como está a sua saúde financeira.\n\n"
            f"💡 Lembra da divisão inicial que fizemos? Nela definimos aproximadamente um limite de gastos "
            f"para algumas áreas da sua vida, com base no valor do seu salário.\n\n"
            f"🎯 Agora, vamos comparar os gastos que você adicionou com esses limites...",
            reply_markup=main_keyboard()
        )
        
        await update.message.reply_text(
            "🚀 **PRÓXIMOS PASSOS**\n\n"
            "No próximo fluxo analisaremos sua saúde financeira com mais detalhes, incluindo:\n"
            "• 📊 Gráficos comparativos\n"
            "• 💡 Recomendações personalizadas\n\n"
            "📋 **Por enquanto, você pode:**\n"
            "• Adicionar mais gastos\n• Ver seu resumo atual\n• Aprender mais sobre finanças",
            reply_markup=main_keyboard()
        )
        
        return ConversationHandler.END
        
    elif any(word in text for word in ['Voltar ao Menu']):
        await update.message.reply_text(
            "🏠 **MENU PRINCIPAL**\n\n"
            "O que gostaria de fazer?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            "❌ Por favor, selecione uma opção válida:",
            reply_markup=analise_keyboard()
        )
        return RESUMO_GASTOS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a conversação"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ **Operação cancelada.**\n\n"
        "💼 Voltando ao menu principal...",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

# ========== HANDLERS DE CONFIGURAÇÕES ==========

async def configuracoes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para configurações"""
    await update.message.reply_text(
        "⚙️ **CONFIGURAÇÕES**\n\n"
        "🔧 Gerencie sua conta e dados:",
        reply_markup=configuracoes_keyboard()
    )

async def edit_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para editar perfil"""
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    await update.message.reply_text(
        f"✏️ **EDITAR PERFIL**\n\n"
        f"👋 Atualmente você é: {user_data['nickname']}\n\n"
        f"📝 Digite seu novo nome:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    context.user_data['user_id'] = user_id
    return EDIT_NAME

async def edit_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa novo nome do usuário"""
    new_name = update.message.text.strip()
    user_id = context.user_data.get('user_id', update.effective_user.id)
    
    if not new_name:
        await update.message.reply_text("❌ Nome inválido. Digite novamente:")
        return EDIT_NAME
    
    user_data = db.get_user_data(user_id)
    success = db.add_user(user_id, new_name, user_data['salario_liquido'])
    
    if success:
        await update.message.reply_text(
            f"✅ **Nome atualizado com sucesso!**\n\n"
            f"👋 Agora você é: {new_name}",
            reply_markup=configuracoes_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Erro ao atualizar nome. Tente novamente.",
            reply_markup=configuracoes_keyboard()
        )
        return ConversationHandler.END

async def edit_salary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para alterar salário"""
    user_id = update.effective_user.id
    user_data = db.get_user_data(user_id)
    
    await update.message.reply_text(
        f"💰 **ALTERAR SALÁRIO**\n\n"
        f"💵 Salário atual: R$ {user_data['salario_liquido']:,.2f}\n\n"
        f"📝 Digite o novo valor do seu salário líquido:\n\n"
        f"💡 **Exemplos:**\n"
        f"• 1500,00\n• 2500,50\n• 3200,00",
        reply_markup=ReplyKeyboardRemove()
    )
    
    context.user_data['user_id'] = user_id
    return EDIT_SALARY

async def edit_salary_process_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa novo salário do usuário"""
    try:
        salary_text = update.message.text.replace(',', '.').strip()
        novo_salario = float(salary_text)
        
        if novo_salario <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return EDIT_SALARY
        
        user_id = context.user_data.get('user_id', update.effective_user.id)
        user_data = db.get_user_data(user_id)
        
        db.add_salary_history(user_id, novo_salario)
        success = db.add_user(user_id, user_data['nickname'], novo_salario)
        
        if success:
            await update.message.reply_text(
                f"✅ **Salário atualizado com sucesso!**\n\n"
                f"💵 Novo salário: R$ {novo_salario:,.2f}",
                reply_markup=configuracoes_keyboard()
            )
            
            try:
                dica = await coach.finance_coach.get_personalized_tip(user_id, "apos_salario")
                await update.message.reply_text(f"💡 **Dica do Edu:** {dica}")
            except Exception as e:
                logger.error(f"Erro ao obter dica do coach: {e}")
                
        else:
            await update.message.reply_text("❌ Erro ao atualizar salário. Tente novamente.")
            
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "💡 Por favor, digite um valor numérico válido.\n\n"
            "📝 **Exemplos corretos:**\n"
            "• 1500,00\n• 2500,50\n• 3200,00\n\n"
            "💵 Digite o novo valor do seu salário:"
        )
        return EDIT_SALARY

async def export_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exporta dados do usuário"""
    user_id = update.effective_user.id
    
    try:
        data = db.export_user_data(user_id)
        
        if not data:
            await update.message.reply_text("❌ Erro ao exportar dados.")
            return
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Tipo', 'Categoria', 'Subcategoria', 'Valor', 'Descrição', 'Data', 'Timestamp'])
        
        for trans in data['transactions']:
            writer.writerow(trans)
        
        csv_data = output.getvalue()
        output.close()
        
        await update.message.reply_document(
            document=io.BytesIO(csv_data.encode('utf-8')),
            filename=f"dados_financeiros_{user_id}.csv",
            caption="📁 **SEUS DADOS FINANCEIROS EXPORTADOS**\n\n"
                   "💾 Arquivo CSV com todas suas transações.\n"
                   "📊 Use para análise em planilhas ou outros apps."
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        await update.message.reply_text(
            "❌ Erro ao exportar dados. Tente novamente mais tarde.",
            reply_markup=configuracoes_keyboard()
        )

async def reset_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia processo de redefinição de dados"""
    await update.message.reply_text(
        "🔄 **REDEFINIR DADOS**\n\n"
        "⚠️ **ATENÇÃO:** Esta ação irá:\n"
        "• ❌ Apagar TODOS seus gastos registrados\n"
        "• ❌ Remover suas categorias personalizadas\n"
        "• ❌ Excluir seus objetivos\n"
        "• ❌ Limpar histórico de salários\n\n"
        "📌 **Será mantido apenas:**\n"
        "• ✅ Seu cadastro básico\n"
        "• ✅ Seu nome\n\n"
        "🔒 Esta ação NÃO pode ser desfeita!\n\n"
        "❓ **Tem certeza que deseja continuar?**",
        reply_markup=confirmacao_keyboard()
    )
    return CONFIRM_RESET

async def confirm_reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma e executa redefinição de dados"""
    user_id = update.effective_user.id
    
    if "CONFIRMAR" in update.message.text:
        success = db.reset_user_data(user_id)
        
        if success:
            await update.message.reply_text(
                "✅ **DADOS REDEFINIDOS COM SUCESSO!**\n\n"
                "🔄 Todos seus dados foram removidos.\n"
                "💼 Você pode começar novamente usando /start\n\n"
                "💡 Dica: Agora é uma chance para recomeçar com mais experiência!",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao redefinir dados. Tente novamente.",
                reply_markup=configuracoes_keyboard()
            )
    else:
        await update.message.reply_text(
            "✅ **Operação cancelada.**\n\n"
            "Seus dados estão seguros! 🔒",
            reply_markup=configuracoes_keyboard()
        )
    
    return ConversationHandler.END

# ========== HANDLERS DE AJUDA ==========

async def ajuda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para ajuda"""
    await update.message.reply_text(
        "❓ **AJUDA E SUPORTE**\n\n"
        "Encontre ajuda e informações:",
        reply_markup=ajuda_keyboard()
    )

async def help_how_to_use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra como usar o bot"""
    help_text = """
📝 **COMO USAR O EDU - SEU ASSISTENTE FINANCEIRO**

🎯 **PRIMEIROS PASSOS:**

1. **📋 Cadastro Inicial**
   Use /start para se cadastrar e configurar seu salário

2. **💸 Registrar Gastos**
   • Vá em "Registrar Gastos"
   • Escolha entre Fixos ou Flexíveis
   • Selecione categoria e valor

3. **📊 Acompanhamento**
   • Use "Meu Resumo" para ver gastos
   • "Saúde Financeira" para análise detalhada

💡 **DICAS DE USO:**
• 🏠 **Gastos Fixos:** Despesas recorrentes (aluguel, contas)
• 🛍️ **Gastos Flexíveis:** Despesas variáveis (comida, lazer)
• 📈 **Saúde Financeira:** Análise automática da sua situação

🔧 **COMANDOS DISPONÍVEIS:**
/start - Iniciar ou redefinir cadastro
/menu - Mostrar menu principal
/resumo - Ver resumo financeiro
/analisar - Análise de saúde financeira
"""
    await update.message.reply_text(help_text, reply_markup=ajuda_keyboard())

async def report_problem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para reportar problemas"""
    await update.message.reply_text(
        "🐛 **REPORTAR PROBLEMA**\n\n"
        "📧 Entre em contato com nosso suporte:\n\n"
        "✉️ **Email:** suporte@edufinance.com\n"
        "📱 **Telegram:** @suporte_edu_finance\n\n"
        "💡 **Inclua em sua mensagem:**\n"
        "• Seu ID: {}\n"
        "• O que estava tentando fazer\n"
        "• O que aconteceu de errado\n\n"
        "🚀 Responderemos o mais rápido possível!".format(update.effective_user.id),
        reply_markup=ajuda_keyboard()
    )

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para enviar feedback"""
    await update.message.reply_text(
        "💬 **ENVIAR FEEDBACK**\n\n"
        "🎯 Sua opinião é muito importante para melhorarmos!\n\n"
        "📧 Envie seu feedback para:\n\n"
        "✉️ **Email:** feedback@edufinance.com\n\n"
        "💡 **Conte para nós:**\n"
        "• O que você mais gosta\n"
        "• O que podemos melhorar\n"
        "• Sua experiência geral\n\n"
        "🌟 Obrigado por ajudar a melhorar o Edu!",
        reply_markup=ajuda_keyboard()
    )

# ========== HANDLERS DE EDUCAÇÃO FINANCEIRA ==========

async def educacao_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para educação financeira"""
    await update.message.reply_text(
        "🎓 **EDUCAÇÃO FINANCEIRA**\n\n"
        "Aprenda e evolua seu conhecimento financeiro:",
        reply_markup=educacao_keyboard()
    )

async def dica_dia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para dica do dia"""
    user_id = update.effective_user.id
    try:
        dica = await coach.finance_coach.get_personalized_tip(user_id, "geral")
        await update.message.reply_text(
            f"💡 **DICA DO EDU**\n\n{dica}\n\n"
            f"📚 Quer aprender mais?",
            reply_markup=educacao_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro ao obter dica: {e}")
        dica_fallback = coach.finance_coach.get_quick_tip()
        await update.message.reply_text(
            f"💡 **DICA DO DIA**\n\n{dica_fallback}\n\n"
            f"📚 Quer aprender mais?",
            reply_markup=educacao_keyboard()
        )

async def aprender_mais_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para aprender mais"""
    await update.message.reply_text(
        "📚 **CONTEÚDO EDUCATIVO**\n\n"
        "🎓 **Em breve disponível:**\n"
        "• 📖 Cursos rápidos\n"
        "• 🎯 Guias práticos\n"
        "• 📊 Calculadoras\n"
        "• 💡 Artigos exclusivos\n\n"
        "Enquanto isso, use as 'Dicas do Dia' para aprender!",
        reply_markup=educacao_keyboard()
    )

async def objetivos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para objetivos"""
    await update.message.reply_text(
        "🎯 **MEUS OBJETIVOS FINANCEIROS**\n\n"
        "Aqui você pode definir e acompanhar suas metas financeiras!\n\n"
        "💡 **Tipos de objetivos:**\n"
        "• 💰 Economia (fundo emergencial, poupança)\n"
        "• 🏠 Moradia (entrada de imóvel, reforma)\n"
        "• 🚗 Veículo (compra de carro/moto)\n"
        "• ✈️ Viagem (ferias, passeios)\n"
        "• 📚 Educação (cursos, faculdade)\n"
        "• 🏥 Saúde (tratamentos, planos)\n"
        "• 💼 Investimento (ações, fundos)\n\n"
        "📊 **O que deseja fazer?**",
        reply_markup=objetivos_keyboard()
    )

async def glossario_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para glossário"""
    glossary = """
📖 **GLOSSÁRIO FINANCEIRO**

💼 **TERMOS BÁSICOS:**

💰 **Renda Líquida**
Valor que sobra do salário após descontos de impostos e encargos.

🏠 **Gastos Fixos**
Despesas regulares e previsíveis (aluguel, internet, escola).

🛍️ **Gastos Flexíveis**
Despesas variáveis que podem ser controladas (alimentação, lazer).

📊 **Orçamento**
Planejamento de receitas e despesas para um período.

💎 **Reserva de Emergência**
Valor guardado para imprevistos (recomenda-se 3-6 meses de gastos).

🚀 **Investimento**
Aplicação de recursos para gerar retorno no futuro.

📈 **Juros Compostos**
"Juros sobre juros" - o segredo do crescimento financeiro.

💡 **Dica:** Educação financeira é contínua! Continue aprendendo! 🎓
"""
    await update.message.reply_text(glossary, reply_markup=educacao_keyboard())

# ========== HANDLERS DE OBJETIVOS ==========

async def add_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia processo de adicionar objetivo"""
    await update.message.reply_text(
        "🎯 **ADICIONAR OBJETIVO**\n\n"
        "📋 Selecione o tipo do objetivo:",
        reply_markup=tipos_objetivo_keyboard()
    )
    return GOAL_TYPE

async def goal_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa tipo do objetivo"""
    goal_type = update.message.text
    context.user_data['goal_type'] = goal_type
    
    await update.message.reply_text(
        f"📝 **DESCREVA SEU OBJETIVO**\n\n"
        f"Tipo: {goal_type}\n\n"
        f"💬 Descreva com detalhes seu objetivo:\n"
        f"• Ex: 'Fundo de emergência de 6 meses'\n"
        f"• Ex: 'Entrada para apartamento'\n"
        f"• Ex: 'Viagem para Europa'",
        reply_markup=ReplyKeyboardRemove()
    )
    return GOAL_DESCRIPTION

async def goal_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa descrição do objetivo"""
    description = update.message.text
    context.user_data['goal_description'] = description
    
    await update.message.reply_text(
        f"💰 **VALOR DA META**\n\n"
        f"Objetivo: {description}\n\n"
        f"💵 Qual o valor total que você precisa atingir?\n\n"
        f"📝 **Exemplos:**\n"
        f"• 5000,00\n• 15000,00\n• 25000,50"
    )
    return GOAL_TARGET

async def goal_target_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa valor da meta"""
    try:
        target_text = update.message.text.replace(',', '.').strip()
        target_value = float(target_text)
        
        if target_value <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero. Tente novamente:")
            return GOAL_TARGET
        
        context.user_data['goal_target'] = target_value
        
        await update.message.reply_text(
            f"📅 **PRAZO ESTIMADO**\n\n"
            f"💡 Em quanto tempo você quer alcançar esta meta?\n\n"
            f"📝 **Exemplos:**\n"
            f"• 6 meses\n• 1 ano\n• 2 anos\n\n"
            f"💬 Descreva o prazo:"
        )
        return GOAL_DEADLINE
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Valor inválido!**\n\n"
            "💡 Por favor, digite um valor numérico válido.\n\n"
            "📝 **Exemplos:** 5000,00 ou 15000,00\n\n"
            "💰 Digite o valor da meta:"
        )
        return GOAL_TARGET

async def goal_deadline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa prazo e salva objetivo"""
    deadline = update.message.text
    user_id = update.effective_user.id
    
    goal_type = context.user_data.get('goal_type')
    description = context.user_data.get('goal_description')
    target_value = context.user_data.get('goal_target')
    
    success = db.add_goal(user_id, goal_type, description, target_value, 0)
    
    if success:
        await update.message.reply_text(
            f"✅ **OBJETIVO CRIADO COM SUCESSO!**\n\n"
            f"🎯 **Tipo:** {goal_type}\n"
            f"📝 **Descrição:** {description}\n"
            f"💰 **Meta:** R$ {target_value:,.2f}\n"
            f"⏰ **Prazo:** {deadline}\n\n"
            f"💡 Acompanhe seu progresso no menu 'Meus Objetivos'!",
            reply_markup=objetivos_keyboard()
        )
        
        try:
            dica = await coach.finance_coach.get_celebration_message(user_id, 'meta_atingida')
            await update.message.reply_text(f"🌟 {dica}")
        except Exception as e:
            logger.error(f"Erro ao obter mensagem: {e}")
            
    else:
        await update.message.reply_text(
            "❌ Erro ao criar objetivo. Tente novamente.",
            reply_markup=objetivos_keyboard()
        )
    
    return ConversationHandler.END

async def list_goals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista objetivos do usuário"""
    user_id = update.effective_user.id
    goals = db.get_goals(user_id)
    
    if not goals:
        await update.message.reply_text(
            "📝 **VOCÊ AINDA NÃO TEM OBJETIVOS**\n\n"
            "🎯 Que tal criar seu primeiro objetivo financeiro?\n\n"
            "💡 Ter metas claras ajuda a manter o foco e motiva a economizar!",
            reply_markup=objetivos_keyboard()
        )
        return
    
    response = "📋 **SEUS OBJETIVOS FINANCEIROS**\n\n"
    
    for i, goal in enumerate(goals, 1):
        progresso = (goal['valor_atual'] / goal['valor_meta']) * 100 if goal['valor_meta'] > 0 else 0
        barra_progresso = "🟩" * int(progresso / 20) + "⬜" * (5 - int(progresso / 20))
        status = "✅ CONCLUÍDO" if goal['concluido'] else f"📊 {progresso:.1f}%"
        
        response += f"{i}. {goal['tipo']} - {goal['descricao']}\n"
        response += f"   💰 R$ {goal['valor_atual']:,.2f} / R$ {goal['valor_meta']:,.2f}\n"
        response += f"   {barra_progresso} {status}\n"
        response += f"   📅 Criado: {goal['data_criacao']}\n\n"
    
    await update.message.reply_text(response, reply_markup=objetivos_keyboard())

# ========== COMANDOS EXISTENTES ==========

async def resumo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para ver resumo"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return
    
    user_data = db.get_user_data(user_id)
    nickname = user_data['nickname']
    expenses = db.get_monthly_expenses(user_id)
    
    analysis = coach.finance_coach.analyze_financial_health(user_id)
    
    response = f"📊 **RESUMO FINANCEIRO - {nickname}**\n\n"
    
    total_fixo = 0
    total_flexivel = 0
    
    if expenses['fixo']:
        response += "🏠 **GASTOS FIXOS:**\n"
        for categoria, subcategorias in expenses['fixo'].items():
            for subcat, valor in subcategorias.items():
                response += f"• {categoria}: R$ {valor:,.2f}\n"
                total_fixo += valor
        response += f"📌 **Total Fixo:** R$ {total_fixo:,.2f}\n\n"
    
    if expenses['flexivel']:
        response += "🛍️ **GASTOS FLEXÍVEIS:**\n"
        for categoria, subcategorias in expenses['flexivel'].items():
            for subcat, valor in subcategorias.items():
                response += f"• {categoria}: R$ {valor:,.2f}\n"
                total_flexivel += valor
        response += f"📌 **Total Flexível:** R$ {total_flexivel:,.2f}\n\n"
    
    total_geral = total_fixo + total_flexivel
    response += f"🎯 **TOTAL GASTO:** R$ {total_geral:,.2f}\n\n"
    
    salario = user_data['salario_liquido']
    saldo = salario - total_geral
    
    response += f"💵 **Seu salário:** R$ {salario:,.2f}\n"
    response += f"💸 **Seus gastos:** R$ {total_geral:,.2f}\n"
    response += f"⚖️ **Saldo disponível:** R$ {saldo:,.2f}\n\n"
    
    response += f"📈 **ANÁLISE DO EDU:**\n{analysis['mensagem']}\n\n"
    response += f"💡 **Recomendação:** {analysis['recomendacao']}\n\n"
    
    response += "🔍 **Próximos passos:**\n"
    if saldo >= 0:
        response += "✅ Continue controlando seus gastos!\n"
        response += "💡 Considere investir o excedente\n"
    else:
        response += "⚠️ Reveja seus gastos flexíveis\n"
        response += "🎯 Estabeleça metas de economia\n"
    
    await update.message.reply_text(response, reply_markup=main_keyboard())

async def analisar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para analisar saúde financeira"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return
    
    user_data = db.get_user_data(user_id)
    nickname = user_data['nickname']
    
    analysis = coach.finance_coach.analyze_financial_health(user_id)
    
    response = f"📈 **SAÚDE FINANCEIRA - {nickname}**\n\n"
    response += f"🏥 **Status:** {analysis['nivel'].upper()}\n"
    response += f"💬 **Diagnóstico:** {analysis['mensagem']}\n\n"
    
    response += "📊 **MÉTRICAS:**\n"
    response += f"• 💰 Saldo atual: R$ {analysis['saldo']:,.2f}\n"
    response += f"• 📈 Percentual de gastos: {analysis['percentual_gastos']:.1f}%\n"
    response += f"• 🏠 Gastos fixos: R$ {analysis['total_fixo']:,.2f}\n"
    response += f"• 🛍️ Gastos flexíveis: R$ {analysis['total_flexivel']:,.2f}\n\n"
    
    response += "🎯 **RECOMENDAÇÕES PERSONALIZADAS:**\n"
    response += f"{analysis['recomendacao']}\n\n"
    
    try:
        dica_extra = await coach.finance_coach.get_personalized_tip(user_id, "apos_analise")
        response += f"💡 **Dica Extra:** {dica_extra}\n\n"
    except Exception as e:
        logger.error(f"Erro ao obter dica extra: {e}")
    
    response += "🔧 **Ações sugeridas:**\n"
    if analysis['nivel'] == 'saudavel':
        response += "✅ Mantenha o controle atual\n"
        response += "💎 Considere investimentos\n"
        response += "🎯 Estabeleça novas metas\n"
    elif analysis['nivel'] == 'atencao':
        response += "⚠️ Revise gastos flexíveis\n"
        response += "📋 Corte despesas desnecessárias\n"
        response += "💡 Acompanhe diariamente\n"
    else:
        response += "🚨 Priorize gastos essenciais\n"
        response += "📞 Busque orientação especializada\n"
        response += "🎯 Crie um plano de ação urgente\n"
    
    await update.message.reply_text(response, reply_markup=analise_keyboard())

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para mostrar o menu"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return
    
    await update.message.reply_text(
        "🏠 **MENU PRINCIPAL**\n\n"
        "💼 **Seu Assistente Financeiro Pessoal**\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=main_keyboard()
    )

# ========== HANDLER PRINCIPAL ==========

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal atualizado para o menu - CORRIGIDO"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("❌ Você precisa se cadastrar primeiro. Use /start para começar.")
        return ConversationHandler.END
    
    # CORREÇÃO: Inicializar user_data com user_id e nickname
    context.user_data['user_id'] = user_id
    context.user_data['nickname'] = db.get_user_nickname(user_id)
    
    logger.info(f"Main menu handler recebeu: {text}")
    
    # Menu Principal
    if text == '💸 Registrar Gastos':
        await update.message.reply_text(
            "💸 **REGISTRAR GASTOS**\n\n"
            "Selecione o tipo de gasto que deseja registrar:",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
        
    elif text == '📊 Meu Resumo':
        await resumo_command(update, context)
        return ConversationHandler.END
        
    elif text == '📈 Saúde Financeira':
        await analisar_command(update, context)
        return ConversationHandler.END
        
    elif text == '🎓 Educação Financeira':
        await educacao_handler(update, context)
        return ConversationHandler.END
        
    elif text == '⚙️ Configurações':
        await configuracoes_handler(update, context)
        return ConversationHandler.END
        
    elif text == '❓ Ajuda':
        await ajuda_handler(update, context)
        return ConversationHandler.END

    # Submenu de Gastos
    elif text == '🏠 Gastos Fixos':
        return await iniciar_registro_gasto(update, context)
        
    elif text == '🛍️ Gastos Flexíveis':
        return await iniciar_registro_gasto(update, context)
        
    elif text == '📅 Gastos do Mês':
        await update.message.reply_text(
            "📅 **GASTOS DO MÊS**\n\n"
            "🔧 **Funcionalidade em desenvolvimento**\n\n"
            "💡 Em breve você poderá ver seus gastos organizados por mês!",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END
        
    elif text == '📋 Categorias':
        await update.message.reply_text(
            "📋 **CATEGORIAS**\n\n"
            "🔧 **Funcionalidade em desenvolvimento**\n\n"
            "💡 Em breve você poderá gerenciar suas categorias personalizadas!",
            reply_markup=gastos_keyboard()
        )
        return ConversationHandler.END

    # Configurações
    elif text == '✏️ Editar Perfil':
        return await edit_profile_handler(update, context)
        
    elif text == '💰 Alterar Salário':
        return await edit_salary_handler(update, context)
        
    elif text == '📁 Exportar Dados':
        await export_data_handler(update, context)
        return ConversationHandler.END
        
    elif text == '🔄 Redefinir':
        return await reset_data_handler(update, context)
        
    elif text == '🏠 Voltar ao Menu':
        await update.message.reply_text(
            "🏠 **MENU PRINCIPAL**\n\n"
            "O que gostaria de fazer?",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END

    # Ajuda
    elif text == '📝 Como Usar':
        await help_how_to_use_handler(update, context)
        return ConversationHandler.END
        
    elif text == '❓ Perguntas Frequentes':
        await update.message.reply_text(
            "❓ **PERGUNTAS FREQUENTES**\n\n"
            "🤔 **P: Meus dados estão seguros?**\n"
            "R: Sim! Seus dados ficam armazenados apenas no seu dispositivo.\n\n"
            "💡 **P: Posso usar em outro celular?**\n"
            "R: Sim, faça login com mesma conta Telegram.\n\n"
            "🔧 **Precisa de mais ajuda?** Use 'Reportar Problema'.",
            reply_markup=ajuda_keyboard()
        )
        return ConversationHandler.END
        
    elif text == '🐛 Reportar Problema':
        await report_problem_handler(update, context)
        return ConversationHandler.END
        
    elif text == '💬 Feedback':
        await feedback_handler(update, context)
        return ConversationHandler.END

    # Educação Financeira
    elif text == '💡 Dica do Dia':
        await dica_dia_handler(update, context)
        return ConversationHandler.END
        
    elif text == '📚 Aprender Mais':
        await aprender_mais_handler(update, context)
        return ConversationHandler.END
        
    elif text == '🎯 Meus Objetivos':
        await objetivos_handler(update, context)
        return ConversationHandler.END
        
    elif text == '📖 Glossário':
        await glossario_handler(update, context)
        return ConversationHandler.END

    # Objetivos
    elif text == '🎯 Adicionar Objetivo':
        return await add_goal_handler(update, context)
        
    elif text == '📋 Meus Objetivos':
        await list_goals_handler(update, context)
        return ConversationHandler.END
        
    elif text == '📊 Atualizar Progresso':
        await update.message.reply_text(
            "📊 **ATUALIZAR PROGRESSO**\n\n"
            "🔧 **Funcionalidade em desenvolvimento**\n\n"
            "💡 Em breve você poderá atualizar o progresso dos seus objetivos!\n"
            "Por enquanto, continue acompanhando suas metas! 📈",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END
        
    elif text == '🗑️ Excluir Objetivo':
        await update.message.reply_text(
            "🗑️ **EXCLUIR OBJETIVO**\n\n"
            "🔧 **Funcionalidade em desenvolvimento**\n\n"
            "💡 Em breve você poderá excluir objetivos!\n"
            "Por enquanto, continue acompanhando seus progressos! 📈",
            reply_markup=objetivos_keyboard()
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "❌ **Comando não reconhecido**\n\n"
            "💡 Use os botões do menu para navegar.",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END