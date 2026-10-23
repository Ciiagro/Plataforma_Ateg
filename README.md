# Plataforma da ATeG (SENAR-CE / FAEC)

Portal que reúne os painéis da ATeG, seguindo a proposta de estrutura (menu: Início, Conheça a ATeG, Resultados e indicadores,
Conhecimento e inovação, Agenda e oportunidades, Área do colaborador, Gestão estratégica).

**Etapa 1 (esta versão):** estrutura institucional + painéis (visitas e cadeias produtivas) abertos dentro do portal.
As áreas "Conhecimento", "Agenda", "Colaborador" e "Gestão" mostram "em preparação"; as duas últimas serão restritas com login (etapa 2).

## Como ligar um painel
Abra `app/paineis.py` e preencha o `url` do painel (o endereço publicado na Vercel). Sem `url` o cartão aparece como "Em breve".

## Rodar no computador
```
pip install -r requirements.txt
uvicorn app.main:app --port 8020
```
Abra http://localhost:8020

## Publicar
Repositório no GitHub e projeto na Vercel (não precisa de variáveis de ambiente nesta etapa: o portal não acessa banco de dados).

## Privacidade
Só dados agregados. Nenhuma informação individual de produtor é exibida no portal.
