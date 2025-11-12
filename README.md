```mermaid
graph TD

  %% Entrada
  Start((Start)) --> StartCommand["Usuário envia /start"]
  StartCommand -- "Novo usuário: db.user_exists() == False" --> CadastroEntry["Entrada Cadastro"]
  StartCommand -- "Usuário existente: db.user_exists() == True" --> MainMenu

  %% 1. Fluxo de Cadastro
  subgraph Cadastro
  direction TD
    CadastroTitle["1 — Fluxo de Cadastro (cadastro_conv_handler)"]
    CadastroEntry --> Cad_GET_NAME["Estado: GET_NAME"]
    Cad_GET_NAME --> Cad_GET_SALARY["Estado: GET_SALARY"]
    Cad_GET_SALARY --> Cad_TIPO_GASTO["Estado: TIPO_GASTO"]
    Cad_TIPO_GASTO --> Gastos_TIPO_GASTO["Redireciona para Fluxo de Gastos"]
  end

  %% 2. Hub central (menu)
  MainMenu["MENU PRINCIPAL / HUB\n(h.main_menu_handler)"]
  MainMenu -- "/menu" --> MainMenu
  MainMenu -- "/cancel" --> MainMenu
  MainMenu -- "Voltar ao Menu" --> MainMenu

  %% 3. Fluxo de Gastos
  MainMenu -- "🧮 Gastos / Rendas" --> GastosEntry["Entrada Gastos"]

  subgraph FluxoDeGastos
  direction TD
    FluxoGastosTitle["2 — Fluxo de Gastos (gastos_conv_handler)"]
    GastosEntry --> Gastos_TIPO_GASTO["Estado: TIPO_GASTO"]

    Gastos_TIPO_GASTO -- "Gastos Fixos" --> Gastos_CAT_FIXA["Estado: CATEGORIA_FIXA"]
    Gastos_TIPO_GASTO -- "Gastos Flexíveis" --> Gastos_CAT_FLEX["Estado: CATEGORIA_FLEXIVEL"]

    Gastos_CAT_FIXA -- "Categoria (ex: Moradia)" --> Gastos_VALOR_GASTO["Estado: VALOR_GASTO"]
    Gastos_CAT_FIXA -- "Outros..." --> Gastos_OUTROS_FIXOS["Estado: OUTROS_FIXOS"]

    Gastos_CAT_FLEX -- "Categoria (ex: Alimentação)" --> Gastos_VALOR_GASTO
    Gastos_CAT_FLEX -- "Outros..." --> Gastos_OUTROS_FLEX["Estado: OUTROS_FLEXIVEIS"]

    Gastos_OUTROS_FIXOS -- "Adicionar novo" --> Gastos_NOVA_CAT_FIXA["Estado: NOVA_CATEGORIA_OUTROS_FIXOS"]
    Gastos_OUTROS_FIXOS -- "Minhas categorias" --> Gastos_MINHAS_CAT_FIXAS["Estado: MINHAS_CATEGORIAS_FIXAS"]
    Gastos_NOVA_CAT_FIXA --> Gastos_VALOR_GASTO
    Gastos_MINHAS_CAT_FIXAS --> Gastos_VALOR_GASTO

    Gastos_OUTROS_FLEX -- "Adicionar novo" --> Gastos_NOVA_CAT_FLEX["Estado: NOVA_CATEGORIA_OUTROS"]
    Gastos_OUTROS_FLEX -- "Minhas categorias" --> Gastos_MINHAS_CAT_FLEX["Estado: MINHAS_CATEGORIAS"]
    Gastos_NOVA_CAT_FLEX --> Gastos_VALOR_GASTO
    Gastos_MINHAS_CAT_FLEX --> Gastos_VALOR_GASTO

    Gastos_TIPO_GASTO -- "Salário" --> Salarios_Menu["Menu Salários"]
    Gastos_TIPO_GASTO -- "Renda extra" --> Renda_Menu["Menu Renda Extra"]

    Gastos_VALOR_GASTO -- "Valor" --> Gastos_DATA_GASTO["Estado: DATA_GASTO"]
    note right of Gastos_DATA_GASTO
gastos_calendario_handler (callback)
Entrada manual (handle_date_input)
    end note

    Gastos_DATA_GASTO -- "Data" --> Gastos_CONTINUAR["Estado: CONTINUAR_GASTOS"]
    Gastos_CONTINUAR -- "SIM" --> Gastos_TIPO_GASTO
    Gastos_CONTINUAR -- "NÃO" --> Gastos_RESUMO["Estado: RESUMO_GASTOS"]
    Gastos_RESUMO --> MainMenu
  end

  %% 4. Fluxo de Objetivos
  MainMenu -- "🎯 Objetivos" --> ObjetivosEntry["Entrada Objetivos"]

  subgraph FluxoDeObjetivos
  direction TD
    ObjetivosTitle["3 — Fluxo de Objetivos (goals_conv / update_goal_conv / delete_goal_conv)"]
    ObjetivosEntry --> Objetivos_Menu["Menu Objetivos"]

    Objetivos_Menu -- "Adicionar Objetivo" --> Goals_TYPE["Estado: GOAL_TYPE"]
    Goals_TYPE --> Goals_DESC["Estado: GOAL_DESCRIPTION"]
    Goals_DESC --> Goals_TARGET["Estado: GOAL_TARGET"]
    Goals_TARGET --> Goals_DEADLINE["Estado: GOAL_DEADLINE"]
    note right of Goals_DEADLINE
goals_calendario_handler (callback)
Entrada manual (goal_deadline_manual_handler)
    end note
    Goals_DEADLINE -- "Salvar" --> MainMenu

    Objetivos_Menu -- "Atualizar Progresso" --> UpdateGoal_SELECT["Estado: SELECT_GOAL"]
    UpdateGoal_SELECT --> UpdateGoal_VALUE["Estado: UPDATE_GOAL_PROGRESS"]
    UpdateGoal_VALUE -- "Salvar" --> MainMenu

    Objetivos_Menu -- "Excluir Objetivo" --> DeleteGoal_SELECT["Estado: SELECT_GOAL_DELETE"]
    DeleteGoal_SELECT --> DeleteGoal_CONFIRM["Estado: CONFIRM_DELETE_GOAL"]
    DeleteGoal_CONFIRM -- "SIM" --> MainMenu
    DeleteGoal_CONFIRM -- "NÃO" --> MainMenu

    Objetivos_Menu -- "Meus Objetivos" --> Action_MeusObjetivos["Lista de objetivos (retorna)"]
    Action_MeusObjetivos --> MainMenu
  end

  %% 5. Fluxo de Salários
  subgraph FluxoDeSalarios
  direction TD
    Salarios_Menu["Menu Salários"]
    Salarios_Menu -- "Adicionar Salário" --> AddSalary_ORIGIN["Estado: ADD_SALARY_ORIGIN"]
    AddSalary_ORIGIN --> AddSalary_VALUE["Estado: ADD_SALARY_VALUE"]
    AddSalary_VALUE -- "Salvar" --> MainMenu

    Salarios_Menu -- "Alterar Salários" --> EditSalary_SELECT["Estado: EDIT_SALARY_SELECT"]
    EditSalary_SELECT --> EditSalary_ACTION["Estado: EDIT_SALARY_ACTION"]
    EditSalary_ACTION -- "Renomear Origem" --> EditSalary_ORIGIN["Estado: EDIT_SALARY_ORIGIN"]
    EditSalary_ACTION -- "Alterar Valor" --> EditSalary_VALUE["Estado: EDIT_SALARY_VALUE"]
    EditSalary_ACTION -- "Tornar Principal" --> MainMenu
    EditSalary_ACTION -- "Excluir Salário" --> MainMenu
    EditSalary_ORIGIN -- "Salvar" --> MainMenu
    EditSalary_VALUE -- "Salvar" --> MainMenu

    Salarios_Menu -- "Consultar Salários" --> Action_ConsultarSalarios["Consultar salários"]
    Action_ConsultarSalarios --> MainMenu
  end

  %% 6. Fluxo de Renda Extra
  subgraph FluxoRendaExtra
  direction TD
    Renda_Menu["Menu Renda Extra"]
    Renda_Menu -- "Adicionar Renda Extra" --> AddExtra_ORIGIN["Estado: ADD_EXTRA_INCOME_ORIGIN"]
    AddExtra_ORIGIN --> AddExtra_VALUE["Estado: ADD_EXTRA_INCOME_VALUE"]
    AddExtra_VALUE -- "Salvar" --> MainMenu

    Renda_Menu -- "Alterar Rendas Extras" --> EditExtra_SELECT["Estado: EDIT_EXTRA_INCOME_SELECT"]
    EditExtra_SELECT --> EditExtra_ACTION["Estado: EDIT_EXTRA_INCOME_ACTION"]
    EditExtra_ACTION -- "Renomear Origem" --> EditExtra_ORIGIN["Estado: EDIT_EXTRA_INCOME_ORIGIN"]
    EditExtra_ACTION -- "Alterar Valor" --> EditExtra_VALUE["Estado: EDIT_EXTRA_INCOME_VALUE"]
    EditExtra_ACTION -- "Excluir Renda Extra" --> MainMenu
    EditExtra_ORIGIN -- "Salvar" --> MainMenu
    EditExtra_VALUE -- "Salvar" --> MainMenu

    Renda_Menu -- "Consultar Rendas Extras" --> Action_ConsultarRendas["Consultar rendas extras"]
    Action_ConsultarRendas --> MainMenu
  end

  %% 7. Fluxo de Extrato
  MainMenu -- "Meu Extrato" --> ExtratoEntry["Entrada Extrato"]

  subgraph FluxoExtrato
  direction TD
    ExtratoEntry --> Extrato_EntryPoint["Estado: EXTRATO_MES"]
    note right of Extrato_EntryPoint
extrato_calendario_handler (callback)
Entrada manual (handle_month_year_input)
    end note
    Extrato_EntryPoint -- "Mês/Ano" --> Action_ShowExtrato["Mostrar extrato do mês"]
    Action_ShowExtrato --> MainMenu
  end

  %% 8. Fluxo de Categorias
  MainMenu -- "Suas Categorias" --> Cat_SUAS_CAT["Estado: SUAS_CATEGORIAS"]

  subgraph FluxoCategorias
  direction TD
    Cat_SUAS_CAT --> Cat_FIXAS["Fixas"]
    Cat_SUAS_CAT --> Cat_FLEXIVEIS["Flexíveis"]
    Cat_FIXAS -- "Excluir Categoria" --> Cat_SELECT_EXCLUIR["Estado: SELECIONAR_CATEGORIA_EXCLUIR"]
    Cat_FLEXIVEIS -- "Excluir Categoria" --> Cat_SELECT_EXCLUIR
    Cat_SELECT_EXCLUIR --> Cat_CONFIRM_EXCLUIR["Estado: CONFIRMAR_EXCLUSAO_CATEGORIA"]
    Cat_CONFIRM_EXCLUIR -- "SIM" --> MainMenu
    Cat_CONFIRM_EXCLUIR -- "NÃO" --> MainMenu
  end

  %% 9. Fluxo de Configurações
  MainMenu -- "Configurações" --> Config_Menu["Menu Configurações"]

  subgraph FluxoConfiguracoes
  direction TD
    Config_Menu -- "Editar Perfil" --> Config_EDIT_NAME["Estado: EDIT_NAME"]
    Config_EDIT_NAME -- "Salvar" --> MainMenu
    Config_Menu -- "Alterar Salário (Legado)" --> Config_EDIT_SALARY["Estado: EDIT_SALARY"]
    Config_EDIT_SALARY -- "Salvar" --> MainMenu
    Config_Menu -- "Redefinir" --> Config_CONFIRM_RESET["Estado: CONFIRM_RESET"]
    Config_CONFIRM_RESET -- "SIM" --> MainMenu
    Config_CONFIRM_RESET -- "NÃO" --> MainMenu
  end

  %% 10. Ações Diretas
  subgraph AcoesDiretas
  direction TD
    MainMenu -- "Saúde Financeira" --> Saude_Menu["Menu Saúde Financeira"]
    Saude_Menu -- "Ver Métricas Detalhadas" --> Action_VerMetricas["Ver métricas"]
    Saude_Menu -- "Recomendações IA" --> Action_Recomendacoes["Recomendações IA"]
    Saude_Menu -- "Análise Detalhada com IA" --> Action_AnaliseIA["Análise IA"]
    Action_VerMetricas --> MainMenu
    Action_Recomendacoes --> MainMenu
    Action_AnaliseIA --> MainMenu

    MainMenu -- "Educação Financeira" --> Edu_Menu["Menu Educação Financeira"]
    Edu_Menu -- "Dica do Dia" --> Action_DicaDia["Dica do dia"]
    Edu_Menu -- "Glossário" --> Action_Glossario["Glossário"]
    Edu_Menu -- "Módulos Educativos" --> Action_Modulos["Módulos educativos"]
    Action_DicaDia --> MainMenu
    Action_Glossario --> MainMenu
    Action_Modulos --> MainMenu

    MainMenu -- "/ajuda" --> Action_Ajuda["Ajuda"]
    MainMenu -- "/analisar" --> Action_AnaliseIA
    MainMenu -- "/resumo" --> Action_Resumo["Resumo gastos"]
    Action_Ajuda --> MainMenu
    Action_Resumo --> MainMenu
  end
