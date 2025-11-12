```mermaid
flowchart TD
  %% Entrada
  Start((Usuário inicia /start))

  %% Autenticação / Cadastro
  Start --> CheckUser{Usuário existe?}
  CheckUser -- Não --> Cadastro[Cadastro\n(GET_NAME → GET_SALARY)]
  Cadastro --> CreateProfile[/db.add_user + db.add_salary/]
  CreateProfile --> MainMenu
  CheckUser -- Sim --> MainMenu

  %% Menu Principal (Hub)
  subgraph HUB [Menu Principal]
    MainMenu([Menu Principal\n(main_keyboard)])
  end

  %% Fluxo Gastos e Rendas
  MainMenu -->|Gastos / Rendas| GastosMenu[Menu Gastos\n(tipo_gasto_keyboard)]
  GastosMenu -->|Gastos Fixos| GastosFixos[CATEGORIA_FIXA]
  GastosMenu -->|Gastos Flexíveis| GastosFlex[CATEGORIA_FLEXIVEL]
  GastosMenu -->|Salário| SalarioMenu[Gerenciar Salários]
  GastosMenu -->|Renda extra| RendaMenu[Gerenciar Rendas Extras]

  %% Registro de gasto (com calendário)
  GastosFixos --> SelectFixCat[Seleciona categoria]
  GastosFlex --> SelectFlexCat[Seleciona categoria]
  SelectFixCat --> InputValorGasto[VALOR_GASTO]
  SelectFlexCat --> InputValorGasto[VALOR_GASTO]
  InputValorGasto --> EscolherData[Calendário (Calendar)\nou entrada manual]
  EscolherData --> PersistGasto[/db.add_transaction/]
  PersistGasto --> Continuar{Continuar?}
  Continuar -- Sim --> GastosMenu
  Continuar -- Não --> Resumo[Mostrar resumo mensal\n(resumo_gastos_handler)]

  %% Calendários separados
  EscolherData -->|Calendário de gasto| CalendarHandler[Calendar.handle_callback (CAL_...)]
  MainMenu -->|Meu Extrato| ExtratoMenu[Extrato mensal]
  ExtratoMenu --> MonthYearCalendar[MonthYearCalendar\n(seleção MM/AAAA ou callbacks MY_...)]
  MonthYearCalendar --> ShowExtrato[/db.get_monthly_transactions + render/]

  %% Salários
  SalarioMenu --> AddSalary[ADD_SALARY_ORIGIN → ADD_SALARY_VALUE]
  AddSalary --> [/db.add_salary/]
  SalarioMenu --> EditSalaries[Lista salários → editar (Callback edit_salary_...)]
  EditSalaries --> UpdateSalary[/db.update_salary | db.set_principal_salary | db.delete_salary/]

  %% Rendas Extras
  RendaMenu --> AddExtra[ADD_EXTRA_INCOME_ORIGIN → ADD_EXTRA_INCOME_VALUE]
  AddExtra --> [/db.add_extra_income/]
  RendaMenu --> EditExtra[editar (Callback edit_extra_income_...)]
  EditExtra --> UpdateExtra[/db.update_extra_income | db.delete_extra_income/]

  %% Categorias do usuário
  MainMenu -->|Suas Categorias| MyCats[Suas Categorias]
  MyCats --> FixCatsView[categorias fixas personalizadas]
  MyCats --> FlexCatsView[categorias flexíveis personalizadas]
  FixCatsView -->|Excluir| ConfirmDeleteCat[CONFIRMAR_EXCLUSAO_CATEGORIA]
  ConfirmDeleteCat --> [/db.delete_custom_category/]

  %% Objetivos (goals)
  MainMenu -->|Objetivos| GoalsMenu[Menu Objetivos]
  GoalsMenu --> AddGoal[Adicionar objetivo\n(GOAL_TYPE → GOAL_DESCRIPTION → GOAL_TARGET → GOAL_DEADLINE)]
  AddGoal --> [/db.add_goal/]
  GoalsMenu --> UpdateGoal[Atualizar progresso (SELECT_GOAL → UPDATE_GOAL_PROGRESS)]
  UpdateGoal --> [/db.update_goal_progress/]
  GoalsMenu --> DeleteGoal[Excluir objetivo (Callback delete_goal_...)]
  DeleteGoal --> [/db.delete_goal/]
  GoalsMenu --> ListGoals[Meus objetivos → /db.get_user_goals]

  %% Saúde Financeira e IA
  MainMenu -->|Saúde Financeira| HealthMenu[Menu Saúde Financeira]
  HealthMenu --> Metrics[Ver Métricas → calcula totals via db.get_monthly_expenses]
  HealthMenu --> IA_Analysis[Análise detalhada IA]
  IA_Analysis -->|chama| Coach[coach.finance_coach.get_detailed_analysis\nou get_personalized_recommendations]
  Coach --> HealthMenu

  %% Configurações e utilidades
  MainMenu -->|Configurações| ConfigMenu[Editar perfil | Redefinir dados]
  ConfigMenu --> EditName[/db.update_user_nickname/]
  ConfigMenu --> EditSalary[/db.update_user_salary/]
  ConfigMenu --> ResetData[/db.reset_user_data/]

  %% Fim / retorno ao menu
  PersistGasto --> MainMenu
  ShowExtrato --> MainMenu
  UpdateSalary --> MainMenu
  UpdateExtra --> MainMenu
  EditName --> MainMenu

    MainMenu -- "/ajuda" --> Action_Ajuda["Ajuda"]
    MainMenu -- "/analisar" --> Action_AnaliseIA
    MainMenu -- "/resumo" --> Action_Resumo["Resumo gastos"]
    Action_Ajuda --> MainMenu
    Action_Resumo --> MainMenu
  end
