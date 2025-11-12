```mermaid
graph TD
    %% -----------------------------------------------------------------
    %% 1. PONTO DE ENTRADA E CADASTRO
    %% -----------------------------------------------------------------
    
    [*] --> StartCommand["Usuário envia /start"]
    
    StartCommand -- Novo Usuário (db.user_exists() == False) --> subgraph Cadastro [1. Fluxo de Cadastro (cadastro_conv_handler)]
        direction TD
        Cad_GET_NAME["Estado: GET_NAME"]
        Cad_GET_SALARY["Estado: GET_SALARY"]
        Cad_TIPO_GASTO["Estado: TIPO_GASTO"]
        
        Cad_GET_NAME -- Nome --> Cad_GET_SALARY
        Cad_GET_SALARY -- Salário --> Cad_TIPO_GASTO
        Cad_TIPO_GASTO -- (Redireciona para Fluxo de Gastos) --> Gastos_TIPO_GASTO
    end

    StartCommand -- Usuário Existente (db.user_exists() == True) --> MainMenu
    
    %% -----------------------------------------------------------------
    %% 2. HUB CENTRAL (MENU PRINCIPAL)
    %% -----------------------------------------------------------------
    
    MainMenu["🏠 MENU PRINCIPAL / HUB\n(h.main_menu_handler)"]
    MainMenu -- /menu --> MainMenu
    MainMenu -- /cancel --> MainMenu
    MainMenu -- "🏠 Voltar ao Menu" --> MainMenu
    
    %% -----------------------------------------------------------------
    %% 3. FLUXO DE GASTOS (O MAIS COMPLEXO)
    %% -----------------------------------------------------------------
    
    MainMenu -- "🧮 Gastos / Rendas" --> Gastos_TIPO_GASTO
    
    subgraph Fluxo de Gastos [2. Fluxo de Gastos (gastos_conv_handler)]
        direction TD
        Gastos_TIPO_GASTO["Estado: TIPO_GASTO"]
        
        %% Caminhos de Gastos
        Gastos_TIPO_GASTO -- "🏠 Gastos Fixos" --> Gastos_CAT_FIXA["Estado: CATEGORIA_FIXA"]
        Gastos_TIPO_GASTO -- "🛍️ Gastos Flexíveis" --> Gastos_CAT_FLEX["Estado: CATEGORIA_FLEXIVEL"]
        
        Gastos_CAT_FIXA -- "Categoria (Ex: Moradia)" --> Gastos_VALOR_GASTO["Estado: VALOR_GASTO"]
        Gastos_CAT_FIXA -- "Outros..." --> Gastos_OUTROS_FIXOS["Estado: OUTROS_FIXOS"]
        
        Gastos_CAT_FLEX -- "Categoria (Ex: Alimentação)" --> Gastos_VALOR_GASTO
        Gastos_CAT_FLEX -- "Outros..." --> Gastos_OUTROS_FLEX["Estado: OUTROS_FLEXIVEIS"]

        %% Sub-fluxo "Outros Fixos"
        Gastos_OUTROS_FIXOS -- "➕ Adicionar novo" --> Gastos_NOVA_CAT_FIXA["Estado: NOVA_CATEGORIA_OUTROS_FIXOS"]
        Gastos_OUTROS_FIXOS -- "📂 Minhas categorias" --> Gastos_MINHAS_CAT_FIXAS["Estado: MINHAS_CATEGORIAS_FIXAS"]
        Gastos_NOVA_CAT_FIXA -- Nome --> Gastos_VALOR_GASTO
        Gastos_MINHAS_CAT_FIXAS -- Categoria --> Gastos_VALOR_GASTO
        
        %% Sub-fluxo "Outros Flexíveis"
        Gastos_OUTROS_FLEX -- "➕ Adicionar novo" --> Gastos_NOVA_CAT_FLEX["Estado: NOVA_CATEGORIA_OUTROS"]
        Gastos_OUTROS_FLEX -- "📂 Minhas categorias" --> Gastos_MINHAS_CAT_FLEX["Estado: MINHAS_CATEGORIAS"]
        Gastos_NOVA_CAT_FLEX -- Nome --> Gastos_VALOR_GASTO
        Gastos_MINHAS_CAT_FLEX -- Categoria --> Gastos_VALOR_GASTO

        %% Caminhos de Rendas (links para outros fluxos)
        Gastos_TIPO_GASTO -- "💰 Salário" --> Salarios_Menu
        Gastos_TIPO_GASTO -- "💵 Renda extra" --> Renda_Menu
        
        %% Continuação do fluxo de gastos
        Gastos_VALOR_GASTO -- Valor --> Gastos_DATA_GASTO["Estado: DATA_GASTO"]
        note right of Gastos_DATA_GASTO
            - <b>gastos_calendario_handler</b> (Callback ^CAL_)
            - Entrada manual (h.handle_date_input)
        end note
        
        Gastos_DATA_GASTO -- Data --> Gastos_CONTINUAR["Estado: CONTINUAR_GASTOS\n(db.add_transaction)"]
        Gastos_CONTINUAR -- "✅ SIM" --> Gastos_TIPO_GASTO
        Gastos_CONTINUAR -- "❌ NÃO" --> Gastos_RESUMO["Estado: RESUMO_GASTOS"]
        Gastos_RESUMO --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 4. FLUXO DE OBJETIVOS
    %% -----------------------------------------------------------------
    
    MainMenu -- "🎯 Objetivos" --> Objetivos_Menu["🎯 Menu Objetivos\n(h.objetivos_handler)"]
    
    subgraph Fluxo de Objetivos [3. Fluxo de Objetivos (goals_conv, update_goal_conv, delete_goal_conv)]
        direction TD
        
        %% Caminho 1: Adicionar Objetivo
        Objetivos_Menu -- "🎯 Adicionar Objetivo" --> Goals_TYPE["Estado: GOAL_TYPE"]
        Goals_TYPE -- Tipo --> Goals_DESC["Estado: GOAL_DESCRIPTION"]
        Goals_DESC -- Descrição --> Goals_TARGET["Estado: GOAL_TARGET"]
        Goals_TARGET -- Valor --> Goals_DEADLINE["Estado: GOAL_DEADLINE / GOAL_DEADLINE_CALENDAR"]
        note right of Goals_DEADLINE
            - <b>goals_calendario_handler</b> (Callback ^CAL_)
            - Entrada manual (h.goal_deadline_manual_handler)
        end note
        Goals_DEADLINE -- Data (db.add_goal) --> MainMenu
        
        %% Caminho 2: Atualizar Progresso
        Objetivos_Menu -- "📊 Atualizar Progresso" --> UpdateGoal_SELECT["Estado: SELECT_GOAL"]
        note right of UpdateGoal_SELECT
            - <b>update_goal_select_handler</b> (Callback ^goal_)
        end note
        UpdateGoal_SELECT -- Seleciona Objetivo --> UpdateGoal_VALUE["Estado: UPDATE_GOAL_PROGRESS"]
        UpdateGoal_VALUE -- Novo Valor (db.update_goal_progress) --> MainMenu
        
        %% Caminho 3: Excluir Objetivo
        Objetivos_Menu -- "🗑️ Excluir Objetivo" --> DeleteGoal_SELECT["Estado: SELECT_GOAL_DELETE"]
        note right of DeleteGoal_SELECT
            - <b>delete_goal_select_handler</b> (Callback ^delete_goal_)
        end note
        DeleteGoal_SELECT -- Seleciona Objetivo --> DeleteGoal_CONFIRM["Estado: CONFIRM_DELETE_GOAL"]
        DeleteGoal_CONFIRM -- "✅ SIM, Excluir" (db.delete_goal) --> MainMenu
        DeleteGoal_CONFIRM -- "❌ NÃO, Cancelar" --> MainMenu
        
        %% Caminho 4: Ação Direta
        Objetivos_Menu -- "📋 Meus Objetivos" --> Action_MeusObjetivos["h.meus_objetivos_handler\nMostra lista e retorna"]
        Action_MeusObjetivos --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 5. FLUXO DE SALÁRIOS
    %% -----------------------------------------------------------------
    
    Salarios_Menu["💰 Menu Salários\n(h.salario_handler)"]
    
    subgraph Fluxo de Salários [4. Fluxo de Salários (add_salary_conv, edit_salaries_...)]
        direction TD
        
        %% Caminho 1: Adicionar Salário
        Salarios_Menu -- "💵 Adicionar Salário" --> AddSalary_ORIGIN["Estado: ADD_SALARY_ORIGIN"]
        AddSalary_ORIGIN -- Origem --> AddSalary_VALUE["Estado: ADD_SALARY_VALUE"]
        AddSalary_VALUE -- Valor (db.add_salary) --> MainMenu
        
        %% Caminho 2: Alterar Salários
        Salarios_Menu -- "✏️ Alterar Salários" --> EditSalary_SELECT["Estado: EDIT_SALARY_SELECT"]
        note right of EditSalary_SELECT
             - <b>edit_salaries_callback_handler</b> (Callback ^edit_salary_)
        end note
        EditSalary_SELECT -- Seleciona Salário --> EditSalary_ACTION["Estado: EDIT_SALARY_ACTION"]
        
        EditSalary_ACTION -- "✏️ Renomear Origem" --> EditSalary_ORIGIN["Estado: EDIT_SALARY_ORIGIN"]
        EditSalary_ACTION -- "💰 Alterar Valor" --> EditSalary_VALUE["Estado: EDIT_SALARY_VALUE"]
        EditSalary_ACTION -- "🎯 Tornar Principal" (db.set_principal_salary) --> MainMenu
        EditSalary_ACTION -- "🗑️ Excluir Salário" (db.delete_salary) --> MainMenu
        
        EditSalary_ORIGIN -- Novo Nome (db.update_salary) --> MainMenu
        EditSalary_VALUE -- Novo Valor (db.update_salary) --> MainMenu

        %% Caminho 3: Ação Direta
        Salarios_Menu -- "📊 Consultar Salários" --> Action_ConsultarSalarios["h.consultar_salarios_handler"]
        Action_ConsultarSalarios --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 6. FLUXO DE RENDA EXTRA
    %% -----------------------------------------------------------------
    
    Renda_Menu["💵 Menu Renda Extra\n(h.renda_extra_handler)"]
    
    subgraph Fluxo de Renda Extra [5. Fluxo de Renda Extra (add_extra_income_conv, edit_extra_incomes_handler)]
        direction TD
        
        %% Caminho 1: Adicionar Renda Extra
        Renda_Menu -- "💵 Adicionar Renda Extra" --> AddExtra_ORIGIN["Estado: ADD_EXTRA_INCOME_ORIGIN"]
        AddExtra_ORIGIN -- Origem --> AddExtra_VALUE["Estado: ADD_EXTRA_INCOME_VALUE"]
        AddExtra_VALUE -- Valor (db.add_extra_income) --> MainMenu
        
        %% Caminho 2: Alterar Rendas Extras
        Renda_Menu -- "✏️ Alterar Rendas Extras" --> EditExtra_SELECT["Estado: EDIT_EXTRA_INCOME_SELECT"]
        note right of EditExtra_SELECT
             - <b>edit_extra_incomes_handler</b> (Callback ^edit_extra_income_)
        end note
        EditExtra_SELECT -- Seleciona Renda --> EditExtra_ACTION["Estado: EDIT_EXTRA_INCOME_ACTION"]
        
        EditExtra_ACTION -- "✏️ Renomear Origem" --> EditExtra_ORIGIN["Estado: EDIT_EXTRA_INCOME_ORIGIN"]
        EditExtra_ACTION -- "💰 Alterar Valor" --> EditExtra_VALUE["Estado: EDIT_EXTRA_INCOME_VALUE"]
        EditExtra_ACTION -- "🗑️ Excluir Renda Extra" (db.delete_extra_income) --> MainMenu
        
        EditExtra_ORIGIN -- Novo Nome (db.update_extra_income) --> MainMenu
        EditExtra_VALUE -- Novo Valor (db.update_extra_income) --> MainMenu
        
        %% Caminho 3: Ação Direta
        Renda_Menu -- "📊 Consultar Rendas Extras" --> Action_ConsultarRendas["h.consultar_rendas_extras_handler"]
        Action_ConsultarRendas --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 7. FLUXO DE EXTRATO
    %% -----------------------------------------------------------------
    
    MainMenu -- "🧾 Meu Extrato" --> Extrato_EntryPoint
    
    subgraph Fluxo de Extrato [6. Fluxo de Extrato (extrato_main_handler)]
        direction TD
        Extrato_EntryPoint["Estado: EXTRATO_MES\n(h.extrato_gastos_handler)"]
        note right of Extrato_EntryPoint
            - <b>extrato_calendario_handler</b> (Callback ^EXTRATO_ | ^MY_)
            - Entrada manual (h.handle_month_year_input)
        end note
        Extrato_EntryPoint -- Mês/Ano --> Action_ShowExtrato["h.MonthYearCalendar.show_month_extrato"]
        Action_ShowExtrato --> MainMenu
    end
    
    %% -----------------------------------------------------------------
    %% 8. FLUXO DE CATEGORIAS
    %% -----------------------------------------------------------------
    
    MainMenu -- "📂 Suas Categorias" --> Cat_SUAS_CAT
    
    subgraph Fluxo de Categorias [7. Fluxo "Suas Categorias" (suas_categorias_conv_handler)]
        direction TD
        Cat_SUAS_CAT["Estado: SUAS_CATEGORIAS"]
        Cat_SUAS_CAT -- "🏦 Fixas" --> Cat_FIXAS["Estado: CATEGORIAS_FIXAS"]
        Cat_SUAS_CAT -- "🛍️ Flexíveis" --> Cat_FLEXIVEIS["Estado: CATEGORIAS_FLEXIVEIS"]
        
        Cat_FIXAS -- "🗑️ Excluir Categoria" --> Cat_SELECT_EXCLUIR["Estado: SELECIONAR_CATEGORIA_EXCLUIR"]
        Cat_FLEXIVEIS -- "🗑️ Excluir Categoria" --> Cat_SELECT_EXCLUIR
        
        Cat_SELECT_EXCLUIR -- Seleciona Categoria --> Cat_CONFIRM_EXCLUIR["Estado: CONFIRMAR_EXCLUSAO_CATEGORIA"]
        Cat_CONFIRM_EXCLUIR -- "✅ SIM, Excluir" (db.delete_custom_category) --> MainMenu
        Cat_CONFIRM_EXCLUIR -- "❌ NÃO, Cancelar" --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 9. FLUXO DE CONFIGURAÇÕES
    %% -----------------------------------------------------------------
    
    MainMenu -- "⚙️ Configurações" --> Config_Menu["⚙️ Menu Configurações\n(h.main_menu_handler)"]

    subgraph Fluxo de Configurações [8. Fluxo de Configurações (config_conv_handler)]
        direction TD
        Config_Menu -- "✏️ Editar Perfil" --> Config_EDIT_NAME["Estado: EDIT_NAME"]
        Config_EDIT_NAME -- Novo Nome (db.update_user_nickname) --> MainMenu
        
        Config_Menu -- "💰 Alterar Salário (Legado)" --> Config_EDIT_SALARY["Estado: EDIT_SALARY"]
        Config_EDIT_SALARY -- Novo Salário (db.update_user_salary) --> MainMenu
        
        Config_Menu -- "🔄 Redefinir" --> Config_CONFIRM_RESET["Estado: CONFIRM_RESET"]
        Config_CONFIRM_RESET -- "✅ SIM" (db.reset_user_data) --> MainMenu
        Config_CONFIRM_RESET -- "❌ NÃO" --> MainMenu
    end

    %% -----------------------------------------------------------------
    %% 10. AÇÕES DIRETAS (Handlers Simples)
    %% -----------------------------------------------------------------
    
    subgraph Ações Diretas (Handlers Simples) [9. Ações Diretas (sem ConversationHandler)]
        direction TD
        
        %% Saúde Financeira
        MainMenu -- "📈 Saúde Financeira" --> Saude_Menu["📈 Menu Saúde Financeira"]
        Saude_Menu -- "📊 Ver Métricas Detalhadas" --> Action_VerMetricas["h.ver_metricas_handler"]
        Saude_Menu -- "🧠 Recomendações IA" --> Action_Recomendacoes["h.recomendacoes_ia_handler"]
        Saude_Menu -- "📈 Análise Detalhada com IA" --> Action_AnaliseIA["h.analise_detalhada_ia_handler"]
        Action_VerMetricas --> MainMenu
        Action_Recomendacoes --> MainMenu
        Action_AnaliseIA --> MainMenu
        
        %% Educação Financeira
        MainMenu -- "🎓 Educação Financeira" --> Edu_Menu["🎓 Menu Educação Financeira"]
        Edu_Menu -- "💡 Dica do Dia" --> Action_DicaDia["h.dica_do_dia_handler"]
        Edu_Menu -- "📚 Glossário" --> Action_Glossario["h.glossario_handler"]
        Edu_Menu -- "🎓 Módulos Educativos" --> Action_Modulos["h.modulos_educativos_handler"]
        Action_DicaDia --> MainMenu
        Action_Glossario --> MainMenu
        Action_Modulos --> MainMenu

        %% Comandos Diretos
        MainMenu -- "/ajuda" --> Action_Ajuda["h.ajuda_handler"]
        MainMenu -- "/analisar" --> Action_AnaliseIA
        MainMenu -- "/resumo" --> Action_Resumo["h.resumo_gastos_handler"]
        Action_Ajuda --> MainMenu
        Action_Resumo --> MainMenu
    end
