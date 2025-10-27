from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import BotCommand
import config
import database as db
import handlers as h
import datetime
import logging

# Configuração de logging RÁPIDA
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)

async def set_commands(application):
    """Configura o menu de comandos da barra"""
    commands = [
        BotCommand("start", "🎯 Iniciar conversa com o Edu"),
        BotCommand("cancel", "❌ Cancelar operação atual"),
        BotCommand("extrato", "📊 Ver extrato de gastos"),
        BotCommand("resumo", "📈 Ver resumo financeiro")
    ]
    await application.bot.set_my_commands(commands)

def main():
    print("🚀 INICIANDO EDU (COM MENU DE COMANDOS)...")
    
    # Inicialização RÁPIDA
    try:
        db.init_db()
        print("✅ BD pronto!")
    except Exception as e:
        print(f"❌ BD: {e}")
        return

    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        print("✅ Bot pronto!")
    except Exception as e:
        print(f"❌ Bot: {e}")
        return

    # ConversationHandler CORRIGIDO - menu consistente
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', h.start)],
        states={
            # Fluxo principal
            h.GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_name)],
            h.GET_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_salary)],
            
            # Classificação de gastos
            h.GET_EXPENSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_expense_type)],
            h.GET_FIXED_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_subcategory)],
            h.GET_FLEXIBLE_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_subcategory)],
            h.GET_NEW_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_new_subcategory)],
            h.GET_EXPENSE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_expense_value)],
            h.GET_EXPENSE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_expense_date)],
            
            # Continuação e resumo
            h.CONTINUE_ADDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_continue_choice)],
            h.SHOW_SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_summary_choice)],
            h.FINANCIAL_HEALTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.financial_health)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
    )

    application.add_handler(conv_handler)
    
    # Adiciona handlers para comandos diretos
    application.add_handler(CommandHandler("extrato", h.extrato_command))
    application.add_handler(CommandHandler("resumo", h.resumo_command))
    application.add_handler(CommandHandler("ajuda", h.ajuda_command))

    # Configura o menu de comandos
    application.post_init = set_commands

    print(f"⏰ {datetime.datetime.now().strftime('%H:%M:%S')} - Bot rodando...")
    print("📍 Ctrl+C para parar")

    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n🛑 Parado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        print("✅ Finalizado!")

if __name__ == '__main__':
    main()