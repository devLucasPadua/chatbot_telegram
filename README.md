🤖 Bot de Finanças Pessoais para Telegram

Um bot inteligente e fácil de usar para gerenciar suas finanças pessoais diretamente no Telegram. Com interface intuitiva e persistência de dados, você pode controlar receitas, despesas e acompanhar seu saldo em tempo real.

https://img.shields.io/badge/Python-3.8+-blue.svg
https://img.shields.io/badge/Telegram-Bot-blue.svg
https://img.shields.io/badge/License-MIT-green.svg

✨ Funcionalidades

· 💰 Saldo Inicial - Configure seu saldo inicial
· 💳 Adicionar Créditos - Registre entradas de dinheiro com descrição
· 💸 Adicionar Débitos - Registre gastos e despesas
· 📊 Saldo Atual - Consulte seu saldo em tempo real
· 📋 Extrato Completo - Visualize histórico de transações
· 💾 Persistência - Dados salvos em SQLite
· 🎯 Interface Intuitiva - Menu com teclado personalizado
· ⚡ Tempo Real - Cálculos instantâneos

🚀 Começando

Pré-requisitos

· Python 3.8 ou superior
· Conta no Telegram
· Token do BotFather

📦 Instalação

1. Clone o repositório

```bash
https://github.com/devLucasPadua/chatbot_telegram.git
cd chatbot_telegram
```

1. Instale as dependências

```bash
pip install python-telegram-bot
```

1. Configure o bot
   · Abra o config.py
   · Substitua "SEU_TOKEN_AQUI" pelo token do seu bot

```python
# config.py
BOT_TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
```

🔧 Como obter o token do bot

1. Abra o Telegram e procure por @BotFather
2. Envie /newbot
3. Siga as instruções para criar um novo bot
4. Copie o token fornecido
5. Cole no arquivo config.py

🎮 Como usar

1. Inicie o bot

```bash
python bot.py
```

1. No Telegram
   · Procure pelo seu bot (@SeuBotName)
   · Envie /start
   · Digite como quer ser chamado
   · Use o menu para gerenciar suas finanças

📱 Fluxo de uso

```
/start → Digite nome → Menu Principal
```

Opções do menu:

· ➕ Saldo Inicial - Configure seu saldo inicial
· 💳 Adicionar Crédito - Registre uma entrada (ex: Salário)
· 💸 Adicionar Débito - Registre uma saída (ex: Aluguel)
· 📊 Saldo Atual - Veja seu saldo atual
· 📋 Extrato - Histórico completo de transações

🏗️ Estrutura do Projeto

```
finance-bot-telegram/
├── bot.py              # Aplicação principal
├── handlers.py         # Handlers das conversas
├── database.py         # Gerenciamento do banco de dados
├── config.py          # Configurações (token do bot)
├── finance.db         # Banco de dados (criado automaticamente)
└── README.md          # Este arquivo
```

🗃️ Esquema do Banco de Dados

Tabela users:

· user_id (INTEGER) - ID único do usuário no Telegram
· nickname (TEXT) - Nome escolhido pelo usuário

Tabela transactions:

· id (INTEGER) - ID único da transação
· user_id (INTEGER) - ID do usuário
· type (TEXT) - 'credit' ou 'debit'
· amount (REAL) - Valor da transação
· description (TEXT) - Descrição/origem
· timestamp (DATETIME) - Data e hora automática

🛠️ Desenvolvimento

🔍 Logs e Debug

O bot inclui sistema de logging para facilitar o debug:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

📈 Exemplo de Uso

```
Usuário: /start
Bot: Olá! Sou seu assistente financeiro. Como você gostaria de ser chamado?

Usuário: João
Bot: Perfeito, João! Vamos gerenciar suas finanças: [Menu]

Usuário: [💳 Adicionar Crédito]
Bot: Valor do crédito:
Usuário: 1500
Bot: Qual a origem deste crédito?
Usuário: Salário
Bot: ✅ Crédito de R$ 1500.00 adicionado com sucesso!

Usuário: [📊 Saldo Atual]
Bot: 💰 Saldo atual de João: R$ 1500.00
```

🐛 Solução de Problemas

Erros Comuns

1. "Token inválido"
   · Verifique se o token no config.py está correto
   · Confirme se o bot foi criado com sucesso no BotFather
2. "Cannot connect to Telegram"
   · Verifique sua conexão com a internet
   · Confirme se não há firewall bloqueando a conexão
3. Erros de banco de dados
   · Certifique-se de que o Python tem permissão de escrita no diretório
   · Delete o arquivo finance.db para recriar o banco

📋 Requisitos do Sistema

· Python 3.8+
· Conexão com internet
· Acesso ao Telegram
· Permissões de arquivo para criar/ler o banco SQLite

🤝 Contribuindo

Contribuições são sempre bem-vindas!

1. Fork o projeto
2. Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)
3. Commit suas mudanças (git commit -m 'Add some AmazingFeature')
4. Push para a branch (git push origin feature/AmazingFeature)
5. Abra um Pull Request

📝 TODO List

· Adicionar categorias para transações
· Gráficos de gastos mensais
· Exportar extrato para CSV
· Orçamentos mensais
· Lembretes de contas a pagar

📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

👨‍💻 Autor

Criado com ❤️ por Seu Nome

🙏 Agradecimentos

· python-telegram-bot - Excelente biblioteca para bots do Telegram
· Comunidade Python Brasil

---

⭐ Não esqueça de dar uma estrela se este projeto foi útil para você!

📞 Suporte

Se você encontrar algum problema ou tiver sugestões, sinta-se à vontade para:

1. Abrir uma issue
2. Enviar um e-mail para: seu-email@exemplo.com

🚀 Status do Projeto

https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellowgreen

Versão: 1.0.0
Última atualização: Dezembro 2024

---

<div align="center">
💡 Dica: Mantenha seu bot sempre atualizado para novas funcionalidades e correções de segurança!
</div>
