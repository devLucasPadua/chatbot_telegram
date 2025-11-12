flowchart TD
  %% Inicialização / Startup
  Start(("Start: bot.py main()"))
  CheckToken{ "config.BOT_TOKEN válido?" }
  InitDB["db.init_db() — cria tabelas"]
  FixGoals["db.fix_goals_data() — corrige goals.progresso"]
  CreateApp["Application.builder().token(...).build()"]
  RegisterHandlers["Registrar handlers (conversation, command, message, callback)"]
  RunPolling["application.run_polling(drop_pending_updates=True, allowed_updates=['message','callback_query','chat_member'])"]

  Start --> CheckToken
  CheckToken -- "não" --> StopToken["Print erro e aborta"]
  CheckToken -- "sim" --> InitDB
  InitDB --> FixGoals
  FixGoals --> CreateApp
  CreateApp --> RegisterHandlers
  RegisterHandlers --> RunPolling

  %% Entrada do usuário e Dispatcher
  UMessage["Usuário envia /start ou mensagem"]
  Dispatcher["Dispatcher -> encontra Handler"]
  StartCmd["/start -> handlers.start"]
  OtherCmds["Outros comandos / botões -> handlers diversos"]

  RunPolling --> UMessage
  UMessage --> Dispatcher
  Dispatcher -->|"/start"| StartCmd
  Dispatcher -->|outros| OtherCmds

  %% Cadastro (start)
  CheckUser{ "db.user_exists(user_id)?" }
  WelcomeReturning["Mostrar main_keyboard() (usuário existente)"]
  AskName["Pedir nome -> estado GET_NAME"]

  StartCmd --> CheckUser
  CheckUser -- "sim" --> WelcomeReturning
  CheckUser -- "não" --> AskName

  GetName["handlers.get_name -> guarda nickname em context.user_data"]
  AskName --> GetName
  GetName --> AskSalary["Pedir salário -> estado GET_SALARY"]
  GetSalary["handlers.get_salary -> valida e cria usuário"]
  AskSalary --> GetSalary
  GetSalary --> ParseSalary{ "salário válido?" }
  ParseSalary -- "não" --> AskSalary
  ParseSalary -- "sim" --> AddUser["db.add_user(user_id,nickname,salario)"]
  AddUser --> AddSalaryPrimary["db.add_salary(... principal=True)"]
  AddSalaryPrimary --> ShowTipoGasto["Mostrar tipo_gasto_keyboard() -> estado TIPO_GASTO"]
  ShowTipoGasto --> MainMenuEntry["Redireciona ao menu principal / TIPO_GASTO"]

  %% Menu principal
  MainMenu["handlers.main_menu_handler -> mostra main_keyboard()"]
  WelcomeReturning --> MainMenu
  MainMenuEntry --> MainMenu

  %% Fluxo Gastos / Rendas (resumido)
  subgraph GASTOS_FLOW ["Gastos / Rendas"]
    direction TB
    EntryGastos["Entrada: '🧮 Gastos / Rendas' ou botões"]
    StartGastos["handlers.adicionar_gastos_handler -> valida user -> mostra gastos_keyboard()"]
    TipoGasto["Estado TIPO_GASTO -> tipo_gasto_handler"]

    EntryGastos --> StartGastos
    StartGastos --> TipoGasto

    Fixos["Escolhe: 'Gastos Fixos' -> set tipo_gasto='fixo' -> categorias_fixas_keyboard() -> estado CATEGORIA_FIXA"]
    Flexiveis["Escolhe: 'Gastos Flexíveis' -> set tipo_gasto='flexivel' -> categorias_flexiveis_keyboard() -> estado CATEGORIA_FLEXIVEL"]
    Salario["Escolhe: 'Salário' -> chama salario_handler (menu salários)"]
    RendaExtra["Escolhe: 'Renda extra' -> chama renda_extra_handler (menu rendas extra)"]

    TipoGasto -->|Gastos Fixos| Fixos
    TipoGasto -->|Gastos Flexíveis| Flexiveis
    TipoGasto -->|Salário| Salario
    TipoGasto -->|Renda extra| RendaExtra

    %% Categorias -> VALOR -> DATA -> registro
    CategoriaFixa["categoria_fixa_handler -> valida categoria -> pergunta VALOR_GASTO"]
    CategoriaFlex["categoria_flexivel_handler -> valida categoria -> pergunta VALOR_GASTO"]

    Fixos --> CategoriaFixa
    Flexiveis --> CategoriaFlex

    ValorGasto["VALOR_GASTO -> valor_gasto_handler -> valida valor -> context.user_data['valor_gasto']"]
    CategoriaFixa --> ValorGasto
    CategoriaFlex --> ValorGasto

    CalendarView["Mostra Calendar.create_calendar() (InlineKeyboard) -> estado DATA_GASTO"]
    ValorGasto --> CalendarView

    CalendarCallback["CallbackQueryHandler Calendar.handle_callback pattern '^CAL_'"]
    CalendarView --> CalendarCallback

    DaySelect["CAL_DAY -> Calendar.handle_date_selection -> process_date_selection"]
    ManualDate["CAL_MANUAL -> pede digitar data -> handle_date_input (mensagem)"]

    CalendarCallback -->|CAL_DAY| DaySelect
    CalendarCallback -->|CAL_MANUAL| ManualDate

    ProcessTx["process_date_selection -> db.add_transaction(user_id,tipo,categoria,subcategoria,valor,descricao,date_str)"]
    DaySelect --> ProcessTx
    ManualDate --> ProcessTx

    TxSuccess{"db.add_transaction retornou True?"}
    ProcessTx --> TxSuccess
    TxSuccess -- "sim" --> ConfirmRegistered["Envia confirmação e sim_nao_keyboard() -> CONTINUAR_GASTOS"]
    TxSuccess -- "não" --> ErrorRegister["Informa erro e retorna ao menu"]

    Continuar["CONTINUAR_GASTOS -> continuar_gastos_handler"]
    ConfirmRegistered --> Continuar
    Continuar -->|SIM| TipoGasto
    Continuar -->|NÃO| ShowResumo["Gera resumo via db.get_monthly_expenses -> mostra saude_financeira_keyboard()"]
  end

  MainMenu --> EntryGastos

  %% Extrato mensal (MonthYearCalendar)
  subgraph EXTRATO_FLOW ["Extrato Mensal / MonthYearCalendar"]
    direction TB
    ExtratoEntry["Usuário -> '🧾 Meu Extrato' ou callback EXTRATO_SHOW_CALENDAR"]
    ShowMYCalendar["MonthYearCalendar.create_month_year_calendar() -> InlineKeyboard"]
    MYCallback["CallbackQueryHandler MonthYearCalendar.handle_callback pattern ^(MY_|EXTRATO_)"]
    MY_MANUAL["MY_MANUAL -> pede entrada manual -> estado EXTRATO_MES -> handle_month_year_input"]
    MY_MONTH["MY_MONTH -> chama show_month_extrato(year,month)"]
    ShowMonthExtrato["MonthYearCalendar.show_month_extrato -> db.get_monthly_transactions + db.get_user_data -> formata resposta"]
    SendExtrato["Envia/edita mensagem com extrato (agrupa por fixo/flexível, totais, % comprometido)"]

    ExtratoEntry --> ShowMYCalendar
    ShowMYCalendar --> MYCallback
    MYCallback -->|MY_MANUAL| MY_MANUAL
    MYCallback -->|MY_MONTH| MY_MONTH
    MY_MANUAL --> ShowMonthExtrato
    MY_MONTH --> ShowMonthExtrato
    ShowMonthExtrato --> SendExtrato
  end

  MainMenu --> ExtratoEntry

  %% Salários (Add / Edit / Consult)
  subgraph SALARIOS_FLOW ["Salários e Rendas Extras"]
    direction TB
    SalMenu["'💰 Salário' -> salario_handler (menu)"]
    AddSalaryFlow["add_salary_handler -> pede origem -> ADD_SALARY_ORIGIN -> add_salary_origin_handler -> pede valor -> ADD_SALARY_VALUE -> add_salary_value_handler -> db.add_salary(...)"]
    ConsultSalaries["consultar_salarios_handler -> db.get_salaries(user_id) -> exibe lista, total"]
    AlterSalaries["alterar_salarios_handler -> constrói InlineKeyboard com edit_salary_{id} -> estado EDIT_SALARY_SELECT"]
    EditSelectCB["Callback edit_salary_{id} -> edit_salary_select_handler -> mostra ações (edit_origin, edit_value, make_principal, delete_salary) -> estado EDIT_SALARY_ACTION"]
    EditActions["edit_salary_action_handler -> dependendo da ação: solicita novo valor/nome ou executa db.set_principal_salary/db.delete_salary"]
    EditNameVal["EDIT_SALARY_ORIGIN / EDIT_SALARY_VALUE handlers atualizam via db.update_salary"]
    AddSalaryFlow --> ConsultSalaries
    SalMenu --> AddSalaryFlow
    SalMenu --> ConsultSalaries
    SalMenu --> AlterSalaries
    AlterSalaries --> EditSelectCB
    EditSelectCB --> EditActions
    EditActions --> EditNameVal
    EditActions -->|make_principal| SetPrincipal["db.set_principal_salary(salary_id,user_id)"]
    EditActions -->|delete_salary| DeleteSalary["db.delete_salary(salary_id)"]
  end

  MainMenu --> SalMenu

  %% Rendas Extras (Add / Edit / Consult)
  subgraph RENDAS ["Rendas Extras"]
    direction TB
    RendaMenu["'💵 Renda extra' -> renda_extra_handler (menu)"]
    AddExtraFlow["add_extra_income_handler -> pede origem -> ADD_EXTRA_INCOME_ORIGIN -> pede valor -> ADD_EXTRA_INCOME_VALUE -> db.add_extra_income"]
    ConsultExtras["consultar_rendas_extras_handler -> db.get_extra_incomes -> exibe lista + total"]
    AlterExtras["alterar_rendas_extras_handler -> InlineKeyboard edit_extra_income_{id} -> edit_extra_income_select_handler -> ações -> edit_extra_income_action_handler -> db.update_extra_income / db.delete_extra_income"]
    RendaMenu --> AddExtraFlow
    RendaMenu --> ConsultExtras
    RendaMenu --> AlterExtras
  end

  MainMenu --> RendaMenu

  %% Objetivos (Goals)
  subgraph GOALS ["Objetivos Financeiros"]
    direction TB
    GoalsMenu["'🎯 Objetivos' -> objetivos_handler -> mostra objetivos_keyboard()"]
    AddGoalStart["add_goal_handler -> pede tipo (economia_mensal/meta_especifica) -> estado GOAL_TYPE"]
    GoalTypeSel["goal_type_handler -> armazena goal_type -> pede descrição -> estado GOAL_DESCRIPTION"]
    GoalDesc["goal_description_handler -> armazena descricao -> pede valor -> estado GOAL_TARGET"]
    GoalTarget["goal_target_handler -> se economia_mensal -> db.add_goal(tipo='economia_mensal',prazo=None) -> confirma\n else meta_especifica -> mostra Calendar -> estado GOAL_DEADLINE_CALENDAR"]
    GoalDeadlineCB["goal_deadline_calendar_handler -> CAL_DAY_ -> process_goal_creation (db.add_goal tipo='meta_especifica' com prazo)"]
    ViewGoals["meus_objetivos_handler -> db.get_user_goals -> exibe lista com progresso e barra"]
    UpdateProgressStart["update_goal_progress_handler -> lista goals -> InlineButtons goal_{id} -> estado SELECT_GOAL"]
    UpdateProgressCB["handle_goal_selection -> pergunta novo valor -> estado UPDATE_GOAL_PROGRESS -> update_goal_value_handler -> db.update_goal_progress"]
    DeleteGoalStart["delete_goal_handler -> lista goals -> InlineButtons delete_goal_{id} -> estado SELECT_GOAL_DELETE"]
    DeleteGoalCB["handle_goal_delete_selection -> confirma -> handle_confirm_delete_goal -> db.delete_goal"]

    GoalsMenu --> AddGoalStart
    GoalsMenu --> ViewGoals
    GoalsMenu --> UpdateProgressStart
    GoalsMenu --> DeleteGoalStart
    AddGoalStart --> GoalTypeSel
    GoalTypeSel --> GoalDesc
    GoalDesc --> GoalTarget
    GoalTarget -->|meta_especifica| GoalDeadlineCB
    GoalTarget -->|economia_mensal| ConfirmGoalCreated["Confirma criação"] 
  end

  MainMenu --> GoalsMenu

  %% Suas Categorias (personalizadas)
  subgraph CATEGORIES ["Gerenciamento de Categorias Personalizadas"]
    direction TB
    SuasCatsEntry["'📂 Suas Categorias' -> suas_categorias_handler -> suas_categorias_keyboard()"]
    SuasCatsMenu["suas_categorias_menu_handler -> escolha Fixas ou Flexíveis"]
    ListFixWithDelete["categorias_fixas_keyboard_with_delete(user_id) -> mostra categorias '📂 nome' + '🗑️ Excluir Categoria'"]
    ListFlexWithDelete["categorias_flexiveis_keyboard_with_delete(user_id)"]
    SelectDeleteCat["selecionar_categoria_excluir_handler -> mostra confirmação com stats -> estado CONFIRMAR_EXCLUSAO_CATEGORIA"]
    ConfirmDeleteCat["confirmar_exclusao_categoria_handler -> se SIM -> db.delete_custom_category -> informa sucesso; se NÃO -> cancela"]

    SuasCatsEntry --> SuasCatsMenu
    SuasCatsMenu --> ListFixWithDelete
    SuasCatsMenu --> ListFlexWithDelete
    ListFixWithDelete --> SelectDeleteCat
    ListFlexWithDelete --> SelectDeleteCat
    SelectDeleteCat --> ConfirmDeleteCat
  end

  MainMenu --> SuasCatsEntry

  %% Configurações e Perfil
  subgraph CONFIG ["Configurações"]
    direction TB
    ConfigEntry["'⚙️ Configurações' -> config_conv_handler -> config_keyboard()"]
    EditProfile["✏️ Editar Perfil -> edit_profile_handler -> pede novo nome -> edit_name_handler -> db.update_user_nickname"]
    EditSalary["💰 Alterar Salário -> edit_salary_handler -> pede novo valor -> edit_salary_process_handler -> db.update_user_salary"]
    ResetData["🔄 Redefinir -> reset_data_handler -> confirma -> confirm_reset_handler -> db.reset_user_data(user_id)"]
    ConfigEntry --> EditProfile
    ConfigEntry --> EditSalary
    ConfigEntry --> ResetData
  end

  MainMenu --> ConfigEntry

  %% Educação Financeira
  subgraph EDU ["Educação Financeira"]
    direction TB
    EduMenu["'🎓 Educação Financeira' -> educacao_keyboard()"]
    DicaDia["'💡 Dica do Dia' -> dica_do_dia_handler -> coach.get_quick_tip()"]
    Glossario["'📚 Glossário' -> glossario_handler (em desenvolvimento)"]
    Modulos["'🎓 Módulos Educativos' -> modulos_educativos_handler (em desenvolvimento)"]
    EduMenu --> DicaDia
    EduMenu --> Glossario
    EduMenu --> Modulos
  end

  MainMenu --> EduMenu

  %% Saúde Financeira e IA (coach)
  subgraph COACH ["Coach / IA (coach.FinanceCoach)"]
    direction TB
    HealthMenu["'📈 Saúde Financeira' -> saude_financeira_handler -> saude_financeira_keyboard()"]
    AnaliseFlow["'📈 Análise Detalhada com IA' / /analise -> analise_detalhada_handler -> coach.get_detailed_analysis(user_id)"]
    RecomFlow["'🧠 Recomendações IA' -> recomendacoes_ia_handler -> coach.get_personalized_recommendations(user_id)"]
    MetasSugeridas["analise_detalhada_inline_keyboard -> '🎯 Metas Sugeridas' -> coach.get_suggested_goals(user_id)"]
    CoachInternal["FinanceCoach.analyze_financial_health(user_id) -> usa db.get_user_data + db.get_monthly_expenses\n -> calcula totais, percentual, saldo -> retorna dict"]
    CallAPI["FinanceCoach._call_deepseek_api(prompt,max_tokens) -> aiohttp POST, retry/backoff, cache"]
    Fallbacks["FinanceCoach._get_fallback_response(prompt) -> respostas locais categorizadas"]
    HealthMenu --> AnaliseFlow
    HealthMenu --> RecomFlow
    AnaliseFlow --> CoachInternal
    RecomFlow --> CoachInternal
    CoachInternal --> CallAPI
    CallAPI -->|fail| Fallbacks
    MetasSugeridas --> CallAPI
  end

  MainMenu --> HealthMenu

  %% Callbacks gerais e utilitários
  subgraph CALLBACKS ["Callbacks & Utilitários"]
    direction TB
    AnaliseCallbacks["CallbackQueryHandler handlers.handle_analise_callback pattern '^analise_'"]
    ModulosCallback["CallbackQueryHandler handlers.handle_modulos_callback pattern '^modulo_'"]
    CalendarCallbacks["CallbackQueryHandler Calendar.handle_callback pattern '^CAL_'"]
    MonthYearCallbacks["CallbackQueryHandler MonthYearCalendar.handle_callback pattern '^(MY_|EXTRATO_)'"]
    MainMenuHandler["Mensagem final: MessageHandler filters.TEXT & ~filters.COMMAND -> main_menu_handler"]
    AnaliseCallbacks --> AnaliseFlow
    ModulosCallback --> Modulos
    CalendarCallbacks --> CalendarCallback
    MonthYearCallbacks --> MYCallback
    MainMenuHandler --> MainMenu
  end

  RunPolling --> AnaliseCallbacks

  %% Database / Persistence
  subgraph DBMODULE ["database.py (Database)"]
    direction TB
    DBClass["class Database(db_path)"]
    Conn["get_connection() → sqlite3.connect"]
    Schema["init_db() → cria tabelas users,transactions,custom_categories,goals,salaries,extra_incomes"]
    CRUDUsers["add_user/get_user_data/update_user_nickname/update_user_salary/user_exists"]
    Transactions["add_transaction/get_monthly_expenses/get_monthly_transactions/get_category_expenses"]
    CustomCats["add_custom_category/get_custom_categories/delete_custom_category"]
    GoalsDB["add_goal/get_user_goals/update_goal_progress/delete_goal/fix_goals_data"]
    SalariesDB["add_salary/get_salaries/update_salary/set_principal_salary/delete_salary"]
    ExtrasDB["add_extra_income/get_extra_incomes/update_extra_income/delete_extra_income"]
    Backup["backup_database/restore_database"]
    DBClass --> Conn
    DBClass --> Schema
    Schema --> CRUDUsers
    Schema --> Transactions
    Schema --> CustomCats
    Schema --> GoalsDB
    Schema --> SalariesDB
    Schema --> ExtrasDB
    DBClass --> Backup
  end

  %% Dependencies: Handlers -> DB and Coach
  handlers_db[Handlers usam db.* funções] --> DBClass
  handlers_coach[Handlers usam coach.finance_coach.*] --> COACH

  %% Erros, Logs e Cleanups
  subgraph ERRORS ["Erros, Logs e Fallbacks"]
    direction TB
    DBErrors["database.py -> log errors, retorna False ou valores default"]
    HandlerErrors["handlers.py -> try/except e mensagens amigáveis ao usuário; limpa context.user_data quando necessário"]
    CoachErrors["coach.py -> retry/backoff; se falha usa fallback local; log de todas as tentativas"]
    Timeouts["Config timeouts: API_TIMEOUT_TOTAL, API_TIMEOUT_CONNECT, API_MAX_RETRIES, API_RETRY_DELAY"]
    CloseSession["coach.finance_coach.close_session() on shutdown"]
    DBErrors --> HandlerErrors
    CoachErrors --> HandlerErrors
    Timeouts --> CoachErrors
    CloseSession --> CoachErrors
  end

  %% Finalização / Shutdown
  Shutdown["Ctrl+C ou exceção -> application.stop; encerra sessões; print logs e finaliza"]
  RunPolling --> Shutdown
  Shutdown --> CloseSession

  %% Notas Auxiliares visuais (não executáveis)
  classDef module fill:#f9f,stroke:#333,stroke-width:1px;
  class DBMODULE module;
  class COACH module;
  class GASTOS module;
  class EXTRATO module;
  class SALARIOS module;
  class RENDAS module;
  class GOALS module;
  class CATEGORIES module;
  class CONFIG module;
  class EDU module;
