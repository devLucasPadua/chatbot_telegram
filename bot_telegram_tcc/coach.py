import aiohttp
import asyncio
import json
import config
import database as db
from datetime import datetime, timedelta
import logging
import random
from typing import Dict, List, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

class FinanceCoach:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.user_profiles = {}
        self.session = None
        self._response_cache = {}
        self._cache_timeout = 1800  # 30 minutos em segundos
        self._fallback_cache = {}
        
        # Configurações de timeout da API (agora vindas do config)
        self.timeout_config = aiohttp.ClientTimeout(
            total=config.API_TIMEOUT_TOTAL, 
            connect=config.API_TIMEOUT_CONNECT
        )
        self.max_retries = config.API_MAX_RETRIES
        self.retry_delay = config.API_RETRY_DELAY
        
        self.max_tokens_short = 500
        self.max_tokens_medium = 1000
        self.max_tokens_long = 3000
        
        # Sistema de prompts pré-definidos
        self._setup_prompts()
        
    def _setup_prompts(self):
        """Configura prompts pré-definidos para melhor performance"""
        self.system_prompt = "Você é Edu, um coach financeiro brasileiro. Seja DIRETO, PRÁTICO e OBJETIVO. Use no máximo 3 parágrafos. Foque em ações concretas."
        
        self.context_prompts = {
            'apos_salario': "Dê uma dica prática para {nickname} administrar o salário de forma inteligente. Seja breve e motivador:",
            'apos_gasto': "Ajude {nickname} a refletir sobre consumo consciente após registrar um gasto. Uma frase inspiradora:",
            'apos_analise': "Com base na situação financeira de {nickname} ({nivel}), dê um conselho específico e encorajador:",
            'incentivo': "{nickname} está aprendendo sobre finanças. Dê uma mensagem motivacional curta:",
            'economia': "Dica prática de economia para {nickname} implementar hoje mesmo:",
            'geral': "Dê um conselho financeiro útil e prático para {nickname}. Seja breve:"
        }
        
        self.learning_topics = {
            'orcamento': "Explique de forma simples como fazer um orçamento pessoal em uma frase prática:",
            'emergencia': "Dê uma dica rápida sobre como criar um fundo de emergência de forma acessível:",
            'dividas': "Um conselho motivacional para quem está organizando dívidas:",
            'investimentos': "Explique por que investir é importante de forma simples e inspiradora:",
            'habitos': "Compartilhe um hábito financeiro simples que traz grandes resultados:"
        }

    def _generate_cache_key(self, text: str, max_tokens: int = None) -> str:
        """Gera chave de cache mais eficiente"""
        base_string = text + (str(max_tokens) if max_tokens else "")
        return hashlib.md5(base_string.encode()).hexdigest()
        
    async def ensure_session(self):
        """Garante que temos uma sessão HTTP aberta"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                timeout=self.timeout_config,
                connector=connector
            )
            
    async def _call_deepseek_api(self, prompt: str, max_tokens: int = None) -> Optional[str]:
        """Faz chamada otimizada para a API do DeepSeek"""
        if max_tokens is None:
            max_tokens = self.max_tokens_medium
            
        logger.info(f"🤖 PROMPT ENVIADO PARA IA ({max_tokens} tokens): {prompt[:200]}...")
        
        # Verificar cache
        cache_key = self._generate_cache_key(prompt, max_tokens)
        if cache_key in self._response_cache:
            cached_time, response = self._response_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                logger.info("✅ Resposta obtida do cache")
                return response
        
        # Verificar se API key está configurada corretamente
        if not self.api_key or self.api_key in ["SUA_KEY", "SUA_KEY_AQUI", "SUA_CHAVE_API"]:
            logger.warning("❌ API key não configurada ou está com valor padrão, retornando None")
            return None # <-- Permite que o chamador use o fallback correto
        
        await self.ensure_session()
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Sistema de retry com backoff
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"🌐 Tentativa {attempt + 1} de {self.max_retries + 1} para API DeepSeek...")
                
                async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data['choices'][0]['message']['content'].strip()
                        
                        logger.info(f"✅ RESPOSTA DA IA ({len(result)} caracteres): {result[:150]}...")
                        
                        # Cache da resposta
                        self._response_cache[cache_key] = (datetime.now(), result)
                        return result
                    else:
                        error_text = await response.text()
                        logger.warning(f"❌ API retornou status {response.status}: {error_text}")
                        
                        # Se for erro do cliente (4xx), não tente novamente
                        if 400 <= response.status < 500:
                            break
                        # Se for erro do servidor (5xx), tente novamente
                        else:
                            logger.info(f"🔄 Erro {response.status}, tentando novamente...")
                            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout na tentativa {attempt + 1}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"🕒 Aguardando {wait_time}s antes da próxima tentativa")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("🚨 Todas as tentativas falharam por timeout")
                    break
                    
            except aiohttp.ClientConnectorError as e:
                logger.error(f"🔌 Erro de conexão: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    break
                    
            except Exception as e:
                logger.error(f"🚨 Erro inesperado na API: {str(e)}")
                break
        
        # Se chegou aqui, todas as tentativas falharam
        logger.info("🔄 Todas as tentativas falharam, retornando None")
        return None # <-- Permite que o chamador use o fallback correto
    
    async def _get_fallback_response(self, prompt: str) -> str:
        """Respostas fallback otimizadas"""
        logger.info("🔄 Usando resposta de fallback")
        prompt_lower = prompt.lower()
        
        fallback_key = self._generate_cache_key(prompt_lower)
        if fallback_key in self._fallback_cache:
            return self._fallback_cache[fallback_key]
        
        # Categorias e respostas otimizadas
        category_keywords = {
            'salario': ['salário', 'salario', 'receber', 'renda', 'ordenado'],
            'gasto': ['gasto', 'gastar', 'comprar', 'compra', 'despesa'],
            'economia': ['economia', 'economizar', 'poupar', 'guardar', 'poupança'],
            'divida': ['dívida', 'divida', 'emprestimo', 'empréstimo', 'cartão'],
            'investimento': ['investimento', 'investir', 'aplicação', 'aplicar'],
            'meta': ['meta', 'objetivo', 'sonho', 'conseguir']
        }
        
        fallback_responses = {
            'salario': [
                "💰 **Estratégia Salarial:** Separe 20% do seu salário assim que receber para poupança automática.",
                "🎯 **Primeiros Passos:** Ao receber o salário, priorize: 1) Contas essenciais, 2) Reserva de emergência.",
                "💡 **Dica Rápida:** Crie o hábito de revisar seu orçamento no mesmo dia que recebe o salário."
            ],
            'gasto': [
                "🤔 **Antes de Gastar:** Pergunte-se: 'Preciso disso agora?' e 'Há alternativas mais econômicas?'",
                "🎯 **Controle de Gastos:** Use a regra 50-30-20: 50% necessidades, 30% desejos, 20% poupança.",
                "💡 **Economia Inteligente:** Identifique 3 gastos não essenciais que pode reduzir este mês."
            ],
            'economia': [
                "🚀 **Micro-economias:** Economizar R$10 por dia = R$300/mês! Pequenos hábitos constroem grandes patrimônios.",
                "📱 **Corte de Assinaturas:** Reveja todas as assinaturas mensais. Cancele pelo menos uma não utilizada.",
                "🍲 **Alimentação:** Reduza 2 deliveries por semana = economia de ~R$200/mês."
            ],
            'divida': [
                "🎯 **Estratégia de Dívidas:** Foque na dívida com maior juros primeiro (cartão de crédito).",
                "💡 **Plano de Pagamento:** Liste todas as dívidas por valor e juros. Estabeleça um plano agressivo.",
                "🔄 **Reorganização:** Considere um empréstimo com juros menores para quitar dívidas de juros altos."
            ],
            'investimento': [
                "💰 **Primeiros Investimentos:** Comece com a reserva de emergência (6 meses de gastos).",
                "🎯 **Estratégia Conservadora:** Para iniciantes: 70% em renda fixa, 30% em renda variável.",
                "💡 **Dica Inicial:** Invista regularmente (mesmo valores pequenos) e pense no longo prazo."
            ],
            'meta': [
                "🎯 **Metas SMART:** Seja Específico, Mensurável, Atingível, Relevante e Temporal.",
                "💡 **Quebra de Metas:** Divida metas grandes em etapas mensais.",
                "📊 **Acompanhamento:** Revise o progresso das suas metas toda semana."
            ],
            'geral': [
                "💡 **Hábito Financeiro:** Reserve 10 minutos por semana para revisar seus gastos.",
                "🎯 **Foco no Essencial:** Priorize construir uma reserva de emergência antes de investimentos complexos.",
                "💰 **Mentalidade:** Educação financeira é sobre fazer seu dinheiro trabalhar para você."
            ]
        }
        
        # Identificação de categoria
        selected_category = 'geral'
        for category, keywords in category_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                selected_category = category
                break
        
        response = random.choice(fallback_responses[selected_category])
        self._fallback_cache[fallback_key] = response
        return response

    def analyze_financial_health(self, user_id: int) -> Dict:
        """Analisa a saúde financeira do usuário"""
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                return self._get_default_analysis()
            
            expenses = db.get_monthly_expenses(user_id)
            salario = user_data.get('salario_liquido', 0)
            
            total_fixo = self._calculate_total_expenses(expenses['fixo'])
            total_flexivel = self._calculate_total_expenses(expenses['flexivel'])
            total_geral = total_fixo + total_flexivel
            
            if salario <= 0:
                return self._build_analysis_response('inicial', total_fixo, total_flexivel, total_geral, 
                                                   "💡 Vamos começar organizando sua renda! Que tal definir seu salário primeiro?",
                                                   "Configure sua renda mensal para uma análise mais precisa.",
                                                   salario, total_geral)
            
            saldo = salario - total_geral
            percentual_gastos = (total_geral / salario) * 100 if salario > 0 else 0
            
            if total_geral == 0:
                return self._build_analysis_response('inicial', total_fixo, total_flexivel, total_geral,
                                                   "🎯 Ótimo começo! Agora vamos registrar seus primeiros gastos.",
                                                   "Comece adicionando seus gastos fixos essenciais.",
                                                   salario, total_geral, saldo, percentual_gastos)
                
            elif percentual_gastos <= 60:
                return self._build_analysis_response('saudavel', total_fixo, total_flexivel, total_geral,
                                                   "✅ Excelente! Suas finanças estão equilibradas.",
                                                   "Mantenha esse controle e pense em investir o excedente.",
                                                   salario, total_geral, saldo, percentual_gastos)
                
            elif percentual_gastos <= 85:
                return self._build_analysis_response('atencao', total_fixo, total_flexivel, total_geral,
                                                   "⚠️ Fique atento! Seus gastos estão chegando no limite.",
                                                   "Revise gastos flexíveis e identifique economias possíveis.",
                                                   salario, total_geral, saldo, percentual_gastos)
                
            else:
                return self._build_analysis_response('critico', total_fixo, total_flexivel, total_geral,
                                                   "🚨 Atenção! Você está gastando mais do que ganha.",
                                                   "Priorize gastos essenciais e reveja seu orçamento urgentemente.",
                                                   salario, total_geral, saldo, percentual_gastos)
                
        except Exception as e:
            logger.error(f"Erro na análise financeira: {e}")
            return self._get_default_analysis()
    
    def _calculate_total_expenses(self, expenses_dict: Dict) -> float:
        """Calcula o total de gastos de um dicionário de despesas"""
        if not expenses_dict:
            return 0
            
        total = 0
        for subcategorias in expenses_dict.values():
            if isinstance(subcategorias, dict):
                for valor in subcategorias.values():
                    if isinstance(valor, (int, float)):
                        total += valor
        return total
    
    def _build_analysis_response(self, nivel: str, total_fixo: float, total_flexivel: float, 
                               total_geral: float, mensagem: str, recomendacao: str,
                               salario: float = 0, total_gastos: float = 0, 
                               saldo: float = 0, percentual_gastos: float = 0) -> Dict:
        """Constrói resposta padronizada de análise"""
        return {
            'nivel': nivel,
            'mensagem': mensagem,
            'recomendacao': recomendacao,
            'saldo': saldo,
            'percentual_gastos': percentual_gastos,
            'total_fixo': total_fixo,
            'total_flexivel': total_flexivel,
            'total_geral': total_geral,
            'salario': salario,
            'total_gastos': total_gastos
        }
    
    def _get_default_analysis(self) -> Dict:
        """Retorna análise padrão para casos de erro"""
        return self._build_analysis_response(
            'inicial', 0, 0, 0,
            '💡 Vamos começar sua jornada financeira!',
            'Adicione seu salário e primeiros gastos para uma análise personalizada.'
        )
    
    async def get_personalized_tip(self, user_id: int, context: str = "geral") -> str:
        """Retorna uma dica personalizada baseada no contexto"""
        try:
            analysis = self.analyze_financial_health(user_id)
            user_data = db.get_user_data(user_id)
            nickname = user_data.get('nickname', "Amigo") if user_data else "Amigo"
            
            prompt_template = self.context_prompts.get(context, self.context_prompts['geral'])
            prompt = prompt_template.format(nickname=nickname, nivel=analysis['nivel'])
            
            if context == 'apos_analise' and analysis['nivel'] != 'inicial':
                prompt += f" Situação: {analysis['mensagem']}"
                
            response = await self._call_deepseek_api(prompt, max_tokens=self.max_tokens_short)
            return response
            
        except Exception as e:
            logger.error(f"Erro ao obter dica personalizada: {e}")
            return await self._get_fallback_response("dica motivacional")

    async def get_personalized_recommendations(self, user_id: int) -> str:
        """Obtém recomendações personalizadas de forma otimizada"""
        logger.info(f"🎯 Iniciando recomendações personalizadas para usuário {user_id}")
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                logger.warning("❌ Usuário não encontrado para recomendações")
                return self._get_quick_fallback_recommendations()
            
            analysis = self.analyze_financial_health(user_id)
            salario = user_data.get('salario_liquido', 0)
            
            prompt = self._build_recommendation_prompt(analysis, salario)
            response = await self._call_deepseek_api(prompt, max_tokens=self.max_tokens_medium)
            return response or self._get_quick_fallback_recommendations()
            
        except Exception as e:
            logger.error(f"Erro otimizado nas recomendações: {e}")
            return self._get_quick_fallback_recommendations()
    
    def _build_recommendation_prompt(self, analysis: Dict, salario: float) -> str:
        """Constrói prompt para recomendações"""
        return f"""
        Dados financeiros RESUMIDOS:
        - Salário: R$ {salario:,.0f}
        - Gastos totais: R$ {analysis.get('total_geral', 0):,.0f} ({analysis.get('percentual_gastos', 0):.0f}% do salário)
        - Saldo: R$ {analysis.get('saldo', 0):,.0f}
        - Saúde: {analysis.get('nivel', 'inicial')}
        
        Forneça 3-4 recomendações PRÁTICAS e DIRETAS. Seja objetivo e focando em ações imediatas.
        """

    async def get_detailed_analysis(self, user_id: int) -> str:
        """Faz análise detalhada otimizada"""
        logger.info(f"📊 Iniciando análise detalhada para usuário {user_id}")
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                logger.warning("❌ Usuário não encontrado para análise detalhada")
                return "📊 Complete seu cadastro para uma análise personalizada."
            
            analysis = self.analyze_financial_health(user_id)
            salario = user_data.get('salario_liquido', 0)
            
            prompt = self._build_detailed_analysis_prompt(analysis, salario)
            response = await self._call_deepseek_api(prompt, max_tokens=self.max_tokens_long)
            return response or self._get_quick_analysis_fallback()
            
        except Exception as e:
            logger.error(f"Erro otimizado na análise: {e}")
            return self._get_quick_analysis_fallback()

    def _build_detailed_analysis_prompt(self, analysis: Dict, salario: float) -> str:
        """Constrói prompt para análise detalhada"""
        return f"""
        Situação financeira RESUMIDA:
        - Renda: R$ {salario:,.0f}/mês
        - Gastos: R$ {analysis.get('total_geral', 0):,.0f}/mês ({analysis.get('percentual_gastos', 0):.0f}% da renda)
        - Fixos: R$ {analysis.get('total_fixo', 0):,.0f}, Flexíveis: R$ {analysis.get('total_flexivel', 0):,.0f}
        - Saldo: R$ {analysis.get('saldo', 0):,.0f}
        - Saúde: {analysis.get('nivel', 'inicial')}
        
        Forneça uma análise CONCISA com: 1) Pontos fortes, 2) Pontos de atenção, 3) 2-3 ações prioritárias.
        Seja direto e prático.
        """

    def _get_quick_analysis_fallback(self) -> str:
        """Fallback rápido para análise"""
        logger.info("🔄 Usando fallback rápido para análise")
        analyses = [
            "📊 **ANÁLISE RÁPIDA:**\n\nPontos fortes: Controle de gastos ativo\nAtenção: Otimizar gastos flexíveis\nAções: 1) Revisar assinaturas 2) Estabelecer metas 3) Automatizar poupança",
            "💎 **DIAGNÓSTICO:**\n\nSituação: Em desenvolvimento\nOportunidades: Economia em pequenos gastos\nPrioridades: Reserva de emergência, Educação financeira contínua",
            "🎯 **VISÃO GERAL:**\n\nProgresso: Registro financeiro consistente\nMelhorias: Diversificação de receitas\nFoco: Estabilidade financeira de curto prazo"
        ]
        return random.choice(analyses)

    async def get_suggested_goals(self, user_id: int) -> str:
        """Metas sugeridas otimizadas"""
        logger.info(f"🎯 Iniciando metas sugeridas para usuário {user_id}")
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                logger.warning("❌ Usuário não encontrado para metas sugeridas")
                return self._get_quick_goals_fallback()
            
            analysis = self.analyze_financial_health(user_id)
            salario = user_data.get('salario_liquido', 0)
            
            prompt = f"""
            Situação: Salário R$ {salario:,.0f}, Saúde {analysis['nivel']}
            Sugira 3 metas financeiras REALISTAS e PRÁTICAS. Seja específico e direto.
            """
            
            response = await self._call_deepseek_api(prompt, max_tokens=120)
            return response or self._get_quick_goals_fallback()
            
        except Exception as e:
            logger.error(f"Erro otimizado em metas: {e}")
            return self._get_quick_goals_fallback()

    def _get_quick_goals_fallback(self) -> str:
        """Fallback rápido para metas"""
        logger.info("🔄 Usando fallback rápido para metas")
        goals = [
            "🎯 **METAS SUGERIDAS:**\n\n1. Reserva de emergência (3 meses)\n2. Redução de dívidas em 30%\n3. Investimento mensal de 10% da renda",
            "🌟 **OBJETIVOS REALISTAS:**\n\n• Economizar R$ X em 6 meses\n• Quitar cartão de crédito\n• Criar fundo para estudos\n• Investir em educação financeira"
        ]
        return random.choice(goals)

    def get_quick_tip(self) -> str:
        """Dica rápida sem necessidade de API"""
        logger.info("💡 Gerando dica rápida")
        tips = [
            "💡 **Regra 24h:** Espere um dia antes de compras não essenciais. Evita arrependimentos!",
            "🎯 **Desafio semanal:** Tente uma semana sem delivery. Sua carteira agradece! 🍲",
            "💰 **Economia invisível:** Cancele uma assinatura que não usa. Surpresa positiva! 📱",
            "📊 **Meta micro:** Guarde R$ 5 por dia. No mês: R$ 150! Pequenos hábitos! 🌱",
            "🛒 **Lista poderosa:** Sempre faça lista de compras. Foge do impulso! 📝",
            "💎 **Futuro você:** Toda economia é um presente para seu futuro eu! 🌟",
            "🚀 **Progresso:** Não perfeição, progresso! Cada passo importa! 💪",
            "🌱 **Jornada:** Organizar finanças é como plantar: colheita vem com tempo! ⏳"
        ]
        return random.choice(tips)

    async def get_learning_moment(self, user_id: int, topic: str = None) -> str:
        """Fornece um momento de aprendizado sobre um tópico específico"""
        logger.info(f"🎓 Solicitando momento de aprendizado: {topic}")
        
        if topic and topic in self.learning_topics:
            prompt = self.learning_topics[topic]
        else:
            prompt = random.choice(list(self.learning_topics.values()))
            
        response = await self._call_deepseek_api(prompt, max_tokens=self.max_tokens_short)
        return response

    async def get_celebration_message(self, user_id: int, achievement: str) -> str:
        """Mensagem de celebração para conquistas"""
        logger.info(f"🎉 Gerando mensagem de celebração: {achievement}")
        
        celebrations = {
            'primeiro_gasto': "🎉 Parabéns pelo primeiro gasto registrado! Este é o primeiro passo para o controle financeiro!",
            'salario_definido': "💰 Ótimo! Com salário definido, você já tem o mapa para sua jornada financeira!",
            'resumo_visto': "📊 Excelente! Acompanhar seus gastos é a chave para mudanças reais!",
            'economia_feita': "🌟 Fantástico! Pequenas economias hoje constroem grandes conquistas amanhã!",
            'meta_atingida': "🎯 Incrível! Você está progredindo em direção aos seus objetivos!"
        }
        
        if achievement in celebrations:
            return celebrations[achievement]
        
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname'] if user_data else "Amigo"
        
        prompt = f"Escreva uma mensagem curta e motivacional para {nickname} celebrando um marco na jornada financeira. Seja empático:"
        response = await self._call_deepseek_api(prompt, max_tokens=60)
        return response

    def get_user_insights(self, user_id: int) -> Dict:
        """Fornece insights sobre os padrões de gasto do usuário"""
        logger.info(f"🔍 Gerando insights para usuário {user_id}")
        try:
            expenses = db.get_monthly_expenses(user_id)
            
            maior_categoria_fixo = None
            maior_valor_fixo = 0
            
            for categoria, subcategorias in expenses['fixo'].items():
                total_categoria = sum(subcategorias.values())
                if total_categoria > maior_valor_fixo:
                    maior_valor_fixo = total_categoria
                    maior_categoria_fixo = categoria
                    
            maior_categoria_flexivel = None
            maior_valor_flexivel = 0
            
            for categoria, subcategorias in expenses['flexivel'].items():
                total_categoria = sum(subcategorias.values())
                if total_categoria > maior_valor_flexivel:
                    maior_valor_flexivel = total_categoria
                    maior_categoria_flexivel = categoria
                    
            return {
                'maior_gasto_fixo': {
                    'categoria': maior_categoria_fixo,
                    'valor': maior_valor_fixo
                },
                'maior_gasto_flexivel': {
                    'categoria': maior_categoria_flexivel,
                    'valor': maior_valor_flexivel
                },
                'total_categorias_fixo': len(expenses['fixo']),
                'total_categorias_flexivel': len(expenses['flexivel'])
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter insights: {e}")
            return {
                'maior_gasto_fixo': {'categoria': None, 'valor': 0},
                'maior_gasto_flexivel': {'categoria': None, 'valor': 0},
                'total_categorias_fixo': 0,
                'total_categorias_flexivel': 0
            }

    def _format_expenses_for_analysis(self, expenses_dict):
        """Formata os gastos para análise da IA"""
        if not expenses_dict:
            return "Nenhum gasto registrado nesta categoria"
        
        formatted = []
        for categoria, subcategorias in expenses_dict.items():
            total_categoria = 0
            for subcat_dict in subcategorias.values():
                if isinstance(subcat_dict, dict):
                    total_categoria += sum(subcat_dict.values())
                else:
                    total_categoria += subcat_dict
            formatted.append(f"- {categoria}: R$ {total_categoria:,.2f}")
            
        return "\n".join(formatted)

    def _get_quick_fallback_recommendations(self) -> str:
        """Fallback rápido para recomendações"""
        logger.info("🔄 Usando fallback rápido para recomendações")
        recommendations = [
            "🎯 **RECOMENDAÇÕES PRÁTICAS:**\n\n1. Revise 3 gastos não essenciais esta semana\n2. Automatize poupança (10% do salário)\n3. Estabeleça uma meta financeira clara\n4. Acompanhe gastos diariamente por 7 dias",
            "💡 **AÇÕES IMEDIATAS:**\n\n• Corte uma assinatura não utilizada\n• Estabeleça limite para gastos flexíveis\n• Crie reserva para emergências\n• Negocie dívidas com juros altos",
            "🚀 **ESTRATÉGIAS RÁPIDAS:**\n\n1. Regra 50-30-20 para orçamento\n2. Revisão semanal de extratos\n3. Meta de economia mensal realista\n4. Planeamento de compras grandes"
        ]
        return random.choice(recommendations)
        
    async def get_ai_quick_tip(self) -> str:
        """Gera uma dica rápida e motivacional usando a IA."""
        logger.info("🤖 Gerando Dica do Dia com IA...")
        
        prompt = "Dê um conselho financeiro útil e prático para um usuário no Brasil. Seja breve, direto, motivador e use no máximo 2 frases."
        
        try:
            # Chamar a API com tokens curtos
            response = await self._call_deepseek_api(
                prompt, 
                max_tokens=self.max_tokens_short
            )
            
            if response:
                return response
            else:
                # Se a API falhar (chave, timeout, etc.), use o fallback estático
                logger.warning("🤖 Falha na API. Usando dica de fallback (get_quick_tip).")
                return self.get_quick_tip() # Chama o método estático
                
        except Exception as e:
            logger.error(f"Erro ao gerar dica de IA: {e}")
            return self.get_quick_tip() # Fallback em caso de exceção

    async def close_session(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def __del__(self):
        """Destrutor para garantir que a sessão seja fechada"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.close_session())

# Instância global do coach
finance_coach = FinanceCoach()

# Funções de conveniência para uso direto
async def get_quick_tip():
    return finance_coach.get_quick_tip()

async def get_personalized_advice(user_id: int, context: str = "geral"):
    return await finance_coach.get_personalized_tip(user_id, context)

async def analyze_financial_situation(user_id: int):
    return finance_coach.analyze_financial_health(user_id)

async def get_learning_content(user_id: int, topic: str = None):
    return await finance_coach.get_learning_moment(user_id, topic)

async def get_detailed_analysis(user_id: int):
    """Função de conveniência para análise detalhada"""
    return await finance_coach.get_detailed_analysis(user_id)