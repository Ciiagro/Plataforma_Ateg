"""AGENDA E OPORTUNIDADES. Para publicar, acrescente itens em EVENTOS (e salve). Enquanto EVENTOS estiver vazia,
a página mostra EXEMPLOS marcados como "exemplo ilustrativo" para mostrar como ficará.
Campos de cada item: data ("AAAA-MM-DD"), titulo, tipo ("Curso", "Oficina", "Dia de campo", "Evento", "Oportunidade"),
local (cidade ou "Online"), descricao (uma frase) e url (link de inscrição ou de informações; pode ficar vazio).
Exemplo:
  {"data": "2026-11-20", "titulo": "Dia de campo de apicultura", "tipo": "Dia de campo", "local": "Quixeramobim",
   "descricao": "Manejo de colmeias na época seca.", "url": "https://..."},
"""
TIPOS = ["Curso", "Oficina", "Dia de campo", "Evento", "Oportunidade"]

EVENTOS = [
]

EXEMPLOS = [
    {"data": "2026-11-12", "titulo": "Curso de manejo de pastagem", "tipo": "Curso", "local": "Município do Ceará",
     "descricao": "Capacitação para produtores atendidos pela ATeG.", "url": ""},
    {"data": "2026-11-20", "titulo": "Dia de campo de apicultura", "tipo": "Dia de campo", "local": "Município do Ceará",
     "descricao": "Demonstração prática de manejo de colmeias.", "url": ""},
    {"data": "2026-12-03", "titulo": "Oficina de gestão da propriedade", "tipo": "Oficina", "local": "Online",
     "descricao": "Uso do caderno do produtor e controle de custos.", "url": ""},
    {"data": "2026-12-10", "titulo": "Vaga de estágio em extensão rural", "tipo": "Oportunidade", "local": "Fortaleza",
     "descricao": "Apoio às equipes técnicas da ATeG.", "url": ""},
]
