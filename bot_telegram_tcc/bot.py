# bot.py - VERSÃO FINAL CORRIGIDA
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import config
import database as db
import handlers as h
import datetime
import logging
import sys

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Função principal do bot"""
    print("🤖 Inicializando Bot de Finanças Pessoais...")
    print("=" * 60)
    
    # Verificar token
    if config.BOT_TOKEN == "SEU_TOKEN_AQUI":
        print("❌ ERRO: Configure o BOT_TOKEN no arquivo config.py")
        return
    
    # Inicializar banco de dados
    try:
        success = db.init_db()
        if not success:
            print("❌ Falha ao inicializar banco de dados")
            return
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return

    # Criar aplicação
    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        print("✅ Aplicação do bot criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar aplicação: {e}")
        return

    # Conversation Handler para CADASTRO INICIAL
    cadastro_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', h.start)],
        states={
            h.GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_name)],
            h.GET_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_salary)],
            h.TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.tipo_gasto_handler)],
            h.CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_fixa_handler)],
            h.CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_flexivel_handler)],
            h.NOVA_CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_fixa_handler)],
            h.NOVA_CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_flexivel_handler)],
            h.VALOR_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.valor_gasto_handler)],
            h.DATA_GASTO: [
                CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_date_input)
            ],
            h.CONTINUAR_GASTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.continuar_gastos_handler)],
            h.RESUMO_GASTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.resumo_gastos_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="cadastro_conv"
    )

    # Conversation Handler para REGISTRAR GASTOS (após cadastro)
    gastos_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🏠 Gastos Fixos|🛍️ Gastos Flexíveis)$'), h.iniciar_registro_gasto)
        ],
        states={
            h.CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_fixa_handler)],
            h.CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_flexivel_handler)],
            h.NOVA_CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_fixa_handler)],
            h.NOVA_CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_flexivel_handler)],
            h.VALOR_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.valor_gasto_handler)],
            h.DATA_GASTO: [
                CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_date_input)
            ],
            h.CONTINUAR_GASTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.continuar_gastos_handler)],
            h.RESUMO_GASTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.resumo_gastos_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="gastos_conv"
    )

    # Conversation Handler para CONFIGURAÇÕES
    config_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(✏️ Editar Perfil|💰 Alterar Salário|🔄 Redefinir)$'), h.main_menu_handler)
        ],
        states={
            h.EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.edit_name_handler)],
            h.EDIT_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.edit_salary_process_handler)],
            h.CONFIRM_RESET: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.confirm_reset_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="config_conv"
    )

    # Conversation Handler para OBJETIVOS
    goals_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🎯 Adicionar Objetivo)$'), h.main_menu_handler)
        ],
        states={
            h.GOAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_type_handler)],
            h.GOAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_description_handler)],
            h.GOAL_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_target_handler)],
            h.GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_deadline_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="goals_conv"
    )

    # Adicionar handlers NA ORDEM CORRETA
    application.add_handler(cadastro_conv_handler)
    application.add_handler(gastos_conv_handler)
    application.add_handler(config_conv_handler)
    application.add_handler(goals_conv_handler)
    
    # Comandos simples
    application.add_handler(CommandHandler("analisar", h.analisar_command))
    application.add_handler(CommandHandler("resumo", h.resumo_command))
    application.add_handler(CommandHandler("menu", h.menu_command))
    application.add_handler(CommandHandler("adicionar", h.adicionar_gastos_handler))

    # Handler para menu principal (DEVE SER O ÚLTIMO)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        h.main_menu_handler
    ))

    # Informações de inicialização
    print("=" * 60)
    print("🎉 BOT DE FINANÇAS INICIADO COM SUCESSO!")
    print(f"🕐 Horário: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("📱 Bot está rodando e aguardando mensagens...")
    print("🔧 **TODAS AS FUNCIONALIDADES DISPONÍVEIS:**")
    print("   • ✅ Cadastro de usuários")
    print("   • ✅ Adição de gastos fixos e flexíveis")
    print("   • ✅ Calendário interativo")
    print("   • ✅ Resumo financeiro")
    print("   • ✅ Análise de saúde financeira")
    print("   • ✅ Configurações (Editar Perfil, Alterar Salário, etc.)")
    print("   • ✅ Sistema de Objetivos Financeiros")
    print("   • ✅ Educação Financeira (Dicas, Glossário)")
    print("   • ✅ Sistema de Ajuda Completo")
    print("⏹️  Pressione Ctrl+C para parar o bot")
    print("=" * 60)

    # Iniciar bot
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
    finally:
        print("✅ Bot finalizado!")

if __name__ == '__main__':
    main()