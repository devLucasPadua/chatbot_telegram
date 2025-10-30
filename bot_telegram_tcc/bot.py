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
        
        # CORREÇÃO: Executar correção de dados dos objetivos
        print("🔧 Verificando e corrigindo dados dos objetivos...")
        db.fix_goals_data()
        
    except Exception as e:
        print(f"Erro na inicialização do banco: {str(e)}")
        return

    # Criar aplicação
    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        print("✅ Aplicação do bot criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar aplicação do bot: {e}")
        return

    # Conversation Handler para CADASTRO INICIAL
    cadastro_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', h.start)],
        states={
            h.GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_name)],
            h.GET_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_salary)],
            h.TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.tipo_gasto_handler)],
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
            h.TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.tipo_gasto_gastos_conv_handler)],
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
            h.OUTROS_FLEXIVEIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.outros_flexiveis_handler)],
            h.MINHAS_CATEGORIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.minhas_categorias_handler)],
            h.NOVA_CATEGORIA_OUTROS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_outros_handler)],
            h.CONFIRM_GASTO_OUTROS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.confirm_gasto_outros_handler)],
            h.OUTROS_FIXOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.outros_fixos_handler)],
            h.MINHAS_CATEGORIAS_FIXAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.minhas_categorias_fixas_handler)],
            h.NOVA_CATEGORIA_OUTROS_FIXOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_outros_fixos_handler)],
            h.CONFIRM_GASTO_OUTROS_FIXOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.confirm_gasto_outros_fixos_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="gastos_conv"
    )

    # Conversation Handler para SUAS CATEGORIAS
    suas_categorias_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(📂 Suas Categorias)$'), h.suas_categorias_handler)
        ],
        states={
            h.SUAS_CATEGORIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.suas_categorias_menu_handler)],
            h.CATEGORIAS_FIXAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categorias_fixas_handler)],
            h.CATEGORIAS_FLEXIVEIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categorias_flexiveis_handler)],
            h.SELECIONAR_CATEGORIA_EXCLUIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.selecionar_categoria_excluir_handler)],
            h.CONFIRMAR_EXCLUSAO_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.confirmar_exclusao_categoria_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="suas_categorias_conv"
    )

    # Conversation Handler para CONFIGURAÇÕES
    config_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(✏️ Editar Perfil)$'), h.edit_profile_handler),
            MessageHandler(filters.Regex(r'^(💰 Alterar Salário)$'), h.edit_salary_handler),
            MessageHandler(filters.Regex(r'^(🔄 Redefinir)$'), h.reset_data_handler)
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
    
    # Conversation Handler para OBJETIVOS - COM CALENDÁRIO
    goals_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🎯 Adicionar Objetivo)$'), h.add_goal_handler)
        ],
        states={
            h.GOAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_type_handler)],
            h.GOAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_description_handler)],
            h.GOAL_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_target_handler)],
            h.GOAL_DEADLINE: [
                # Handler para entrada manual de data
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_deadline_manual_handler)
            ],
            h.GOAL_DEADLINE_CALENDAR: [
                # Handler para calendário interativo
                CallbackQueryHandler(h.goal_deadline_calendar_handler, pattern='^CAL_')
            ],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="goals_conv"
    )

    # Conversation Handler para ATUALIZAR PROGRESSO DE OBJETIVOS
    update_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(📊 Atualizar Progresso)$'), h.update_goal_progress_handler)
        ],
        states={
            h.SELECT_GOAL: [CallbackQueryHandler(h.handle_goal_selection, pattern='^goal_')],
            h.UPDATE_GOAL_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.update_goal_value_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="update_goal_conv"
    )

    # Conversation Handler para EXCLUIR OBJETIVOS
    delete_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🗑️ Excluir Objetivo)$'), h.delete_goal_handler)
        ],
        states={
            h.SELECT_GOAL_DELETE: [CallbackQueryHandler(h.handle_goal_delete_selection, pattern='^delete_goal_')],
            h.CONFIRM_DELETE_GOAL: [CallbackQueryHandler(h.handle_confirm_delete_goal, pattern='^confirm_delete_')],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="delete_goal_conv"
    )

    # Conversation Handler para GASTOS DO MÊS - VERSÃO SIMPLIFICADA
    gastos_mes_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(📅 Gastos do Mês)$'), h.gastos_mes_handler)
        ],
        states={
            h.GASTOS_MES: [
                # Handler único para TODOS os callbacks do calendário
                CallbackQueryHandler(h.MonthYearCalendar.handle_callback)
            ],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="gastos_mes_conv"
    )
    
    # Adicionar handlers NA ORDEM CORRETA
    application.add_handler(cadastro_conv_handler)
    application.add_handler(gastos_conv_handler)
    application.add_handler(suas_categorias_conv_handler)
    application.add_handler(config_conv_handler)
    application.add_handler(goals_conv_handler)
    application.add_handler(update_goal_conv_handler)
    application.add_handler(delete_goal_conv_handler)
    application.add_handler(gastos_mes_conv_handler)
    
    # Comandos simples
    application.add_handler(CommandHandler("analisar", h.analise_detalhada_handler))
    application.add_handler(CommandHandler("resumo", h.resumo_gastos_handler))
    application.add_handler(CommandHandler("menu", h.menu_command))
    application.add_handler(CommandHandler("adicionar", h.adicionar_gastos_handler))
    application.add_handler(CommandHandler("analise_detalhada", h.analise_detalhada_handler))
    
    # HANDLERS SIMPLES PARA SAÚDE FINANCEIRA
    application.add_handler(MessageHandler(
        filters.Regex(r'^(📊 Ver Métricas Detalhadas)$'), 
        h.ver_metricas_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r'^(🧠 Recomendações IA)$'), 
        h.recomendacoes_ia_handler
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r'^(📈 Análise Detalhada com IA)$'), 
        h.analise_detalhada_ia_handler
    ))
    
    # Handler para Meus Objetivos
    application.add_handler(MessageHandler(
        filters.Regex(r'^(📋 Meus Objetivos)$'), 
        h.meus_objetivos_handler
    ))
    
    # Handlers para callbacks de análise
    application.add_handler(CallbackQueryHandler(h.handle_analise_callback, pattern='^analise_'))
    
    # Handler para callbacks de módulos educativos
    application.add_handler(CallbackQueryHandler(h.handle_modulos_callback, pattern='^modulo_'))
    
    # Handler para menu principal (DEVE SER O ÚLTIMO)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        h.main_menu_handler
    ))
    
    # Informações de inicialização
    print("=" * 60)
    print("🎉 BOT DE FINANÇAS INICIADO COM SUCESSO!")
    print("🕐 Horário: " + datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("📱 Bot está rodando e aguardando mensagens...")
    print("🔧 **TODAS AS FUNCIONALIDADES DISPONÍVEIS:**")
    print("   • ✅ Cadastro de usuários")
    print("   • ✅ Adição de gastos fixos e flexíveis")
    print("   • ✅ Calendário interativo")
    print("   • ✅ Resumo financeiro")
    print("   • ✅ Análise de saúde financeira")
    print("   • ✅ Análise detalhada com IA")
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
        print(f"❌ Erro durante a execução: {str(e)}")
    finally:
        print("✅ Bot finalizado!")

if __name__ == '__main__':
    main()