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

    # 1. CADASTRO INICIAL
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
            CommandHandler('start', h.start),
            MessageHandler(filters.ALL, lambda u, c: u.message.reply_text("❌ Operação inválida. Use /cancel para cancelar ou continue o cadastro."))
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="cadastro_conv"
    )

    # 2. REGISTRAR GASTOS - Handler UNIFICADO
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
            h.DATA_GASTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_date_input),
                # --- CORREÇÃO: Calendário tratado DENTRO da conversa ---
                CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_')
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
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            # Adicionar fallback de callback para o calendário
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="gastos_conv"
    )
    
    # 3. SUAS CATEGORIAS
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

    # 4. CONFIGURAÇÕES
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

    # 5. OBJETIVOS - Handler UNIFICADO
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
            # --- CORREÇÃO: Calendário tratado DENTRO da conversa ---
            h.GOAL_DEADLINE_CALENDAR: [
                CallbackQueryHandler(h.goal_deadline_calendar_handler, pattern='^CAL_')
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="goals_conv"
    )

    # 6. ATUALIZAR PROGRESSO DE OBJETIVOS - Handler UNIFICADO
    update_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(📊 Atualizar Progresso)$'), h.update_goal_progress_handler)
        ],
        states={
            # --- CORREÇÃO: Callbacks DENTRO da conversa ---
            h.SELECT_GOAL: [
                CallbackQueryHandler(h.handle_goal_selection, pattern='^goal_|^cancel_update$')
            ],
            h.UPDATE_GOAL_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.update_goal_value_handler)],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel_update$') 
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="update_goal_conv"
    )

    # 7. EXCLUIR OBJETIVOS - Handler UNIFICADO
    delete_goal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🗑️ Excluir Objetivo)$'), h.delete_goal_handler)
        ],
        states={
            # --- CORREÇÃO: Callbacks DENTRO da conversa ---
            h.SELECT_GOAL_DELETE: [
                CallbackQueryHandler(h.handle_goal_delete_selection, pattern='^delete_goal_|^cancel_delete$')
            ],
            h.CONFIRM_DELETE_GOAL: [
                CallbackQueryHandler(h.handle_confirm_delete_goal, pattern='^confirm_delete_|^cancel_confirm_delete$')
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="delete_goal_conv"
    )
    
    # 8. ADICIONAR SALÁRIO
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

    # 9. ALTERAR SALÁRIOS - Handler UNIFICADO
    edit_salaries_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(✏️ Alterar Salários)$'), h.alterar_salarios_handler)
        ],
        states={
            # Estado para receber cliques nos botões de ação (editar, deletar, etc.)
            h.EDIT_SALARY_SELECT: [
                CallbackQueryHandler(h.edit_salary_callback_handler, pattern='^edit_salary_|^cancel_edit_salary|^edit_origin_|^edit_value_|^make_principal_|^delete_salary_|^cancel_action$')
            ],
            # Estados para receber texto do usuário
            h.EDIT_SALARY_ORIGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_salary_origin_edit)
            ],
            h.EDIT_SALARY_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.process_salary_value_edit)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel_action$'),
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="edit_salaries_conv"
    )

    # 10. ADICIONAR RENDA EXTRA
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

    # 11. ALTERAR RENDAS EXTRAS
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

    # 12. EXTRATO MENSAL - Handler UNIFICADO
    extrato_main_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^(🧾 Meu Extrato)$'), h.extrato_gastos_handler),
        ],
        states={
            h.EXTRATO_MES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.handle_month_year_input),
                # --- CORREÇÃO: Calendário tratado DENTRO da conversa ---
                CallbackQueryHandler(h.MonthYearCalendar.handle_callback, pattern='^(EXTRATO_|MY_)')
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r'^(🏠 Voltar ao Menu)$'), h.voltar_menu_handler),
            CommandHandler('menu', h.menu_command),
            CommandHandler('cancel', h.cancel),
            CallbackQueryHandler(h.cancel_callback, pattern='^cancel$')
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
        name="extrato_main_conv"
    )

    # ========== REGISTRO DE HANDLERS ==========

    # --- CORREÇÃO: REMOVER HANDLERS GLOBAIS DE CALLBACK QUE CAUSAM CONFLITO ---
    # application.add_handler(CallbackQueryHandler(h.handle_analise_callback, pattern='^analise_'))
    # application.add_handler(CallbackQueryHandler(h.handle_modulos_callback, pattern='^modulo_'))
    # application.add_handler(CallbackQueryHandler(h.Calendar.handle_callback, pattern='^CAL_'))
    # application.add_handler(CallbackQueryHandler(h.MonthYearCalendar.handle_callback, pattern='^(MY_|EXTRATO_)'))
    
    # --- CORREÇÃO: Adicionar handlers de callback GLOBAIS (que não são de conversa) ---
    application.add_handler(CallbackQueryHandler(h.handle_analise_callback, pattern='^analise_'))
    application.add_handler(CallbackQueryHandler(h.handle_modulos_callback, pattern='^modulo_'))
    
    # 1. CONVERSATION HANDLERS (Unificados e Corrigidos)
    application.add_handler(gastos_conv_handler)
    application.add_handler(suas_categorias_conv_handler)
    application.add_handler(cadastro_conv_handler)
    application.add_handler(config_conv_handler)
    application.add_handler(goals_conv_handler)
    application.add_handler(update_goal_conv_handler)
    application.add_handler(delete_goal_conv_handler)
    application.add_handler(extrato_main_handler)
    application.add_handler(add_salary_conv_handler)
    application.add_handler(edit_salaries_conv_handler) # Handler unificado de edição de salário
    application.add_handler(add_extra_income_conv_handler)
    application.add_handler(edit_extra_incomes_handler)

    # --- CORREÇÃO: REMOVER TODOS OS HANDLERS SEPARADOS E DUPLICADOS ---
    # (gastos_calendario_handler já foi removido)
    # (goals_calendario_handler foi removido)
    # (update_goal_select_handler foi removido)
    # (delete_goal_select_handler foi removido)
    # (extrato_calendario_handler foi removido)
    # (edit_salaries_main_handler, edit_salary_details_handler, etc. foram unificados)

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

    # 3. MESSAGE HANDLERS ESPECÍFICOS (Que não são conversas)
    # Saúde Financeira
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Ver Métricas)$'), h.ver_metricas_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🧠 Recomendações IA)$'), h.recomendacoes_ia_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📈 Análise Detalhada com IA)$'), h.analise_detalhada_ia_handler))
    
    # Objetivos
    application.add_handler(MessageHandler(filters.Regex(r'^(📋 Meus Objetivos)$'), h.meus_objetivos_handler))
    
    # Salários e Rendas
    application.add_handler(MessageHandler(filters.Regex(r'^(💰 Salário)$'), h.salario_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(💵 Renda extra)$'), h.renda_extra_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Consultar Salários)$'), h.consultar_salarios_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📊 Consultar Rendas Extras)$'), h.consultar_rendas_extras_handler))

    # 6. MAIN MENU HANDLER (SEMPRE O ÚLTIMO)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        h.main_menu_handler
    ))

    # ========== INICIALIZAÇÃO ==========
    
    print("=" * 60)
    print("🎉 BOT DE FINANÇAS INICIADO COM SUCESSO! (v.Corrigida)")
    print("🕐 Horário: " + datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("📱 Bot está rodando e aguardando mensagens...")
    print("🔧 Todos os Handlers de Conversa foram unificados.")
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