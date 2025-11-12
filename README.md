flowchart TD
  %% STARTUP
  Start(("Start: bot.py main()"))
  CheckToken{"config.BOT_TOKEN válido?"}
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

  %% USER / DISPATCHER / START
  UMessage["Usuário envia /start ou outra mensagem"]
  Dispatcher["Dispatcher → encontra Handler"]
  StartCmd["/start → handlers.start"]
  OtherCmds["Outros comandos / botões → handlers diversos"]

  RunPolling --> UMessage
  UMessage --> Dispatcher
  Dispatcher -->|"/start"| StartCmd
  Dispatcher -->|outros| OtherCmds

  %% CADASTRO
  CheckUser{"db.user_exists(user_id)?"}
  WelcomeReturning["Mostrar main_keyboard() (usuário existente)"]
  AskName["Pedir nome → estado GET_NAME"]
  GetName["handlers.get_name → guarda nickname"]
  AskSalary["Pedir salário → estado GET_SALARY"]
  GetSalary["handlers.get_salary → valida e cria usuário"]
  ParseSalary{"salário válido?"}
  AddUser["db.add_user(user_id,nickname,salario)"]
  AddSalaryPrimary["db.add_salary(... principal=True)"]
  ShowTipoGasto["Mostrar tipo_gasto_keyboard() → estado TIPO_GASTO"]

  StartCmd --> CheckUser
  CheckUser -- "sim" --> WelcomeReturning
  CheckUser -- "não" --> AskName
  AskName --> GetName --> AskSalary --> GetSalary --> ParseSalary
  ParseSalary -- "não" --> AskSalary
  ParseSalary -- "sim" --> AddUser --> AddSalaryPrimary --> ShowTipoGasto

  %% MENU PRINCIPAL
  MainMenu["handlers.main_menu_handler → main_keyboard()"]
  WelcomeReturning --> MainMenu
  ShowTipoGasto --> MainMenu

  %% GASTOS / RENDAS (DETALHADO)
  subgraph GASTOS ["Gastos / Rendas"]
    direction TB
    EntryGastos["Entrada: '🧮 Gastos / Rendas' ou botão"]
    StartGastos["handlers.adicionar_gastos_handler → valida user → mostra gastos_keyboard()"]
    TipoGasto["Estado TIPO_GASTO → tipo_gasto_handler"]
    Fixos["Gastos Fixos → categorias_fixas_keyboard()"]
    Flexiveis["Gastos Flexíveis → categorias_flexiveis_keyboard()"]
    SalarioOpt["Salário → salario_handler"]
    RendaExtraOpt["Renda extra → renda_extra_handler"]

    EntryGastos --> StartGastos --> TipoGasto
    TipoGasto -->|Fixos| Fixos
    TipoGasto -->|Flexíveis| Flexiveis
    TipoGasto -->|Salário| SalarioOpt
    TipoGasto -->|Renda extra| RendaExtraOpt

    CategoriaFixa["categoria_fixa_handler → valida categoria → pede VALOR_GASTO"]
    CategoriaFlex["categoria_flexivel_handler → valida categoria → pede VALOR_GASTO"]
    Fixos --> CategoriaFixa
    Flexiveis --> CategoriaFlex

    OutrosFix["Outros fixos → minhas categorias / adicionar novo"]
    OutrosFlex["Outros flex → minhas categorias / adicionar novo"]
    CategoriaFixa --> OutrosFix
    CategoriaFlex --> OutrosFlex

    ValorGasto["VALOR_GASTO → valor_gasto_handler (valida)"]
    CategoriaFixa --> ValorGasto
    CategoriaFlex --> ValorGasto

    CalendarView["Calendar.create_calendar() → estado DATA_GASTO"]
    ValorGasto --> CalendarView

    CalendarCallback["CallbackQueryHandler Calendar.handle_callback (^CAL_)"]
    CalendarView --> CalendarCallback

    DaySelect["CAL_DAY → Calendar.handle_date_selection → process_date_selection"]
    ManualDate["CAL_MANUAL → pede digitar data → handle_date_input"]
    CalendarCallback -->|CAL_DAY| DaySelect
    CalendarCallback -->|CAL_MANUAL| ManualDate

    ProcessTx["process_date_selection / handle_date_input → db.add_transaction(user_id,tipo,categoria,valor,date)"]
    DaySelect --> ProcessTx
    ManualDate --> ProcessTx

    TxSuccess{"inserção ok?"}
    ProcessTx --> TxSuccess
    TxSuccess -- "sim" --> ConfirmRegistered["Envia confirmação + sim_nao_keyboard()"]
    TxSuccess -- "não" --> ErrorRegister["Informa erro e retorna ao menu"]

    ConfirmRegistered --> ContinuarGastos["CONTINUAR_GASTOS → continuar_gastos_handler"]
    ContinuarGastos -->|SIM| TipoGasto
    ContinuarGastos -->|NÃO| ShowResumo["Gera resumo → db.get_monthly_expenses → mostra saude_financeira_keyboard()"]
  end

  MainMenu --> EntryGastos

  %% EXTRATO / CALENDÁRIO
  subgraph EXTRATO ["Extrato Mensal / MonthYearCalendar"]
    direction TB
    ExtratoEntry["Usuário → '🧾 Meu Extrato'"]
    ShowMYCalendar["MonthYearCalendar.create_month_year_calendar() → InlineKeyboard"]
    MYCallback["CallbackQueryHandler MonthYearCalendar.handle_callback (MY_/EXTRATO_)"]
    MY_MANUAL["MY_MANUAL → pede entrada manual → handle_month_year_input"]
    MY_MONTH["MY_MONTH → MonthYearCalendar.show_month_extrato(year,month)"]
    ShowMonthExtrato["show_month_extrato → db.get_monthly_transactions + db.get_user_data"]
    SendExtrato["Envia/edita mensagem com extrato (agrupa e mostra totais)"]

    ExtratoEntry --> ShowMYCalendar --> MYCallback
    MYCallback -->|MY_MANUAL| MY_MANUAL
    MYCallback -->|MY_MONTH| MY_MONTH
    MY_MANUAL --> ShowMonthExtrato
    MY_MONTH --> ShowMonthExtrato --> SendExtrato
  end

  MainMenu --> ExtratoEntry

  %% SALÁRIOS E RENDAS EXTRAS
  subgraph SALARIOS ["Salários e Rendas Extras"]
    direction TB
    SalMenu["💰 Salário → salario_handler (menu)"]
    AddSalary["add_salary_handler → pede origem → pede valor → db.add_salary"]
    ConsultSalaries["consultar_salarios_handler → db.get_salaries"]
    AlterSalaries["alterar_salarios_handler → edit_salary_{id} → ações (edit/set_principal/delete)"]
    RendaMenu["💵 Renda extra → renda_extra_handler"]
    AddExtra["add_extra_income_handler → db.add_extra_income"]
    ConsultExtras["consultar_rendas_extras_handler → db.get_extra_incomes"]
    AlterExtras["alterar_rendas_extras_handler → edit_extra_{id} → ações"]

    SalMenu --> AddSalary
    SalMenu --> ConsultSalaries
    SalMenu --> AlterSalaries
    RendaMenu --> AddExtra
    RendaMenu --> ConsultExtras
    RendaMenu --> AlterExtras
  end

  MainMenu --> SalMenu
  MainMenu --> RendaMenu

  %% OBJETIVOS
  subgraph GOALS ["Objetivos Financeiros"]
    direction TB
    GoalsMenu["🎯 Objetivos → objetivos_handler"]
    AddGoalStart["add_goal_handler → escolher tipo (economia_mensal/meta_especifica)"]
    GoalTypeSel["goal_type_handler → pede descrição"]
    GoalDesc["goal_description_handler → pede valor"]
    GoalTarget["goal_target_handler → se economia_mensal: db.add_goal; se meta_especifica: mostrar Calendar"]
    GoalDeadlineCB["goal_deadline_calendar_handler → CAL_DAY → db.add_goal com prazo"]
    ViewGoals["meus_objetivos_handler → db.get_user_goals"]
    UpdateProgress["update_goal_progress_handler → db.update_goal_progress"]
    DeleteGoal["delete_goal_handler → db.delete_goal"]

    GoalsMenu --> AddGoalStart --> GoalTypeSel --> GoalDesc --> GoalTarget
    GoalTarget -->|meta_especifica| GoalDeadlineCB
    GoalsMenu --> ViewGoals
    GoalsMenu --> UpdateProgress
    GoalsMenu --> DeleteGoal
  end

  MainMenu --> GoalsMenu

  %% CATEGORIAS PERSONALIZADAS
  subgraph CATS ["Categorias Personalizadas"]
    direction TB
    SuasCats["📂 Suas Categorias → suas_categorias_handler"]
    SuasCatsMenu["Escolher Fixas / Flexíveis"]
    ListFix["categorias_fixas_keyboard_with_delete"]
    ListFlex["categorias_flexiveis_keyboard_with_delete"]
    SelectDelete["selecionar_categoria_excluir_handler → confirmar"]
    ConfirmDelete["confirmar_exclusao_categoria_handler → db.delete_custom_category"]

    SuasCats --> SuasCatsMenu --> ListFix
    SuasCatsMenu --> ListFlex
    ListFix --> SelectDelete --> ConfirmDelete
    ListFlex --> SelectDelete
  end

  MainMenu --> SuasCats

  %% EDUCAÇÃO FINANCEIRA
  subgraph EDU ["Educação Financeira"]
    direction TB
    EduMenu["🎓 Educação Financeira → educacao_keyboard()"]
    DicaDia["💡 Dica do Dia → coach.get_quick_tip()"]
    Glossario["📚 Glossário (em desenvolvimento)"]
    Modulos["🎓 Módulos Educativos (em desenvolvimento)"]

    EduMenu --> DicaDia
    EduMenu --> Glossario
    EduMenu --> Modulos
  end

  MainMenu --> EduMenu

  %% COACH / IA
  subgraph COACH ["Coach / IA (FinanceCoach)"]
    direction TB
    HealthMenu["📈 Saúde Financeira → saude_financeira_handler"]
    AnaliseFlow["analise_detalhada_handler → coach.get_detailed_analysis(user_id)"]
    RecomFlow["recomendacoes_ia_handler → coach.get_personalized_recommendations(user_id)"]
    MetasSugeridas["Metas Sugeridas → coach.get_suggested_goals(user_id)"]
    CoachInternal["FinanceCoach: analyze_financial_health; _call_deepseek_api; cache; fallback"]

    HealthMenu --> AnaliseFlow
    HealthMenu --> RecomFlow
    AnaliseFlow --> CoachInternal
    RecomFlow --> CoachInternal
    CoachInternal --> MetasSugeridas
  end

  MainMenu --> HealthMenu

  %% CALLBACKS / UTILITÁRIOS
  Callbacks["CallbackQueryHandlers: ^analise_, ^modulo_, ^CAL_, ^MY_/EXTRATO_"]
  MainMenuHandler["Mensagem padrão → main_menu_handler (MessageHandler filters.TEXT & ~filters.COMMAND)"]

  RunPolling --> Callbacks
  RunPolling --> MainMenuHandler

  %% DATABASE
  DB["SQLite: financas.db (users, transactions, custom_categories, goals, salaries, extra_incomes)"]
  ProcessToDB["Handlers chamam db.* (add_transaction, get_monthly_transactions, add_salary, add_goal, etc.)"]

  ProcessToDB --> DB
  ProcessToDB --- ProcessTx
  ProcessToDB --- ShowMonthExtrato
  ProcessToDB --- ViewGoals
  CoachInternal --- ProcessToDB

  %% ERROS / LOGS / SHUTDOWN
  Errors["Erros: logs, fallback; Timeouts config; retry/backoff"]
  Shutdown["Shutdown: Ctrl+C → application.stop; coach.close_session()"]

  CreateApp --> Errors
  DB --> Errors
  RunPolling --> Shutdown

  classDef module fill:#f3f4f6,stroke:#9CA3AF;
  class GASTOS,EXTRATO,SALARIOS,GOALS,CATS,EDU,COACH module;
