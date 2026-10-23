"""LISTA DOS PAINÉIS DA PLATAFORMA. É aqui que você liga cada painel: basta colocar o endereço (url) quando ele estiver publicado.
Sem url, o cartão aparece como "Em breve". grupo: "visitas" ou "cadeias"."""
PAINEIS = [
    {"slug": "visitas", "grupo": "visitas", "titulo": "Acompanhamento das visitas",
     "desc": "Visitas, propriedades assistidas, técnicos, supervisores, municípios e orientações.",
     "url": "https://painel-visitas-ateg.vercel.app/", "img": "visitas.svg"},
    {"slug": "bovinocultura", "grupo": "cadeias", "titulo": "Bovinocultura de leite",
     "desc": "Receita, produção e margem bruta da cadeia do leite.", "url": "https://painel-cadeias-produtivas.vercel.app/", "img": "bovino_0.jpg"},
    {"slug": "ovinocaprinocultura", "grupo": "cadeias", "titulo": "Ovinocaprinocultura de corte",
     "desc": "Receita, produção e margem bruta da cadeia de ovinos e caprinos.",
     "url": "https://cadeia-produtiva-ovinocaprino-corte.vercel.app/", "img": "ovino_0.jpg"},
    {"slug": "apicultura", "grupo": "cadeias", "titulo": "Apicultura",
     "desc": "Receita, produção e margem bruta da cadeia do mel.",
     "url": "https://cadeia-produtiva-apicultura.vercel.app/", "img": "apicultura_0.jpg"},
    {"slug": "fruticultura", "grupo": "cadeias", "titulo": "Fruticultura perene",
     "desc": "Receita, produção e margem bruta da fruticultura.", "url": "https://cadeia-produtiva-fruticultura-peren.vercel.app/", "img": "fruta_0.jpg"},
    {"slug": "suinocultura", "grupo": "cadeias", "titulo": "Suinocultura",
     "desc": "Receita, produção e margem bruta da suinocultura.", "url": "https://cadeia-produtiva-suinocultura.vercel.app/", "img": "suino_0.jpg"},
    {"slug": "carcinicultura", "grupo": "cadeias", "titulo": "Carcinicultura",
     "desc": "Em preparação.", "url": "", "img": "carcinicultura_0.jpg"},
]

# Ícones das cadeias (faixa verde da página inicial)
ICONES = {'bovinocultura': '<path d="M4 8c0-2 1-3 2-3l1.5 2.5M20 8c0-2-1-3-2-3l-1.5 2.5M7.5 7.5h9c1.5 0 2.5 1 2.5 2.5v3a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-3c0-1.5 1-2.5 2.5-2.5z"/><circle cx="9.5" cy="11" r=".8"/><circle cx="14.5" cy="11" r=".8"/><path d="M9 15v2M15 15v2"/>', 'ovinocaprinocultura': '<path d="M6 9a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3 3 3 0 0 1 0 5H6a3 3 0 0 1 0-5z"/><path d="M8 14v5M16 14v5"/><circle cx="12" cy="10" r=".8"/>', 'apicultura': '<ellipse cx="12" cy="14" rx="4" ry="5"/><path d="M8.2 13h7.6M8.2 16h7.6M12 9V6M9 5l3 1 3-1"/><path d="M5 10c1-3 4-3 5-1M19 10c-1-3-4-3-5-1"/>', 'fruticultura': '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-14 14z"/><path d="M5 19c3-5 6-8 10-10"/>', 'suinocultura': '<path d="M5 10c0-3 3-5 7-5s7 2 7 5v3c0 3-3 5-7 5s-7-2-7-5z"/><ellipse cx="12" cy="13" rx="3" ry="2"/><circle cx="10.8" cy="13" r=".6"/><circle cx="13.2" cy="13" r=".6"/><path d="M6 7L4 4M18 7l2-3"/>', 'carcinicultura': '<path d="M18 7c-2-2-6-2-8 1-2 3-1 6 2 8 2 1 4 1 5 0M10 8C7 7 5 9 5 11M8 17l-2 3M12 18l-1 3"/><circle cx="16.5" cy="8" r=".7"/>'}
for _p in PAINEIS:
    _p["ico"] = ICONES.get(_p["slug"], "")
