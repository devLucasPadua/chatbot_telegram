import aiohttp
import asyncio
import json
import config
import database as db
from datetime import datetime, timedelta
import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FinanceCoach:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.user_profiles = {}
        self.session = None
        self._response_cache = {}
        self._cache_timeout = 1800  # 30 minutos em segundos
        # Cache de fallback para evitar chamadas repetidas à API
        self._fallback_cache = {}
        
    async def ensure_session(self):
        """Garante que temos uma sessão HTTP aberta com timeout otimizado"""
        if self.session is None or self.session.closed:
            # Timeout mais agressivo: 8 segundos no total, 5 segundos de conexão
            timeout = aiohttp.ClientTimeout(total=8, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
    async def _call_deepseek_api(self, prompt: str, max_tokens: int = 120) -> Optional[str]:
        """Faz chamada otimizada para a API do DeepSeek com fallback rápido"""
        # LOG DO PROMPT ENVIADO
        logger.info(f"🤖 PROMPT ENVIADO PARA IA ({max_tokens} tokens): {prompt[:200]}...")
        
        # Verificar cache primeiro
        cache_key = hash(prompt + str(max_tokens))
        if cache_key in self._response_cache:
            cached_time, response = self._response_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                logger.info("✅ Resposta obtida do cache")
                return response
        
        # Verificar se API key está configurada
        if not self.api_key or self.api_key == "SUA_KEY_AQUI":
            logger.info("❌ API key não configurada, usando fallback")
            return await self._get_fallback_response(prompt)
        
        await self.ensure_session()
        
        # Payload otimizado para respostas mais rápidas
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é Edu, um coach financeiro brasileiro. Seja DIRETO, PRÁTICO e OBJETIVO. Use no máximo 3 parágrafos. Foque em ações concretas."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,  # Reduzido para respostas mais curtas
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # LOG DA TENTATIVA DE CHAMADA
            logger.info(f"🌐 Chamando API DeepSeek...")
            
            # Timeout mais agressivo com fallback rápido
            async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data['choices'][0]['message']['content'].strip()
                    
                    # LOG DA RESPOSTA RECEBIDA
                    logger.info(f"✅ RESPOSTA DA IA ({len(result)} caracteres): {result[:150]}...")
                    
                    # Cache da resposta
                    self._response_cache[cache_key] = (datetime.now(), result)
                    return result
                else:
                    error_text = await response.text()
                    logger.warning(f"❌ API retornou status {response.status}: {error_text}")
                    return await self._get_fallback_response(prompt)
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout na chamada da API - usando fallback")
            return await self._get_fallback_response(prompt)
        except Exception as e:
            logger.error(f"🚨 Erro na API: {str(e)}")
            return await self._get_fallback_response(prompt)
    
    async def _get_fallback_response(self, prompt: str) -> str:
        """Respostas fallback otimizadas e contextualizadas"""
        logger.info("🔄 Usando resposta de fallback")
        prompt_lower = prompt.lower()
        
        # Cache de fallback para evitar processamento repetido
        fallback_key = hash(prompt_lower)
        if fallback_key in self._fallback_cache:
            return self._fallback_cache[fallback_key]
        
        # Respostas pré-definidas otimizadas por categoria
        fallback_responses = {
            'salario': [
                "💰 **Estratégia Salarial:** Separe 20% do seu salário assim que receber para poupança automática. O restante divida entre necessidades (50%) e desejos (30%).",
                "🎯 **Primeiros Passos:** Ao receber o salário, priorize: 1) Contas essenciais, 2) Reserva de emergência, 3) Metas financeiras. Deixe os gastos flexíveis por último.",
                "💡 **Dica Rápida:** Crie o hábito de revisar seu orçamento no mesmo dia que recebe o salário. 15 minutos de planeamento evitam surpresas no mês."
            ],
            'gasto': [
                "🤔 **Antes de Gastar:** Pergunte-se: 'Preciso disso agora?' e 'Há alternativas mais econômicas?'. Muitas compras impulsivas são evitadas com 24h de reflexão.",
                "🎯 **Controle de Gastos:** Use a regra 50-30-20: 50% necessidades, 30% desejos, 20% poupança. Revise semanalmente seus gastos para ajustes.",
                "💡 **Economia Inteligente:** Identifique 3 gastos não essenciais que pode reduzir este mês. Pequenos cortes geram grandes economias anuais."
            ],
            'economia': [
                "🚀 **Micro-economias:** Economizar R$10 por dia = R$300/mês = R$3.600/ano! Pequenos hábitos constroem grandes patrimônios.",
                "📱 **Corte de Assinaturas:** Reveja todas as assinaturas mensais. Cancele pelo menos uma que não usa regularmente.",
                "🍲 **Alimentação:** Reduza 2 deliveries por semana = economia de ~R$200/mês. Cozinhar em casa é mais saudável e econômico."
            ],
            'divida': [
                "🎯 **Estratégia de Dívidas:** Foque na dívida com maior juros primeiro (cartão de crédito). Negocie prazos maiores para as outras.",
                "💡 **Plano de Pagamento:** Liste todas as dívidas por valor e juros. Estabeleça um plano de pagamento agressivo para a mais crítica.",
                "🔄 **Reorganização:** Considere um empréstimo com juros menores para quitar dívidas de juros altos, mas discipline-se para não criar novas dívidas."
            ],
            'investimento': [
                "💰 **Primeiros Investimentos:** Comece com a reserva de emergência (6 meses de gastos). Depois, explore Tesouro Direto e fundos de baixo risco.",
                "🎯 **Estratégia Conservadora:** Para iniciantes: 70% em renda fixa (Tesouro, CDB), 30% em renda variável (ações, fundos). Ajuste conforme seu perfil.",
                "💡 **Dica Inicial:** Invista regularmente (mesmo valores pequenos) e pense no longo prazo. Juros compostos são seus maiores aliados."
            ],
            'meta': [
                "🎯 **Metas SMART:** Seja Específico, Mensurável, Atingível, Relevante e Temporal. Ex: 'Economizar R$5.000 para emergência em 10 meses'.",
                "💡 **Quebra de Metas:** Divida metas grandes em etapas mensais. Economizar R$500/mês parece mais fácil que R$6.000/ano.",
                "📊 **Acompanhamento:** Revise o progresso das suas metas toda semana. Celebre pequenas vitórias para manter a motivação."
            ],
            'geral': [
                "💡 **Hábito Financeiro:** Reserve 10 minutos por semana para revisar seus gastos. Consistência é mais importante que perfeição.",
                "🎯 **Foco no Essencial:** Priorize construir uma reserva de emergência antes de investimentos complexos. Segurança primeiro, crescimento depois.",
                "💰 **Mentalidade:** Educação financeira não é sobre restrição, mas sobre fazer seu dinheiro trabalhar para você. Cada decisão conta."
            ]
        }
        
        # Identificação mais precisa da categoria
        if any(word in prompt_lower for word in ['salário', 'salario', 'receber', 'renda', 'ordenado']):
            response = random.choice(fallback_responses['salario'])
        elif any(word in prompt_lower for word in ['gasto', 'gastar', 'comprar', 'compra', 'despesa']):
            response = random.choice(fallback_responses['gasto'])
        elif any(word in prompt_lower for word in ['economia', 'economizar', 'poupar', 'guardar', 'poupança']):
            response = random.choice(fallback_responses['economia'])
        elif any(word in prompt_lower for word in ['dívida', 'divida', 'emprestimo', 'empréstimo', 'cartão']):
            response = random.choice(fallback_responses['divida'])
        elif any(word in prompt_lower for word in ['investimento', 'investir', 'aplicação', 'aplicar']):
            response = random.choice(fallback_responses['investimento'])
        elif any(word in prompt_lower for word in ['meta', 'objetivo', 'sonho', 'conseguir']):
            response = random.choice(fallback_responses['meta'])
        else:
            response = random.choice(fallback_responses['geral'])
        
        # Cache da resposta de fallback
        self._fallback_cache[fallback_key] = response
        return response

    def analyze_financial_health(self, user_id: int) -> Dict:
        """Analisa a saúde financeira do usuário com base nos gastos"""
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                return self._get_default_analysis()
            
            expenses = db.get_monthly_expenses(user_id)
            salario = user_data['salario_liquido'] or 0
            
            total_fixo = 0
            total_flexivel = 0
            
            if expenses['fixo']:
                for categoria, subcategorias in expenses['fixo'].items():
                    for subcat, valor in subcategorias.items():
                        total_fixo += valor
                        
            if expenses['flexivel']:
                for categoria, subcategorias in expenses['flexivel'].items():
                    for subcat, valor in subcategorias.items():
                        total_flexivel += valor
                        
            total_geral = total_fixo + total_flexivel
            
            if salario <= 0:
                return {
                    'nivel': 'inicial',
                    'mensagem': '💡 Vamos começar organizando sua renda! Que tal definir seu salário primeiro?',
                    'recomendacao': 'Configure sua renda mensal para uma análise mais precisa.',
                    'saldo': 0,
                    'percentual_gastos': 0,
                    'total_fixo': total_fixo,
                    'total_flexivel': total_flexivel,
                    'total_geral': total_geral
                }
            
            saldo = salario - total_geral
            percentual_gastos = (total_geral / salario) * 100 if salario > 0 else 0
            
            if total_geral == 0:
                nivel = 'inicial'
                mensagem = '🎯 Ótimo começo! Agora vamos registrar seus primeiros gastos.'
                recomendacao = 'Comece adicionando seus gastos fixos essenciais.'
                
            elif percentual_gastos <= 60:
                nivel = 'saudavel'
                mensagem = '✅ Excelente! Suas finanças estão equilibradas.'
                recomendacao = 'Mantenha esse controle e pense em investir o excedente.'
                
            elif percentual_gastos <= 85:
                nivel = 'atencao'
                mensagem = '⚠️ Fique atento! Seus gastos estão chegando no limite.'
                recomendacao = 'Revise gastos flexíveis e identifique economias possíveis.'
                
            else:
                nivel = 'critico'
                mensagem = '🚨 Atenção! Você está gastando mais do que ganha.'
                recomendacao = 'Priorize gastos essenciais e reveja seu orçamento urgentemente.'
                
            return {
                'nivel': nivel,
                'mensagem': mensagem,
                'recomendacao': recomendacao,
                'saldo': saldo,
                'percentual_gastos': percentual_gastos,
                'total_fixo': total_fixo,
                'total_flexivel': total_flexivel,
                'total_geral': total_geral
            }
            
        except Exception as e:
            logger.error(f"Erro na análise financeira: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict:
        """Retorna análise padrão para casos de erro"""
        return {
            'nivel': 'inicial',
            'mensagem': '💡 Vamos começar sua jornada financeira!',
            'recomendacao': 'Adicione seu salário e primeiros gastos para uma análise personalizada.',
            'saldo': 0,
            'percentual_gastos': 0,
            'total_fixo': 0,
            'total_flexivel': 0,
            'total_geral': 0
        }
    
    async def get_personalized_tip(self, user_id: int, context: str = "geral") -> str:
        """Retorna uma dica personalizada baseada no contexto"""
        try:
            analysis = self.analyze_financial_health(user_id)
            user_data = db.get_user_data(user_id)
            nickname = user_data['nickname'] if user_data else "Amigo"
            
            context_prompts = {
                'apos_salario': f"Dê uma dica prática para {nickname} administrar o salário de forma inteligente. Seja breve e motivador:",
                'apos_gasto': f"Ajude {nickname} a refletir sobre consumo consciente após registrar um gasto. Uma frase inspiradora:",
                'apos_analise': f"Com base na situação financeira de {nickname} ({analysis['nivel']}), dê um conselho específico e encorajador:",
                'incentivo': f"{nickname} está aprendendo sobre finanças. Dê uma mensagem motivacional curta:",
                'economia': f"Dica prática de economia para {nickname} implementar hoje mesmo:",
                'geral': f"Dê um conselho financeiro útil e prático para {nickname}. Seja breve:"
            }
            
            prompt = context_prompts.get(context, context_prompts['geral'])
            
            if context == 'apos_analise' and analysis['nivel'] != 'inicial':
                prompt += f" Situação: {analysis['mensagem']}"
                
            response = await self._call_deepseek_api(prompt, max_tokens=80)
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
            
            # Análise rápida sem detalhamento excessivo
            expenses = db.get_monthly_expenses(user_id)
            analysis = self.analyze_financial_health(user_id)
            
            total_fixo = analysis.get('total_fixo', 0)
            total_flexivel = analysis.get('total_flexivel', 0)
            total_geral = analysis.get('total_geral', 0)
            salario = user_data.get('salario_liquido', 0)
            saldo = salario - total_geral
            percentual_gastos = analysis.get('percentual_gastos', 0)
            
            # Prompt mais direto e objetivo
            prompt = f"""
            Dados financeiros RESUMIDOS:
            - Salário: R$ {salario:,.0f}
            - Gastos totais: R$ {total_geral:,.0f} ({percentual_gastos:.0f}% do salário)
            - Saldo: R$ {saldo:,.0f}
            - Saúde: {analysis['nivel']}
            
            Forneça 3-4 recomendações PRÁTICAS e DIRETAS. Seja objetivo e focando em ações imediatas.
            """
            
            response = await self._call_deepseek_api(prompt, max_tokens=150)
            return response or self._get_quick_fallback_recommendations()
            
        except Exception as e:
            logger.error(f"Erro otimizado nas recomendações: {e}")
            return self._get_quick_fallback_recommendations()

    async def get_detailed_analysis(self, user_id: int) -> str:
        """Faz análise detalhada otimizada"""
        logger.info(f"📊 Iniciando análise detalhada para usuário {user_id}")
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                logger.warning("❌ Usuário não encontrado para análise detalhada")
                return "📊 Complete seu cadastro para uma análise personalizada."
            
            # Análise local rápida primeiro
            expenses = db.get_monthly_expenses(user_id)
            analysis = self.analyze_financial_health(user_id)
            
            total_fixo = analysis.get('total_fixo', 0)
            total_flexivel = analysis.get('total_flexivel', 0)
            total_geral = analysis.get('total_geral', 0)
            salario = user_data.get('salario_liquido', 0)
            saldo = salario - total_geral
            percentual_gastos = analysis.get('percentual_gastos', 0)
            
            # Prompt mais conciso
            prompt = f"""
            Situação financeira RESUMIDA:
            - Renda: R$ {salario:,.0f}/mês
            - Gastos: R$ {total_geral:,.0f}/mês ({percentual_gastos:.0f}% da renda)
            - Fixos: R$ {total_fixo:,.0f}, Flexíveis: R$ {total_flexivel:,.0f}
            - Saldo: R$ {saldo:,.0f}
            - Saúde: {analysis['nivel']}
            
            Forneça uma análise CONCISA com: 1) Pontos fortes, 2) Pontos de atenção, 3) 2-3 ações prioritárias.
            Seja direto e prático.
            """
            
            response = await self._call_deepseek_api(prompt, max_tokens=200)
            return response or self._get_quick_analysis_fallback()
            
        except Exception as e:
            logger.error(f"Erro otimizado na análise: {e}")
            return self._get_quick_analysis_fallback()

    def _get_quick_fallback_recommendations(self) -> str:
        """Fallback rápido para recomendações"""
        logger.info("🔄 Usando fallback rápido para recomendações")
        recommendations = [
            "🎯 **RECOMENDAÇÕES PRÁTICAS:**\n\n1. Revise 3 gastos não essenciais esta semana\n2. Automatize poupança (10% do salário)\n3. Estabeleça uma meta financeira clara\n4. Acompanhe gastos diariamente por 7 dias",
            
            "💡 **AÇÕES IMEDIATAS:**\n\n• Corte uma assinatura não utilizada\n• Estabeleça limite para gastos flexíveis\n• Crie reserva para emergências\n• Negocie dívidas com juros altos",
            
            "🚀 **ESTRATÉGIAS RÁPIDAS:**\n\n1. Regra 50-30-20 para orçamento\n2. Revisão semanal de extratos\n3. Meta de economia mensal realista\n4. Planeamento de compras grandes"
        ]
        return random.choice(recommendations)

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
            
            # Prompt mais direto
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
        
        topics = {
            'orcamento': "Explique de forma simples como fazer um orçamento pessoal em uma frase prática:",
            'emergencia': "Dê uma dica rápida sobre como criar um fundo de emergência de forma acessível:",
            'dividas': "Um conselho motivacional para quem está organizando dívidas:",
            'investimentos': "Explique por que investir é importante de forma simples e inspiradora:",
            'habitos': "Compartilhe um hábito financeiro simples que traz grandes resultados:"
        }
        
        if topic and topic in topics:
            prompt = topics[topic]
        else:
            prompt = random.choice(list(topics.values()))
            
        response = await self._call_deepseek_api(prompt, max_tokens=80)
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

    async def close_session(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

# Instância global do coach
finance_coach = FinanceCoach()

# Funções de conveniência para uso direto
async def get_quick_tip():
    """Função de conveniência para dica rápida"""
    return finance_coach.get_quick_tip()

async def get_personalized_advice(user_id: int, context: str = "geral"):
    """Função de conveniência para conselho personalizado"""
    return await finance_coach.get_personalized_tip(user_id, context)

async def analyze_financial_situation(user_id: int):
    """Função de conveniência para análise financeira"""
    return finance_coach.analyze_financial_health(user_id)

async def get_learning_content(user_id: int, topic: str = None):
    """Função de conveniência para conteúdo educacional"""
    return await finance_coach.get_learning_moment(user_id, topic)