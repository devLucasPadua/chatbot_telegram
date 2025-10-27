import requests
import json
import config
import database as db
from typing import Dict
import datetime
import time

class EduFinanceCoach:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self.cache = {}
        
    def get_flow_response(self, user_id: int, current_step: str, user_input: str = "", context: Dict = None) -> str:
        """Gera respostas para o fluxo específico usando DeepSeek"""
        try:
            # Cache simples para evitar chamadas repetidas
            cache_key = f"{user_id}_{current_step}_{user_input}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            user_data = db.get_user_data(user_id)
            user_context = {
                'name': user_data['nickname'] if user_data else '',
                'salary': user_data.get('salary', 0) if user_data else 0,
                'current_step': current_step,
                'user_input': user_input
            }
            
            if context:
                user_context.update(context)
            
            prompt = self._create_flow_prompt(current_step, user_context)
            response = self._call_deepseek_api(prompt)
            
            # Cache por 5 minutos
            self.cache[cache_key] = response
            return response
            
        except Exception as e:
            return self._get_fallback_response(current_step, user_context)
    
    def _create_flow_prompt(self, step: str, context: Dict) -> str:
        """Cria prompt específico para cada etapa do fluxo"""
        
        base_prompt = f"""
        Você é o Edu, assistente financeiro. Seja DIRETO e CONCISO.
        Máximo 2-3 frases por resposta.
        Evite repetições.
        
        Nome: {context.get('name', '')}
        Etapa: {step}
        """
        
        step_prompts = {
            "welcome": "Dê boas-vindas CURTAS como Edu.",
            "get_name": "Peça o nome. 1 frase.",
            "confirm_name": f"Confirme o nome {context.get('name', '')} e diga que vai ajudar com orçamento. 2 frases.",
            "get_salary": f"Peça salário líquido. Exemplo: 1000,00. 2 frases.",
            "expense_education": "Explique RAPIDAMENTE diferença entre gastos fixos e flexíveis. 3 frases máx.",
            "get_expense_type": "Pergunte: Fixo ou Flexível?",
            "get_fixed_subcategory": "Liste categorias fixas. Seja DIRETO.",
            "get_flexible_subcategory": "Liste categorias flexíveis. Seja DIRETO.",
            "get_new_subcategory": "Peça nome da nova categoria.",
            "get_expense_value": "Peça valor. Ex: 150,00",
            "get_expense_date": "Peça data. Opções: Hoje, Ontem, Outra.",
            "continue_adding": "Pergunte se quer continuar. SIM/NÃO",
            "show_summary": f"Mostre resumo {context.get('summary_data', '')}. Opções: 1-Analisar ou 2-Encerrar",
            "financial_health_intro": "Introduza análise saúde financeira. 2 frases.",
            "financial_health_analysis": f"Analise {context.get('analysis_data', '')}. Seja DIRETO."
        }
        
        return step_prompts.get(step, base_prompt)
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """Faz a chamada para a API do DeepSeek com timeout reduzido"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": "Você é o Edu, assistente financeiro. Seja MUITO DIRETO. Máximo 3 frases. Sem repetições."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 150,  # Reduzido para respostas mais curtas
            "stream": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)  # Timeout reduzido
            response.raise_for_status()
            
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            # Log de performance
            elapsed = time.time() - start_time
            print(f"⏱️  IA Response time: {elapsed:.2f}s")
            
            return result
            
        except requests.exceptions.Timeout:
            return "Vamos continuar..."
        except Exception as e:
            return "Próximo passo..."
    
    def _get_fallback_response(self, step: str, context: Dict) -> str:
        """Respostas fallback ULTRA RÁPIDAS"""
        name = context.get('name', '')
        
        fallbacks = {
            "welcome": "👋 Olá! Sou o Edu.",
            "get_name": "Nome?",
            "confirm_name": f"👋 {name}! Vou ajudar com seu orçamento.",
            "get_salary": f"💰 {name}, qual seu salário líquido? Ex: 1000,00",
            "expense_education": "💡 Gastos fixos: regulares (aluguel, internet). Flexíveis: variam (alimentação, lazer). Vamos classificar!",
            "get_expense_type": "📊 Fixo ou Flexível?",
            "get_fixed_subcategory": "🏠 Categorias Fixas:\n• Moradia\n• Serviços\n• Educação\n• Transporte\n• Seguros\n• Assinaturas\n• Impostos\n• NOVA",
            "get_flexible_subcategory": "🛍️ Categorias Flexíveis:\n• Alimentação\n• Lazer\n• Vestuário\n• Cuidados\n• Manutenção\n• Presentes\n• NOVA",
            "get_new_subcategory": "📝 Nome da nova categoria:",
            "get_expense_value": "💵 Valor:",
            "get_expense_date": "📅 Data: Hoje, Ontem ou Outra?",
            "continue_adding": "🔄 Continuar?",
            "show_summary": "📋 Resumo. 1-Analisar saúde ou 2-Encerrar?",
            "financial_health_intro": "📈 Analisando sua saúde financeira...",
            "financial_health_analysis": "💎 Análise concluída!"
        }
        return fallbacks.get(step, "Próximo...")

# Instância global do coach
edu_coach = EduFinanceCoach()