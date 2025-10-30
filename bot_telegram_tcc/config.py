BOT_TOKEN = "SEU_TOKEN"
DEEPSEEK_API_KEY = "SUA_KEY"

SALARIO_MINIMO = 1518.00

CATEGORIAS_FIXAS = {
    'Moradia': ['aluguel', 'financiamento imobiliário', 'condomínio'],
    'Serviços essenciais': ['água', 'luz', 'gás', 'internet', 'telefone'],
    'Educação': ['mensalidades escolares ou universitárias'],
    'Transporte': ['parcela de veículo', 'seguro', 'transporte público'],
    'Seguros': ['saúde', 'vida', 'carro', 'residencial'],
    'Assinaturas': ['streaming (Netflix, Spotify)', 'academia', 'revistas'],
    'Impostos': ['IPTU', 'IPVA'],
    'Outros...': []  # Alterado de 'Nova_fixo' para 'Outros...'
}

CATEGORIAS_FLEXIVEIS = {
    'Alimentação': ['supermercado', 'restaurantes', 'delivery'],
    'Lazer': ['cinema', 'viagens', 'passeios', 'eventos'],
    'Vestuário': ['roupas', 'sapatos', 'acessórios'],
    'Cuidados pessoais': ['salão de beleza', 'cosméticos', 'barbearia'],
    'Manutenção': ['pequenos reparos domésticos ou do carro'],
    'Presentes e doações': ['datas comemorativas', 'causas sociais'],
    'Outros...': []  # Alterado de 'Nova_flexivel' para 'Outros...'
}

EDUCATION_MODULES = {
    'basico': ['orçamento', 'emergencia', 'gastos_essenciais'],
    'intermediario': ['investimentos_basicos', 'metas', 'dividas'],
    'avancado': ['investimentos_avancados', 'patrimonio', 'aposentadoria']
}