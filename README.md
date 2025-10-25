Bot de Finanças Pessoais com Coach Inteligente
Descrição do Projeto

Este projeto consiste em um bot para Telegram desenvolvido em Python que atua como assistente financeiro pessoal com funcionalidades de coaching inteligente. O sistema permite aos usuários registrar transações financeiras, acompanhar seu extrato e receber orientação personalizada sobre educação financeira, adaptada ao contexto econômico brasileiro.

O diferencial deste bot é a integração com inteligência artificial para fornecer conselhos financeiros contextualizados, considerando a realidade econômica do usuário e oferecendo ensino progressivo sobre conceitos fundamentais de finanças pessoais.
Funcionalidades Principais
Gestão de Transações

    Registro de salários, gastos e créditos extras

    Sistema de calendário interativo para seleção de datas

    Extrato financeiro com saldo atualizado

    Histórico de transações organizado temporalmente

Coach Financeiro Inteligente

    Análise personalizada da situação financeira do usuário

    Recomendações baseadas em IA considerando a realidade brasileira

    Micro-aulas educacionais após cada transação

    Dicas rápidas e contextualizadas sobre finanças

    Ensino progressivo de conceitos financeiros

Características Técnicas

    Interface conversacional natural via Telegram

    Banco de dados SQLite para persistência de dados

    Sistema de cache para otimização de performance

    Arquitetura modular e escalável

Tecnologias Utilizadas

    Python 3.8+ - Linguagem de programação principal

    python-telegram-bot - Framework para integração com Telegram

    SQLite - Banco de dados para armazenamento local

    DeepSeek API - Serviço de inteligência artificial para geração de conteúdo

    Requests - Cliente HTTP para consumo de APIs

Estrutura do Projeto
text

bot_telegram_tcc/
├── bot.py                 # Arquivo principal de execução do bot
├── config.txt             # Configurações e chaves de API
├── database.txt           # Modelos e operações de banco de dados
├── handlers.txt           # Gerenciadores de comandos e conversações
├── coach.txt              # Lógica do coach financeiro inteligente
└── README.md              # Documentação do projeto

Configuração e Instalação
Pré-requisitos

    Python 3.8 ou superior

    Conta no Telegram

    Token do Bot do Telegram (obtido via @BotFather)

    Chave de API do DeepSeek (opcional)

Instalação

    Clone o repositório:

bash

git clone <url-do-repositorio>
cd bot_telegram_tcc

    Instale as dependências necessárias:

bash

pip install python-telegram-bot requests

    Configure as variáveis de ambiente no arquivo config.txt:

python

BOT_TOKEN = "seu_token_do_telegram"
DEEPSEEK_API_KEY = "sua_chave_da_api_deepseek"
SALARIO_MINIMO = 1412.00

    Execute o bot:

bash

python bot.py

Utilização
Comandos Disponíveis

    /start - Inicia o bot e realiza cadastro do usuário

    /salario - Registra um novo salário

    /gasto - Registra uma despesa

    /credito - Registra um crédito extra

    /extrato - Exibe o extrato financeiro

    /aprender - Acessa lições personalizadas de educação financeira

    /dica - Recebe uma dica financeira rápida

Fluxo de Interação

    Cadastro Inicial: O usuário inicia com /start e fornece um apelido

    Menu Principal: Interface com opções organizadas por categorias

    Registro de Transações: Processo guiado para inserção de valores, datas e descrições

    Feedback Educacional: Após cada transação, o bot oferece insights relevantes

    Acompanhamento: Extrato atualizado e análise contínua dos hábitos financeiros

Metodologia Educacional

O sistema implementa uma abordagem progressiva de educação financeira:

    Contextualização Brasileira: Considera a realidade econômica local e desigualdades sociais

    Microlearning: Conteúdo em pequenas doses após cada interação

    Personalização: Análise individual dos padrões de gastos e renda

    Progressão Gradual: Ensino que evolui conforme o usuário avança

    Linguagem Acessível: Explicações simples sem jargões complexos

Arquitetura do Sistema
Módulos Principais

    Core Bot (bot.py) - Gerencia a aplicação principal e handlers

    Database Layer (database.txt) - Operações de persistência e queries

    Conversation Handlers (handlers.txt) - Fluxos de conversação e estados

    AI Coach (coach.txt) - Lógica de análise e geração de conteúdo educativo

Padrões de Design

    Conversation Handler para gerenciamento de estados

    Repository Pattern para acesso a dados

    Strategy Pattern para diferentes tipos de análise financeira

    Cache Pattern para otimização de performance

Considerações sobre Privacidade e Segurança

    Dados armazenados localmente com SQLite

    Identificação por ID único do Telegram

    Processamento de dados financeiros de forma anônima

    Comunicação segura com APIs via HTTPS

Limitações e Melhorias Futuras
Limitações Atuais

    Dependência de conexão com API externa para funcionalidades avançadas

    Armazenamento local limita acesso multi-dispositivo

    Análises baseadas apenas em transações registradas manualmente

Roadmap de Melhorias

    Implementação de categorização automática de gastos

    Integração com sistemas bancários (Open Banking)

    Relatórios analíticos mais detalhados

    Sistema de metas e planejamento financeiro

    Versão web complementar

Contribuição

Contribuições são bem-vindas. Para colaborar:

    Faça um fork do projeto

    Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)

    Commit suas mudanças (git commit -m 'Add some AmazingFeature')

    Push para a branch (git push origin feature/AmazingFeature)

    Abra um Pull Request