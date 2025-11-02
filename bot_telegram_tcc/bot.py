from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import config
import database as db
import handlers as h
import datetime
import logging
import sys
import coach

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

    # ========== CONVERSATION HANDLERS OTIMIZADOS ==========

    # 1. CADASTRO INICIAL (sem CallbackQueryHandler)
    cadastro_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', h.start)],
        states={
            h.GET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_name),
                MessageHandler(filters.ALL, lambda u, c: u.message.reply_text("❌ Por favor, digite apenas texto para seu nome."))
            ],
            h.GET_SALARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_salary),
                MessageHandler(filters.ALL, lambda u, c: u.message.reply_text("❌ Por favor, digite um valor numérico para o salário."))
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CommandHandler('start', h.start),  # Permite reiniciar o cadastro
            MessageHandler(filters.ALL, lambda u, c: u.message.reply_text("❌ Operação inválida. Use /cancel para cancelar ou continue o cadastro."))
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="cadastro_conv"
    )

    # 2. REGISTRAR GASTOS - Handler principal para gastos
    gastos_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🧮 Gastos / Rendas)$'), h.adicionar_gastos_handler),
            MessageHandler(filters.Regex(r'^(🏠 Gastos Fixos|🛍️ Gastos Flexíveis)$'), h.iniciar_registro_gasto)
        ],
        states={
            h.TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.tipo_gasto_gastos_conv_handler)],
            h.CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_fixa_handler)],
            h.CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.categoria_flexivel_handler)],
            h.NOVA_CATEGORIA_FIXA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_fixa_handler)],
            h.NOVA_CATEGORIA_FLEXIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.nova_categoria_flexivel_handler)],
            h.VALOR_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.valor_gasto_handler)],
            h.DATA_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_date_input)],
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

    # Handler separado para calendário de gastos - CORRIGIDO
    gastos_calendario_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_')
        ],
        states={
            h.DATA_GASTO: [
                CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_date_input)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$'),
            CommandHandler('cancel', h.cancel)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="gastos_calendario_conv"
    )

    
    # 3. SUAS CATEGORIAS (sem CallbackQueryHandler)
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

    # 4. CONFIGURAÇÕES (sem CallbackQueryHandler)
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

    # 5. OBJETIVOS - Handler principal (sem calendário)
    goals_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🎯 Adicionar Objetivo)$'), h.add_goal_handler)
        ],
        states={
            h.GOAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_type_handler)],
            h.GOAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_description_handler)],
            h.GOAL_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_target_handler)],
            h.GOAL_DEADLINE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_deadline_manual_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="goals_conv"
    )

    # ✅ CORREÇÃO DO CALENDÁRIO DE OBJETIVOS:
    goals_calendario_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.goal_deadline_calendar_handler, pattern='^CAL_')
        ],
        states={
            h.GOAL_DEADLINE_CALENDAR: [
                CallbackQueryHandler(h.goal_deadline_calendar_handler, pattern='^CAL_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.goal_deadline_manual_handler)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$'),
            CommandHandler('cancel', h.cancel)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="goals_calendario_conv"
    )

    # 6. ATUALIZAR PROGRESSO DE OBJETIVOS - Handler separado
    update_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(📊 Atualizar Progresso)$'), h.update_goal_progress_handler)
        ],
        states={
            h.UPDATE_GOAL_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.update_goal_value_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="update_goal_conv"
    )

    # Handler separado para seleção de objetivos (CallbackQueryHandler)
    update_goal_select_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.handle_goal_selection, pattern='^goal_')
        ],
        states={
            h.SELECT_GOAL: [CallbackQueryHandler(h.handle_goal_selection, pattern='^goal_')],
        },
        fallbacks=[CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="update_goal_select_conv"
    )

    # 7. EXCLUIR OBJETIVOS - Handler separado
    delete_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🗑️ Excluir Objetivo)$'), h.delete_goal_handler)
        ],
        states={
            h.CONFIRM_DELETE_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.confirm_reset_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="delete_goal_conv"
    )

    # Handler separado para seleção de exclusão (CallbackQueryHandler)
    delete_goal_select_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.handle_goal_delete_selection, pattern='^delete_goal_'),
            CallbackQueryHandler(h.handle_confirm_delete_goal, pattern='^confirm_delete_')
        ],
        states={
            h.SELECT_GOAL_DELETE: [CallbackQueryHandler(h.handle_goal_delete_selection, pattern='^delete_goal_')],
            h.CONFIRM_DELETE_GOAL: [CallbackQueryHandler(h.handle_confirm_delete_goal, pattern='^confirm_delete_')],
        },
        fallbacks=[CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="delete_goal_select_conv"
    )

    # 8. ADICIONAR SALÁRIO (sem CallbackQueryHandler)
    add_salary_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(💵 Adicionar Salário)$'), h.add_salary_handler)
        ],
        states={
            h.ADD_SALARY_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_salary_origin_handler)],
            h.ADD_SALARY_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_salary_value_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="add_salary_conv"
    )

    add_salary_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^💵 Adicionar Salário$'), h.add_salary_handler)],
        states={
            h.ADD_SALARY_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_salary_origin_handler)],
            h.ADD_SALARY_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_salary_value_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        per_message=True
    )

    # Handler para consultar salários
    consultar_salarios_handler = MessageHandler(filters.Regex('^📊 Consultar Salários$'), h.consultar_salarios_handler)

    # Handler para alterar salários
    alterar_salarios_handler = MessageHandler(filters.Regex('^✏️ Alterar Salários$'), h.alterar_salarios_handler)

    # Handler para callbacks de salário
    salary_callback_handler = CallbackQueryHandler(
        h.edit_salary_callback_handler, 
        pattern='^edit_salary_|^cancel_edit_salary|^edit_origin_|^edit_value_|^make_principal_|^delete_salary_|^cancel_action'
    )

    # 9. ALTERAR SALÁRIOS - Handler separado
    edit_salaries_main_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(✏️ Alterar Salários)$'), h.alterar_salarios_handler)
        ],
        states={
            # ✅ CORREÇÃO: Remover estados problemáticos e usar apenas callbacks
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="edit_salaries_main_conv"
    )

    # ✅ Handler para callbacks de salário (REMOVER os padrões de edição)
    edit_salaries_callback_handler = CallbackQueryHandler(
        h.edit_salary_callback_handler, 
        pattern='^edit_salary_|^cancel_edit_salary|^make_principal_|^delete_salary_|^cancel_action'
    )

    # ✅ CONVERSATION HANDLER PARA EDIÇÃO DE SALÁRIOS (VERSÃO CORRIGIDA)
    edit_salary_details_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.handle_edit_origin, pattern='^edit_origin_'),
            CallbackQueryHandler(h.handle_edit_value, pattern='^edit_value_')
        ],
        states={
            h.EDIT_SALARY_ORIGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_salary_origin_edit)
            ],
            h.EDIT_SALARY_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_salary_value_edit)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel_action'),
            MessageHandler(filters.Regex(r'^(🏠 Voltar ao Menu|/menu|/start)'), h.voltar_menu_handler)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="edit_salary_details_conv"
    )

    # 10. ADICIONAR RENDA EXTRA (sem CallbackQueryHandler)
    add_extra_income_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(💵 Adicionar Renda Extra)$'), h.add_extra_income_handler)
        ],
        states={
            h.ADD_EXTRA_INCOME_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_extra_income_origin_handler)],
            h.ADD_EXTRA_INCOME_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.add_extra_income_value_handler)],
        },
        fallbacks=[CommandHandler('cancel', h.cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="add_extra_income_conv"
    )

    # 11. ALTERAR RENDAS EXTRAS - Handler simplificado
    edit_extra_incomes_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(✏️ Alterar Rendas Extras)$'), h.alterar_rendas_extras_handler)
        ],
        states={
            h.EDIT_EXTRA_INCOME_SELECT: [
                CallbackQueryHandler(h.edit_extra_income_select_handler, pattern='^edit_extra_income_|^cancel_edit_extra_income')
            ],
            h.EDIT_EXTRA_INCOME_ACTION: [
                CallbackQueryHandler(h.edit_extra_income_action_handler, pattern='^edit_extra_origin|^edit_extra_value|^delete_extra_income|^cancel_extra_action')
            ],
            h.EDIT_EXTRA_INCOME_ORIGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.edit_extra_income_origin_handler)
            ],
            h.EDIT_EXTRA_INCOME_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.edit_extra_income_value_handler)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            MessageHandler(filters.Regex(r'^(🏠 Voltar ao Menu)$'), h.voltar_menu_handler)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="edit_extra_incomes_conv"
    )

    # 12. EXTRATO MENSAL - Handler separado
    extrato_main_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🧾 Meu Extrato)$'), h.extrato_gastos_handler),
        ],
        states={
            h.EXTRATO_MES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_month_year_input)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r'^(🏠 Voltar ao Menu)$'), h.voltar_menu_handler),
            CommandHandler('menu', h.menu_command),
            CommandHandler('cancel', h.cancel)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="extrato_main_conv"
    )

    # Handler separado para calendário do extrato
    extrato_calendario_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(h.MonthYearCalendar.handle_callback, pattern='^(EXTRATO_|MY_)')
        ],
        states={
            h.EXTRATO_MES: [
                CallbackQueryHandler(h.MonthYearCalendar.handle_callback, pattern='^(EXTRATO_|MY_)'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_month_year_input)
            ],
        },
        fallbacks=[CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="extrato_calendario_conv"
    )

    # ========== REGISTRO DE HANDLERS ==========

    # 4. CALLBACK HANDLERS (PRIMEIRO - são mais específicos)
    application.add_handler(CallbackQueryHandler(h.handle_analise_callback, pattern='^analise_'))
    application.add_handler(CallbackQueryHandler(h.handle_modulos_callback, pattern='^modulo_'))
    application.add_handler(CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_'))
    application.add_handler(CallbackQueryHandler(h.MonthYearCalendar.handle_callback, pattern='^(MY_|EXTRATO_)'))
    
    # ✅ CORREÇÃO: Adicionar handlers de callback separados
    application.add_handler(edit_salaries_callback_handler)

    # 1. CONVERSATION HANDLERS (por ordem de especificidade)   
    application.add_handler(gastos_calendario_handler)
    application.add_handler(gastos_conv_handler)
    application.add_handler(suas_categorias_conv_handler)
    application.add_handler(cadastro_conv_handler) #novo
    application.add_handler(config_conv_handler)
    application.add_handler(goals_conv_handler)
    application.add_handler(update_goal_conv_handler)
    application.add_handler(goals_calendario_handler)
    application.add_handler(update_goal_select_handler)
    application.add_handler(delete_goal_conv_handler)
    application.add_handler(delete_goal_select_handler)
    application.add_handler(extrato_main_handler)
    application.add_handler(extrato_calendario_handler)
    application.add_handler(add_salary_conv_handler)
    application.add_handler(edit_salaries_main_handler)
    application.add_handler(edit_salary_details_handler)  # ✅ ADICIONAR ESTE
    application.add_handler(add_extra_income_conv_handler)
    application.add_handler(edit_extra_incomes_handler)

    # 2. COMMAND HANDLERS
    application.add_handler(CommandHandler("start", h.start))
    application.add_handler(CommandHandler("menu", h.menu_command))
    application.add_handler(CommandHandler("ajuda", h.ajuda_handler))
    application.add_handler(CommandHandler("cancel", h.cancel))
    application.add_handler(CommandHandler("analisar", h.analise_detalhada_handler))
    application.add_handler(CommandHandler("resumo", h.resumo_gastos_handler))
    application.add_handler(CommandHandler("adicionar", h.adicionar_gastos_handler))
    application.add_handler(CommandHandler("analise_detalhada", h.analise_detalhada_handler))
    application.add_handler(CommandHandler("salarios", h.consultar_salarios_handler))
    application.add_handler(CommandHandler("rendas", h.consultar_rendas_extras_handler))
    application.add_handler(CommandHandler("extrato", h.extrato_gastos_handler))

    # 3. MESSAGE HANDLERS ESPECÍFICOS
    # Saúde Financeira
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Ver Métricas Detalhadas)$'), h.ver_metricas_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🧠 Recomendações IA)$'), h.recomendacoes_ia_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📈 Análise Detalhada com IA)$'), h.analise_detalhada_ia_handler))
    
    # Objetivos
    application.add_handler(MessageHandler(filters.Regex(r'^(📋 Meus Objetivos)$'), h.meus_objetivos_handler))
    
    # Salários e Rendas
    application.add_handler(MessageHandler(filters.Regex(r'^(💰 Salário)$'), h.salario_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(💵 Renda extra)$'), h.renda_extra_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Consultar Salários)$'), h.consultar_salarios_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Consultar Rendas Extras)$'), h.consultar_rendas_extras_handler))
    
    # Educação Financeira
    application.add_handler(MessageHandler(filters.Regex(r'^(💡 Dica do Dia)$'), h.dica_do_dia_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📚 Glossário)$'), h.glossario_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🎓 Módulos Educativos)$'), h.modulos_educativos_handler))

    # 6. MAIN MENU HANDLER (SEMPRE O ÚLTIMO)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        h.main_menu_handler
    ))

    # ========== INICIALIZAÇÃO ==========
    
    # Informações de inicialização
    print("=" * 60)
    print("🎉 BOT DE FINANÇAS INICIADO COM SUCESSO!")
    print("🕐 Horário: " + datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("📱 Bot está rodando e aguardando mensagens...")
    print("🔧 **TODAS AS FUNCIONALIDADES DISPONÍVEIS:**")
    print("   • ✅ Cadastro de usuários")
    print("   • ✅ Adição de gastos fixos e flexíveis")
    print("   • ✅ Calendário interativo para gastos")
    print("   • ✅ Resumo financeiro")
    print("   • ✅ Análise de saúde financeira")
    print("   • ✅ Análise detalhada com IA")
    print("   • ✅ Configurações (Editar Perfil, Alterar Salário, etc.)")
    print("   • ✅ Sistema de Objetivos Financeiros")
    print("   • ✅ Educação Financeira (Dicas, Glossário, Módulos)")
    print("   • ✅ Sistema de Salários e Rendas Extras")
    print("   • ✅ EXTRATO MENSAL com calendário")
    print("   • ✅ Sistema de Ajuda Completo")
    print("⏹️  Pressione Ctrl+C para parar o bot")
    print("=" * 60)
    
    # Iniciar bot
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query', 'chat_member']
        )
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        print(f"❌ Erro durante a execução: {str(e)}")
    finally:
        print("✅ Bot finalizado!")

if __name__ == '__main__':
    main()