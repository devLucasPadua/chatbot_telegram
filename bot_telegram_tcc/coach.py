# coach.py
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
        self._cache_timeout = 3600  # 1 hora

    async def ensure_session(self):
        """Garante que temos uma sessão HTTP aberta"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _call_deepseek_api(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """Faz chamada para a API do DeepSeek"""
        # Verificar se a API key está configurada
        if not self.api_key or self.api_key == "SUA_KEY_AQUI":
            logger.info("API key não configurada, usando fallback")
            return await self._get_fallback_response(prompt)

        await self.ensure_session()

        # Verificar cache primeiro
        cache_key = hash(prompt + str(max_tokens))
        if cache_key in self._response_cache:
            cached_time, response = self._response_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                return response

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": """Você é Edu, um coach financeiro brasileiro especializado em educação financeira para pessoas comuns.
                    
                    SEU ESTILO:
                    - Seja EMPÁTICO e MOTIVADOR
                    - Use linguagem SIMPLES e ACESSÍVEL
                    - Seja PRÁTICO com ações concretas
                    - Use EMOJIS moderadamente
                    - Máximo 2-3 frases por resposta
                    - Foque em HÁBITOS sustentáveis
                    
                    NÃO USE:
                    - Jargões financeiros complexos
                    - Recomendações genéricas
                    - Linguagem técnica
                    - Excesso de emojis"""
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data['choices'][0]['message']['content'].strip()
                    
                    # Salvar no cache
                    self._response_cache[cache_key] = (datetime.now(), result)
                    logger.info(f"Resposta da API obtida: {result[:50]}...")
                    return result
                else:
                    error_text = await response.text()
                    logger.warning(f"API retornou status {response.status}: {error_text}")
                    return await self._get_fallback_response(prompt)
                    
        except asyncio.TimeoutError:
            logger.warning("Timeout na chamada da API")
            return await self._get_fallback_response(prompt)
        except Exception as e:
            logger.error(f"Erro na API: {e}")
            return await self._get_fallback_response(prompt)

    async def _get_fallback_response(self, prompt: str) -> str:
        """Respostas fallback quando a API não está disponível"""
        
        # Análise do prompt para categorizar
        prompt_lower = prompt.lower()
        
        # Dicas para diferentes contextos
        salario_dicas = [
            "💰 **Momento Salário:** Que tal separar 10% assim que receber? 'Pagamento próprio primeiro' é o segredo! 🛡️",
            "🎯 **Organização:** Faça um orçamento simples: 50% necessidades, 30% desejos, 20% economias. Funciona! ✨",
            "💡 **Dica Rápida:** Antes de gastar o salário, planeje o mês. Pequeno hábito, grande diferença! 📊"
        ]
        
        gasto_dicas = [
            "🤔 **Reflexão:** Esse gasto era realmente necessário ou foi impulsivo? A pergunta que economiza! 💭",
            "🎯 **Consciência:** Cada compra é uma escolha. Escolhas conscientes = futuro tranquilo! 🌟",
            "💡 **Estratégia:** Antes de comprar, espere 24h. Muitos 'desejos' desaparecem! ⏳"
        ]
        
        economia_dicas = [
            "🚀 **Micro-economia:** Guardar R$ 5 por dia = R$ 150/mês! Pequenos hábitos, grandes resultados! 💪",
            "📱 **Economia Digital:** Reveja assinaturas que não usa. Pode ser uma surpresa agradável! 🔍",
            "🍲 **Alimentação:** Um delivery a menos por semana = R$ 200/mês economizados! Pequenas mudanças! 🌱"
        ]
        
        motivacao_dicas = [
            "🌟 **Lembrete:** Sua jornada financeira é única! Cada passo conta, celebre as pequenas vitórias! 🎉",
            "💎 **Perspective:** Educação financeira não é sobre restrição, é sobre liberdade de escolhas! 🕊️",
            "🌱 **Crescimento:** Organizar suas finanças é como plantar uma árvore: os melhores frutos vêm com tempo! 🌳"
        ]
        
        # Selecionar categoria baseada no prompt
        if any(word in prompt_lower for word in ['salário', 'salario', 'receber', 'renda']):
            return random.choice(salario_dicas)
        elif any(word in prompt_lower for word in ['gasto', 'gastar', 'comprar', 'compra']):
            return random.choice(gasto_dicas)
        elif any(word in prompt_lower for word in ['economia', 'economizar', 'poupar', 'guardar']):
            return random.choice(economia_dicas)
        elif any(word in prompt_lower for word in ['dica', 'conselho', 'motivação', 'motivacao']):
            return random.choice(motivacao_dicas)
        else:
            # Dicas gerais
            todas_dicas = salario_dicas + gasto_dicas + economia_dicas + motivacao_dicas
            return random.choice(todas_dicas)

    def analyze_financial_health(self, user_id: int) -> Dict:
        """Analisa a saúde financeira do usuário com base nos gastos"""
        try:
            user_data = db.get_user_data(user_id)
            if not user_data:
                return self._get_default_analysis()
            
            expenses = db.get_monthly_expenses(user_id)
            salario = user_data['salario_liquido'] or 0
            
            # Calcular totais
            total_fixo = sum(
                sum(subcat.values()) 
                for subcat in expenses['fixo'].values()
            )
            total_flexivel = sum(
                sum(subcat.values()) 
                for subcat in expenses['flexivel'].values()
            )
            total_geral = total_fixo + total_flexivel
            
            # Análise básica
            if salario <= 0:
                return {
                    'nivel': 'inicial',
                    'mensagem': '💡 Vamos começar organizando sua renda! Que tal definir seu salário primeiro?',
                    'recomendacao': 'Configure sua renda mensal para uma análise mais precisa.',
                    'saldo': 0,
                    'percentual_gastos': 0
                }
            
            saldo = salario - total_geral
            percentual_gastos = (total_geral / salario) * 100 if salario > 0 else 0
            
            # Determinar nível de saúde financeira
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
            
            # Prompts específicos por contexto
            context_prompts = {
                'apos_salario': f"Dê uma dica prática para {nickname} administrar o salário de forma inteligente. Seja breve e motivador:",
                'apos_gasto': f"Ajude {nickname} a refletir sobre consumo consciente após registrar um gasto. Uma frase inspiradora:",
                'apos_analise': f"Com base na situação financeira de {nickname} ({analysis['nivel']}), dê um conselho específico e encorajador:",
                'incentivo': f"{nickname} está aprendendo sobre finanças. Dê uma mensagem motivacional curta:",
                'economia': f"Dica prática de economia para {nickname} implementar hoje mesmo:",
                'geral': f"Dê um conselho financeiro útil e prático para {nickname}. Seja breve:"
            }
            
            prompt = context_prompts.get(context, context_prompts['geral'])
            
            # Adicionar contexto da análise se disponível
            if context == 'apos_analise' and analysis['nivel'] != 'inicial':
                prompt += f" Situação: {analysis['mensagem']}"
            
            # Tentar API primeiro, depois fallback
            response = await self._call_deepseek_api(prompt, max_tokens=100)
            return response
            
        except Exception as e:
            logger.error(f"Erro ao obter dica personalizada: {e}")
            return await self._get_fallback_response("dica motivacional")

    async def get_learning_moment(self, user_id: int, topic: str = None) -> str:
        """Fornece um momento de aprendizado sobre um tópico específico"""
        
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
            # Tópico aleatório
            prompt = random.choice(list(topics.values()))
        
        response = await self._call_deepseek_api(prompt, max_tokens=120)
        return response

    async def get_celebration_message(self, user_id: int, achievement: str) -> str:
        """Mensagem de celebração para conquistas"""
        
        celebrations = {
            'primeiro_gasto': "🎉 Parabéns pelo primeiro gasto registrado! Este é o primeiro passo para o controle financeiro!",
            'salario_definido': "💰 Ótimo! Com salário definido, você já tem o mapa para sua jornada financeira!",
            'resumo_visto': "📊 Excelente! Acompanhar seus gastos é a chave para mudanças reais!",
            'economia_feita': "🌟 Fantástico! Pequenas economias hoje constroem grandes conquistas amanhã!",
            'meta_atingida': "🎯 Incrível! Você está progredindo em direção aos seus objetivos!"
        }
        
        if achievement in celebrations:
            return celebrations[achievement]
        
        # Mensagem genérica de celebração
        user_data = db.get_user_data(user_id)
        nickname = user_data['nickname'] if user_data else "Amigo"
        
        prompt = f"Escreva uma mensagem curta e motivacional para {nickname} celebrando um marco na jornada financeira. Seja empático:"
        response = await self._call_deepseek_api(prompt, max_tokens=80)
        return response

    def get_quick_tip(self) -> str:
        """Dica rápida sem necessidade de API"""
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

    async def close_session(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    # Métodos de utilidade para estatísticas
    def get_user_insights(self, user_id: int) -> Dict:
        """Fornece insights sobre os padrões de gasto do usuário"""
        try:
            expenses = db.get_monthly_expenses(user_id)
            
            # Calcular categoria com maior gasto
            maior_categoria_fixo = None
            maior_valor_fixo = 0
            
            for categoria, subcategorias in expenses['fixo'].items():
                total_categoria = sum(subcat.values() for subcat in subcategorias.values())
                if total_categoria > maior_valor_fixo:
                    maior_valor_fixo = total_categoria
                    maior_categoria_fixo = categoria
            
            maior_categoria_flexivel = None
            maior_valor_flexivel = 0
            
            for categoria, subcategorias in expenses['flexivel'].items():
                total_categoria = sum(subcat.values() for subcat in subcategorias.values())
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

async def celebrate_achievement(user_id: int, achievement: str):
    """Função de conveniência para mensagens de celebração"""
    return await finance_coach.get_celebration_message(user_id, achievement)

async def close_coach_session():
    """Função de conveniência para fechar sessão"""
    await finance_coach.close_session()