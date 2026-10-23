"""MATERIAIS DA PÁGINA "CONHECIMENTO E INOVAÇÃO".
Para publicar um material, acrescente uma linha na lista abaixo (e salve). Campos:
  titulo, cadeia (use um dos nomes da lista CADEIAS), tipo ("Cartilha", "Manual", "Boa prática", "Caso de sucesso", "Vídeo"),
  url (link do PDF ou vídeo), descricao (uma frase).
Exemplo:
  {"titulo": "Manejo de pastagem no semiárido", "cadeia": "Bovinocultura de leite", "tipo": "Cartilha",
   "url": "https://...", "descricao": "Passo a passo para a época seca."},
"""
CADEIAS = ["Bovinocultura de leite", "Ovinocaprinocultura de corte", "Apicultura", "Fruticultura perene", "Suinocultura", "Carcinicultura"]
TIPOS = ["Cartilha", "Manual", "Boa prática", "Caso de sucesso", "Vídeo"]

MATERIAIS = [
]

PERGUNTAS = [
    ("O que é a ATeG?", "A Assistência Técnica e Gerencial é um programa do Sistema CNA/SENAR, executado no Ceará pelo SENAR-CE e pela FAEC. Técnicos de campo acompanham a propriedade rural para melhorar a produção, a gestão e a renda do produtor."),
    ("Quanto custa participar?", "Nada. O serviço é gratuito para o produtor rural e é financiado pelo Sistema CNA/SENAR, em parceria com os sindicatos rurais."),
    ("Quanto tempo dura o acompanhamento?", "Em geral, 24 meses, podendo variar em algumas cadeias. As visitas são mensais e agendadas com antecedência."),
    ("Como são as visitas?", "O técnico visita a propriedade, faz o diagnóstico, planeja as melhorias com o produtor e acompanha a sua execução, medindo os resultados ao longo do tempo."),
    ("Em quais cadeias a ATeG atua?", "Bovinocultura de leite e de corte, ovinocaprinocultura, suinocultura, apicultura, fruticultura e carcinicultura, entre outras."),
    ("Como posso ser atendido?", "Procure o sindicato rural do seu município ou o SENAR-CE para saber se há vaga e técnico disponível na sua região."),
]
