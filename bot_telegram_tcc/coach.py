import aiohttp
import asyncio
import json
import config
import database as db
from datetime import datetime, timedelta
import logging
import random
from typing import Dict, List

class FinanceCoach:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.user_profiles = {}
        self.session = None
        self._response_cache = {}  # Cache simples para respostas
        self._cache_timeout = 3600  # 1 hora em segundos

    async def ensure_session(self):
        """Garante que temos uma sessão HTTP aberta"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=8)  # Timeout reduzido para 8 segundos
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _call_deepseek_api_fast(self, prompt, max_tokens=150):
        """Versão otimizada da chamada da API"""
        # Verifica cache primeiro
        cache_key = hash(prompt + str(max_tokens))
        if cache_key in self._response_cache:
            cached_time, response = self._response_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                return response

        if not self.api_key or self.api_key == "SUA_KEY":
            return await self._get_fallback_fast(prompt)

        await self.ensure_session()

        # Payload mais leve e otimizado
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um coach financeiro BR. Seja CURTO, PRÁTICO e use EMOJIS. Máximo 2 frases."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": False  # Important: desabilita streaming para respostas mais rápidas
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data['choices'][0]['message']['content']
                    
                    # Salva no cache
                    self._response_cache[cache_key] = (datetime.now(), result)
                    return result
                else:
                    logging.warning(f"API retornou status {response.status}")
                    return await self._get_fallback_fast(prompt)
                    
        except asyncio.TimeoutError:
            logging.warning("Timeout na chamada da API")
            return await self._get_fallback_fast(prompt)
        except Exception as e:
            logging.error(f"Erro rápido na API: {e}")
            return await self._get_fallback_fast(prompt)

    async def _get_fallback_fast(self, prompt):
        """Fallback super rápido com respostas pré-geradas"""
        fallback_responses = {
            "micro": [
                "💡 Guarde R$ 5 por dia = R$ 150/mês! Pequenos hábitos, grandes resultados! 🚀",
                "🎯 Antes de comprar: 'Preciso ou quero?' A diferença é ENORME! 💪",
                "💰 10% do salário na reserva. Comece HOJE! Seu futuro eu agradece! 🛡️",
                "📱 1 delivery a menos por semana = R$ 200/mês economizados! 🍲",
                "💸 Reveja assinaturas que não usa. Economia FÁCIL! 📊",
                "🚀 Pequenas economias diárias → Grandes conquistas mensais! ✨"
            ],
            "salario": [
                "💰 **Momento Salário:** Separe 10% PRIMEIRO! 'Pay yourself first'! 🛡️",
                "🎯 **Ao receber:** Planeje o mês ANTES de gastar! Controle = Liberdade! 💪"
            ],
            "gasto": [
                "💸 **Gasto registrado:** Era necessário ou impulsivo? Reflita! 🤔",
                "📊 **Consumo consciente:** Cada compra é uma escolha. Escolha sabiamente! 🎯"
            ],
            "credito": [
                "🚀 **Dinheiro extra:** Use 70% para metas, 30% para celebrar! Equilíbrio! ⚖️",
                "💎 **Renda extra:** Invista no seu futuro! Juros compostos são mágicos! ✨"
            ]
        }

        # Seleciona categoria baseada no prompt
        if any(word in prompt.lower() for word in ['salário', 'salario', 'receber']):
            return random.choice(fallback_responses["salario"])
        elif any(word in prompt.lower() for word in ['gasto', 'gastar', 'comprar']):
            return random.choice(fallback_responses["gasto"]) 
        elif any(word in prompt.lower() for word in ['crédito', 'credito', 'extra']):
            return random.choice(fallback_responses["credito"])
        else:
            return random.choice(fallback_responses["micro"])

    def analyze_user_reality_fast(self, user_id):
        """Versão rápida da análise do usuário"""
        recent_transactions = self.get_recent_transactions(user_id, 7)  # Apenas 7 dias para ser mais rápido
        
        if not recent_transactions or len(recent_transactions) < 3:
            return self.get_default_profile_fast()
        
        # Cálculo rápido
        total_income = sum(t[1] for t in recent_transactions if t[0] == 'credit')
        
        # Análise simplificada
        if total_income <= config.SALARIO_MINIMO:
            reality_level = 'basica'
        elif total_income <= config.SALARIO_MINIMO * 3:
            reality_level = 'estavel'
        else:
            reality_level = 'conforto'
        
        return {
            'realidade': reality_level,
            'renda_mensal': total_income * 4.3,  # Estimativa rápida mensal
            'transacoes_recentes': len(recent_transactions)
        }

    async def get_personalized_education_fast(self, user_id, user_nickname):
        """Versão RÁPIDA do aprendizado personalizado"""
        reality = self.analyze_user_reality_fast(user_id)
        
        # Prompt mais curto e direto
        prompt = f"""
        Dê UM conselho financeiro PRÁTICO para {user_nickname}.
        Renda: R$ {reality['renda_mensal']:,.0f}/mês.
        Situação: {reality['realidade']}.
        
        Seja CURTO (máximo 100 palavras), PRÁTICO e use EMOJIS.
        Foco em UMA ação específica para HOJE.
        """
        
        return await self._call_deepseek_api_fast(prompt, max_tokens=200)

    async def get_micro_lesson_fast(self, user_id, context):
        """Versão RÁPIDA das micro-aulas"""
        context_prompts = {
            'apos_salario': "Dica RÁPIDA para administrar salário (1 frase, use emojis):",
            'apos_gasto': "Reflexão RÁPIDA sobre consumo (1 frase, use emojis):",
            'apos_credito': "Dica RÁPIDA para dinheiro extra (1 frase, use emojis):",
            'primeira_vez': "Motivação RÁPIDA para finanças (1 frase, use emojis):"
        }
        
        prompt = context_prompts.get(context, context_prompts['primeira_vez'])
        return await self._call_deepseek_api_fast(prompt, max_tokens=80)

    async def get_quick_tip_fast(self, user_id):
        """Versão RÁPIDA das dicas rápidas"""
        quick_prompts = [
            "Dica financeira EM UMA FRASE (use emojis):",
            "Conselho de dinheiro que cabe num tweet:",
            "Melhor dica financeira rápida:",
            "Frase motivacional sobre dinheiro (curta):"
        ]
        
        prompt = random.choice(quick_prompts)
        return await self._call_deepseek_api_fast(prompt, max_tokens=60)

    async def close_session(self):
        """Fecha a sessão HTTP"""
        if self.session:
            await self.session.close()
            self.session = None

    # Mantemos estas funções para compatibilidade, mas são síncronas
    def get_recent_transactions(self, user_id, days=7):
        """Obtém transações recentes (versão síncrona)"""
        conn = db.sqlite3.connect(db.DB_NAME)
        c = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            SELECT type, amount, description, date, timestamp 
            FROM transactions 
            WHERE user_id=? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (user_id, since_date))
        
        transactions = c.fetchall()
        conn.close()
        return transactions

    def get_default_profile_fast(self):
        """Perfil padrão rápido"""
        return {
            'realidade': 'basica',
            'renda_mensal': 0,
            'transacoes_recentes': 0
        }

# Instância global do coach
finance_coach = FinanceCoach()