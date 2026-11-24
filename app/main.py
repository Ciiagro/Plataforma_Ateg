"""Plataforma da ATeG (SENAR-CE / FAEC): portal que reúne os painéis. Etapa 1: estrutura institucional e painéis."""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.agenda import EVENTOS, EXEMPLOS, TIPOS as _TIPOS_AG
from app.conhecimento import CADEIAS as _CAD_CONH, MATERIAIS, PERGUNTAS, TIPOS
from app.noticias import NOTICIAS
from app.paineis import PAINEIS

load_dotenv()

BASE = Path(__file__).parent
app = FastAPI(title="Plataforma da ATeG")
app.mount("/img", StaticFiles(directory=str(BASE / "static")), name="img")
templates = Jinja2Templates(directory=str(BASE / "templates"))

# ---- Login da área restrita: mesmos usuários e senhas do sistema de avaliação dos técnicos (tabela usuarios_supervisores) ----
import hashlib
_seg = os.environ.get("SESSION_SECRET") or hashlib.sha256(("portal-ateg|" + os.environ.get("REMOTE_DB_PASS", "dev")).encode()).hexdigest()
app.add_middleware(SessionMiddleware, secret_key=_seg, session_cookie="portal_ateg", max_age=60 * 60 * 8, same_site="lax", https_only=bool(os.environ.get("VERCEL")))


def _logado(request: Request):
    return request.session.get("usuario")


def _exige_login(request: Request):
    """Para páginas: devolve um redirecionamento para a tela de entrada, ou None se já estiver logado."""
    if _logado(request):
        return None
    return RedirectResponse("/entrar?next=" + request.url.path, status_code=303)


def _next_seguro(n):
    return n if n and n.startswith("/") and not n.startswith("//") else "/colaborador"


MENU = [("/", "Início"), ("/conheca", "Conheça a ATeG"), ("/resultados", "Resultados e indicadores"),
        ("/conhecimento", "Conhecimento e inovação"), ("/agenda", "Agenda e oportunidades"),
        ("/colaborador", "Área do colaborador"), ("/gestao", "Gestão estratégica")]


def _pg(request: Request, nome: str, **ctx):
    return templates.TemplateResponse(request, nome, {"menu": MENU, "atual": request.url.path, "paineis": PAINEIS, "noticias": NOTICIAS, "usuario": request.session.get("usuario"), **ctx})


# ---- Números da página inicial (somente dados agregados, direto do banco do painel de visitas) ----
_engine = None
_cache = {"t": 0, "v": None}


def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL
        if os.environ.get("DB_URL"):
            url = os.environ["DB_URL"]
        else:
            url = URL.create("postgresql+psycopg2", username=os.environ.get("REMOTE_DB_USER", "postgres"), password=os.environ["REMOTE_DB_PASS"],
                             host=os.environ["REMOTE_DB_HOST"], port=int(os.environ.get("REMOTE_DB_PORT", "5432")), database=os.environ["REMOTE_DB_NAME"])
        _engine = create_engine(url, pool_pre_ping=True, pool_size=1, max_overflow=1, pool_recycle=300, connect_args={"connect_timeout": 8})
    return _engine


def _tab_historico(con):
    """Tabela com TODO o histórico (desde 2016): public.vw_visitas_anual. Se ela não existir, cai na mv_visitas/vw_visitas (só 2024 em diante)."""
    from sqlalchemy import text
    for t in ("public.vw_visitas_anual", "public.mv_visitas"):
        try:
            if con.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": t}).scalar():
                return t
        except Exception:
            pass
    return "public.vw_visitas"


@app.get("/api/indicadores")
def indicadores():
    """Totais da ATeG: propriedades assistidas, municípios, visitas e técnicos (ano atual e acumulado). Cache de 10 minutos."""
    if _cache["v"] and time.time() - _cache["t"] < 600:
        return _cache["v"]
    try:
        from sqlalchemy import text
        eng = _get_engine()
        with eng.connect() as con:
            tab = _tab_historico(con)
            ano = "dt_visita >= date_trunc('year', CURRENT_DATE)"
            r = con.execute(text(f"""SELECT
                COUNT(DISTINCT id_propriedade), COUNT(DISTINCT municipio), COUNT(DISTINCT id_visita), COUNT(DISTINCT tecnico), COUNT(DISTINCT id_visita) FILTER (WHERE valida),
                COUNT(DISTINCT id_propriedade) FILTER (WHERE {ano}), COUNT(DISTINCT municipio) FILTER (WHERE {ano}),
                COUNT(DISTINCT id_visita) FILTER (WHERE {ano}), COUNT(DISTINCT tecnico) FILTER (WHERE {ano}), COUNT(DISTINCT id_visita) FILTER (WHERE valida AND {ano}),
                MAX(dt_visita), MIN(dt_visita), EXTRACT(year FROM CURRENT_DATE)::int, COUNT(DISTINCT projeto)
                FROM {tab}""")).one()
            cad = [{"nome": n, "propriedades": int(q)} for n, q in con.execute(text(
                f"SELECT projeto, COUNT(DISTINCT id_propriedade) q FROM {tab} WHERE projeto IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 8")).all()]
    except Exception:
        raise HTTPException(503, "Indicadores indisponíveis")
    v = {"ano": r[12], "ate": r[10].isoformat() if r[10] else None, "desde": r[11].isoformat() if r[11] else None,
         "total": {"propriedades": r[0], "municipios": r[1], "visitas": r[2], "tecnicos": r[3], "validas": r[4], "cadeias": r[13]},
         "no_ano": {"propriedades": r[5], "municipios": r[6], "visitas": r[7], "tecnicos": r[8], "validas": r[9]},
         "cadeias": cad}
    _cache.update(t=time.time(), v=v)
    return v


_cache_mapa = {"t": 0, "v": None}
_cache_gestao = {"t": 0, "v": None}

# Área restrita (valores financeiros dos produtores, mesmo agregados): LIGADA só no seu computador. Na Vercel fica desligada
# até existir login por perfil. Para forçar: GESTAO_ATIVA=1/0.
_g = os.environ.get("GESTAO_ATIVA")
GESTAO_ATIVA = (_g.strip().lower() in ("1", "true", "sim")) if _g is not None else not os.environ.get("VERCEL")

_CADEIAS_TAB = [("Bovinocultura de leite", "resumo_leite_mensal"), ("Ovinocaprinocultura de corte", "resumo_ovino_mensal"),
                ("Fruticultura perene", "resumo_fruta_mensal"), ("Apicultura", "resumo_api_mensal"), ("Suinocultura", "resumo_suino_mensal")]


def _mes_add(ym, n):
    a, mth = int(ym[:4]), int(ym[5:7])
    t = a * 12 + (mth - 1) + n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


@app.get("/api/gestao")
def api_gestao(request: Request):
    """Visão macro das cadeias (receita bruta, despesa direta, margem bruta), últimos 12 meses fechados x 12 anteriores."""
    if not request.session.get("usuario"):
        raise HTTPException(401, "Faça login para ver esta área")
    if not GESTAO_ATIVA:
        raise HTTPException(403, "Área restrita")
    if _cache_gestao["v"] is not None and time.time() - _cache_gestao["t"] < 600:
        return _cache_gestao["v"]
    import datetime as _dt
    fim = _mes_add(_dt.date.today().strftime("%Y-%m"), -1)      # último mês fechado
    ini_a, ini_b, fim_b = _mes_add(fim, -11), _mes_add(fim, -23), _mes_add(fim, -12)
    try:
        from sqlalchemy import text
        with _get_engine().connect() as con:
            dados = {}
            for nome, tab in _CADEIAS_TAB:
                rows = con.execute(text(f"""SELECT mes, COALESCE(SUM(receita_bruta),0), COALESCE(SUM(despesa_direta),0), COUNT(DISTINCT id_propriedade)
                    FROM public.{tab} WHERE mes BETWEEN :i AND :f GROUP BY mes ORDER BY mes"""), {"i": ini_b, "f": fim}).all()
                dados[nome] = {r[0]: (float(r[1]), float(r[2]), int(r[3])) for r in rows}
            uni = " UNION ALL ".join(f"SELECT id_propriedade, mes FROM public.{t}" for _, t in _CADEIAS_TAB)
            props_a = con.execute(text(f"SELECT COUNT(DISTINCT id_propriedade) FROM ({uni}) x WHERE mes BETWEEN :i AND :f"), {"i": ini_a, "f": fim}).scalar()
            props_b = con.execute(text(f"SELECT COUNT(DISTINCT id_propriedade) FROM ({uni}) x WHERE mes BETWEEN :i AND :f"), {"i": ini_b, "f": fim_b}).scalar()
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").exception("api_gestao")
        raise HTTPException(503, "Dados indisponíveis: " + type(e).__name__ + " - " + str(e).splitlines()[0][:300])

    def soma(d, i, f):
        r = dp = 0.0
        for mes, (a, b, _) in d.items():
            if i <= mes <= f:
                r += a; dp += b
        return r, dp

    def pct(a, b):
        return None if not b or b <= 0 else (a - b) / b

    cad = []
    for nome, d in dados.items():
        ra, da = soma(d, ini_a, fim); rb, db = soma(d, ini_b, fim_b)
        pa = max([v[2] for k, v in d.items() if ini_a <= k <= fim] or [0])   # maior nº de propriedades com lançamento em um mês
        pb = max([v[2] for k, v in d.items() if ini_b <= k <= fim_b] or [0])
        cad.append({"nome": nome, "receita": ra, "despesa": da, "margem": ra - da, "receita_ant": rb, "despesa_ant": db, "margem_ant": rb - db,
                    "cresc_receita": pct(ra, rb), "cresc_margem": pct(ra - da, rb - db),
                    "props_mes": pa, "props_mes_ant": pb,
                    "receita_por_prop": (ra / pa / 12) if pa else None, "receita_por_prop_ant": (rb / pb / 12) if pb else None})
    tot = {k: sum(c[k] for c in cad) for k in ("receita", "despesa", "margem", "receita_ant", "despesa_ant", "margem_ant")}
    tot["cresc_receita"] = pct(tot["receita"], tot["receita_ant"]); tot["cresc_margem"] = pct(tot["margem"], tot["margem_ant"])
    tot["propriedades"], tot["propriedades_ant"] = int(props_a or 0), int(props_b or 0)
    meses = [_mes_add(fim, -i) for i in range(23, -1, -1)]
    serie = {"meses": meses,
             "receita": {n: [round(d.get(x, (0, 0, 0))[0], 2) for x in meses] for n, d in dados.items()},
             "margem": [round(sum(d.get(x, (0, 0, 0))[0] - d.get(x, (0, 0, 0))[1] for d in dados.values()), 2) for x in meses]}
    v = {"fim": fim, "periodo": {"a": [ini_a, fim], "b": [ini_b, fim_b]}, "total": tot, "cadeias": cad, "serie": serie}
    _cache_gestao.update(t=time.time(), v=v)
    return v


@app.get("/conhecimento", response_class=HTMLResponse)
def conhecimento(request: Request):
    return _pg(request, "conhecimento.html", materiais=MATERIAIS, perguntas=PERGUNTAS, cad_nomes=_CAD_CONH, tipos=TIPOS)


@app.get("/agenda", response_class=HTMLResponse)
def agenda(request: Request):
    import datetime as _dt
    meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    exemplo = not EVENTOS
    itens = []
    for e in sorted(EVENTOS or EXEMPLOS, key=lambda x: x["data"]):
        d = _dt.date.fromisoformat(e["data"])
        if not exemplo and d < _dt.date.today():
            continue
        itens.append({**e, "dia": f"{d.day:02d}", "mes": meses[d.month - 1], "ano": d.year})
    return _pg(request, "agenda.html", itens=itens, exemplo=exemplo, tipos=_TIPOS_AG)


@app.get("/entrar", response_class=HTMLResponse)
def entrar_tela(request: Request, next: str = "/colaborador"):
    if _logado(request):
        return RedirectResponse(_next_seguro(next), status_code=303)
    return _pg(request, "login.html", erro=None, next=_next_seguro(next))


@app.post("/entrar", response_class=HTMLResponse)
def entrar(request: Request, login: str = Form(...), senha: str = Form(...), next: str = Form("/colaborador")):
    import bcrypt
    from sqlalchemy import text
    login = (login or "").strip()
    erro = None
    try:
        with _get_engine().connect() as con:
            u = con.execute(text("SELECT supervisor, login, senha_hash, tipo FROM public.usuarios_supervisores WHERE login = :l"), {"l": login}).first()
        if u and bcrypt.checkpw(senha.encode("utf-8"), u[2].encode("utf-8")):
            request.session["usuario"] = u[0]
            request.session["login"] = u[1]
            request.session["tipo"] = u[3]
            return RedirectResponse(_next_seguro(next), status_code=303)
        time.sleep(0.8)
        erro = "Login ou senha inválidos."
    except Exception:
        import logging
        logging.getLogger("uvicorn.error").exception("entrar")
        erro = "Não foi possível verificar o acesso agora. Tente novamente em instantes."
    return _pg(request, "login.html", erro=erro, next=_next_seguro(next))


AVALIACAO_URL = os.environ.get("AVALIACAO_URL", "https://avaliacao-tecnicos-ateg.senarce.org.br").rstrip("/")


@app.get("/ir/avaliacao")
def ir_avaliacao(request: Request):
    """Abre o sistema de avaliação já logado: manda um link assinado (vale 2 min) com o login da pessoa."""
    import base64, hashlib, hmac, json as _json
    if not request.session.get("usuario"):
        return RedirectResponse("/entrar?next=/ir/avaliacao", status_code=303)
    login = request.session.get("login")
    segredo = os.environ.get("SSO_SECRET", "")
    if not login or not segredo:
        request.session.clear()
        return RedirectResponse("/entrar?next=/ir/avaliacao" if segredo else AVALIACAO_URL + "/login", status_code=303)
    corpo = base64.urlsafe_b64encode(_json.dumps({"l": login, "t": time.time()}).encode()).decode().rstrip("=")
    ass = hmac.new(segredo.encode(), corpo.encode(), hashlib.sha256).hexdigest()
    return RedirectResponse(f"{AVALIACAO_URL}/sso?t={corpo}.{ass}", status_code=303)


@app.get("/sair")
def sair(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/colaborador", response_class=HTMLResponse)
def colaborador(request: Request, ok: str = "", erro: str = ""):
    r = _exige_login(request)
    if r:
        return r
    return _pg(request, "colaborador.html", comunicados=_comunicados(), eh_coord=_eh_coord(request), ok=ok, erro=erro)


def _eh_coord(request: Request):
    return request.session.get("tipo") == "coordenador"


_MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _comunicados(so_mes=True):
    """Comunicados ativos (tabela public.portal_comunicados). so_mes=True: só os do mês atual (Área do colaborador);
    False: todos, do mais novo para o mais antigo (página /comunicados). Sem a tabela, devolve lista vazia."""
    try:
        from sqlalchemy import text
        filtro = "AND criado_em >= date_trunc('month', "+"(NOW() AT TIME ZONE 'America/Sao_Paulo')"+")" if so_mes else ""
        limite = 5 if so_mes else 500
        ordem = "destaque DESC, criado_em DESC, id DESC" if so_mes else "criado_em DESC, id DESC"
        base = "SELECT id, titulo, texto, criado_por, to_char(criado_em, 'DD/MM/YYYY \"às\" HH24:MI'), (criado_em > (NOW() AT TIME ZONE 'America/Sao_Paulo') - interval '3 days'), {d}, to_char(criado_em, 'YYYY-MM') FROM public.portal_comunicados WHERE ativo " + filtro + " ORDER BY {o} LIMIT " + str(limite)
        with _get_engine().connect() as con:
            try:
                rows = con.execute(text(base.format(d="destaque", o=ordem))).all()
            except Exception:
                con.rollback()
                rows = con.execute(text(base.format(d="FALSE", o="criado_em DESC, id DESC"))).all()
        out = []
        for r in rows:
            a, m = r[7].split("-")
            out.append({"id": r[0], "titulo": r[1], "texto": r[2], "por": r[3], "data": r[4], "novo": bool(r[5]), "destaque": bool(r[6]),
                        "mes": f"{_MESES[int(m) - 1].capitalize()} de {a}"})
        return out
    except Exception:
        return []


@app.get("/comunicados", response_class=HTMLResponse)
def comunicados_todos(request: Request, ok: str = "", erro: str = ""):
    r = _exige_login(request)
    if r:
        return r
    return _pg(request, "comunicados.html", comunicados=_comunicados(False), eh_coord=_eh_coord(request), ok=ok, erro=erro)


@app.post("/comunicados")
def comunicado_novo(request: Request, titulo: str = Form(""), texto: str = Form(""), destaque: str = Form("")):
    if not _logado(request):
        return RedirectResponse("/entrar?next=/colaborador", status_code=303)
    if not _eh_coord(request):
        return RedirectResponse("/comunicados?erro=Só a coordenação publica comunicados.", status_code=303)
    titulo, texto = (titulo or "").strip()[:150], (texto or "").strip()[:3000]
    if not titulo or not texto:
        return RedirectResponse("/comunicados?erro=Preencha o título e o texto.", status_code=303)
    try:
        from sqlalchemy import text
        with _get_engine().begin() as con:
            try:
                with con.begin_nested():
                    con.execute(text("INSERT INTO public.portal_comunicados (titulo, texto, criado_por, destaque, criado_em) VALUES (:t, :x, :p, :d, (NOW() AT TIME ZONE 'America/Sao_Paulo'))"),
                                {"t": titulo, "x": texto, "p": request.session.get("usuario") or "", "d": bool(destaque)})
            except Exception:   # coluna "destaque" ainda não criada: publica sem destaque
                con.execute(text("INSERT INTO public.portal_comunicados (titulo, texto, criado_por, criado_em) VALUES (:t, :x, :p, (NOW() AT TIME ZONE 'America/Sao_Paulo'))"),
                            {"t": titulo, "x": texto, "p": request.session.get("usuario") or ""})
    except Exception:
        import logging
        logging.getLogger("uvicorn.error").exception("comunicado_novo")
        return RedirectResponse("/comunicados?erro=Não foi possível publicar agora.", status_code=303)
    return RedirectResponse("/comunicados?ok=Comunicado publicado.", status_code=303)


@app.post("/comunicados/{cid}/remover")
def comunicado_remover(request: Request, cid: int):
    if not _logado(request) or not _eh_coord(request):
        return RedirectResponse("/comunicados", status_code=303)
    try:
        from sqlalchemy import text
        with _get_engine().begin() as con:
            con.execute(text("UPDATE public.portal_comunicados SET ativo = FALSE WHERE id = :i"), {"i": cid})
    except Exception:
        import logging
        logging.getLogger("uvicorn.error").exception("comunicado_remover")
    return RedirectResponse("/comunicados?ok=Comunicado removido.", status_code=303)


@app.get("/gestao", response_class=HTMLResponse)
def gestao(request: Request):
    r = _exige_login(request)
    if r:
        return r
    if GESTAO_ATIVA:
        return _pg(request, "gestao.html")
    titulo, sub, restrito, itens = _EM_BREVE["/gestao"]
    return _pg(request, "embreve.html", titulo=titulo, sub=sub, restrito=restrito, itens=itens)


def _norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").upper().strip()


_CAD_PADROES = {  # slug da cadeia -> trechos do campo "atividade" (sem diferenciar maiúsculas/acentos parciais)
    "bovinocultura": ["%bovinocultura de leite%"], "ovinocaprinocultura": ["%ovinocaprinocultura de corte%"], "apicultura": ["%apicult%", "%abelha%"],
    "fruticultura": ["%frut%"], "suinocultura": ["%suin%"], "carcinicultura": ["%carcin%", "%camar%"]}
_NOME_CAD = {"bovinocultura": "Bovinocultura de leite", "ovinocaprinocultura": "Ovinocaprinocultura de corte", "apicultura": "Apicultura",
             "fruticultura": "Fruticultura perene", "suinocultura": "Suinocultura", "carcinicultura": "Carcinicultura"}
_cache_cad = {"t": 0, "v": None}


def _contagem_cadeias(con, tab):
    from sqlalchemy import text
    cols = []
    params = {}
    for i, (slug, pads) in enumerate(_CAD_PADROES.items()):
        conds = []
        for j, p in enumerate(pads):
            params[f"p{i}_{j}"] = p
            conds.append(f"atividade ILIKE :p{i}_{j}")
        cols.append(f"COUNT(DISTINCT id_propriedade) FILTER (WHERE {' OR '.join(conds)})")
    todas = " OR ".join(f"atividade ILIKE :p{i}_{j}" for i, (s, pads) in enumerate(_CAD_PADROES.items()) for j in range(len(pads)))
    cols.append(f"COUNT(DISTINCT id_propriedade) FILTER (WHERE atividade IS NOT NULL AND NOT ({todas}))")
    r = con.execute(text(f"SELECT {', '.join(cols)} FROM {tab}"), params).one()
    res = {slug: int(r[k] or 0) for k, slug in enumerate(_CAD_PADROES)}
    res["_outras"] = int(r[len(_CAD_PADROES)] or 0)
    rows = con.execute(text(f"""SELECT atividade, COUNT(DISTINCT id_propriedade) q FROM {tab}
        WHERE atividade IS NOT NULL AND NOT ({todas}) GROUP BY 1 ORDER BY 2 DESC"""), params).all()
    res["_lista"] = [{"nome": str(n).capitalize() if str(n).isupper() else str(n), "n": int(q)} for n, q in rows]
    return res


@app.get("/api/cadeias")
def cadeias_contagem():
    """Propriedades atendidas por cadeia (acumulado, agregado). Cache de 10 minutos."""
    if _cache_cad["v"] is not None and time.time() - _cache_cad["t"] < 600:
        return _cache_cad["v"]
    try:
        from sqlalchemy import text
        with _get_engine().connect() as con:
            tab = _tab_historico(con)
            cc = _contagem_cadeias(con, tab)
            v = {"outras": cc.pop("_outras"), "lista": cc.pop("_lista"), "cadeias": cc}
    except Exception:
        raise HTTPException(503, "Contagem indisponível")
    _cache_cad.update(t=time.time(), v=v)
    return v


_cache_dest = {"t": 0, "v": None}


def _mil(n):
    return f"{int(n):,}".replace(",", ".")


@app.get("/api/destaques")
def destaques():
    """Frases de destaque da home. Só dados de atendimento agregados (nada de receita/margem, nada individual). Cache de 10 minutos."""
    if _cache_dest["v"] is not None and time.time() - _cache_dest["t"] < 600:
        return _cache_dest["v"]
    out = []
    try:
        from sqlalchemy import text
        with _get_engine().connect() as con:
            tab = _tab_historico(con)
            r = con.execute(text(f"""SELECT
                COUNT(DISTINCT id_visita) FILTER (WHERE dt_visita >= date_trunc('year', CURRENT_DATE) AND dt_visita <= CURRENT_DATE),
                COUNT(DISTINCT id_visita) FILTER (WHERE dt_visita >= date_trunc('year', CURRENT_DATE) - interval '1 year'
                                                   AND dt_visita <= CURRENT_DATE - interval '1 year'),
                EXTRACT(year FROM CURRENT_DATE)::int FROM {tab}""")).one()
            atual, ant, ano = int(r[0]), int(r[1]), r[2]
            if atual and ant and atual > ant:
                p = round((atual - ant) / ant * 100)
                if p >= 1:
                    out.append({"ic": "visitas", "t": f"Em {ano}, a ATeG já fez {_mil(atual)} visitas, {p}% a mais que no mesmo período de {ano - 1}."})
            try:
                mu = con.execute(text(f"""SELECT municipio, COUNT(DISTINCT id_visita) q FROM {tab}
                    WHERE municipio IS NOT NULL AND dt_visita >= date_trunc('year', CURRENT_DATE) GROUP BY 1 ORDER BY 2 DESC LIMIT 1""")).first()
                if mu:
                    out.append({"ic": "mun", "t": f"O município com mais visitas em {ano} é {str(mu[0]).title()}, com {_mil(mu[1])} visitas."})
            except Exception:
                pass
            try:
                np_ = con.execute(text(f"""SELECT COUNT(*) FROM (SELECT id_propriedade, MIN(dt_visita) m FROM {tab}
                    WHERE id_propriedade IS NOT NULL GROUP BY 1) s WHERE m >= date_trunc('year', CURRENT_DATE)""")).scalar()
                if np_:
                    out.append({"ic": "novas", "t": f"{_mil(np_)} propriedades começaram a ser atendidas em {ano}."})
                nm = con.execute(text(f"""SELECT COUNT(*) FROM (SELECT municipio, MIN(dt_visita) m FROM {tab}
                    WHERE municipio IS NOT NULL GROUP BY 1) s WHERE m >= date_trunc('year', CURRENT_DATE)""")).scalar()
                if nm:
                    out.append({"ic": "mun", "t": f"{_mil(nm)} {'município recebeu' if nm == 1 else 'municípios receberam'} a ATeG pela primeira vez em {ano}."})
            except Exception:
                con.rollback()
            try:
                cc = _contagem_cadeias(con, tab)
                top = max((k for k in cc if not k.startswith("_")), key=cc.get)
                if cc[top] > 0:
                    out.append({"ic": "cadeia", "t": f"A cadeia com mais propriedades atendidas é {_NOME_CAD[top]}, com {_mil(cc[top])} propriedades."})
            except Exception:
                con.rollback()
    except Exception:
        raise HTTPException(503, "Destaques indisponíveis")
    v = {"itens": out}
    _cache_dest.update(t=time.time(), v=v)
    return v


@app.get("/api/mapa")
def mapa_atendimento():
    """Municípios atendidos pela ATeG, com a quantidade de propriedades por município (agregado; nada individual)."""
    if _cache_mapa["v"] is not None and time.time() - _cache_mapa["t"] < 600:
        return _cache_mapa["v"]
    try:
        from sqlalchemy import text
        with _get_engine().connect() as con:
            tab = _tab_historico(con)
            rows = con.execute(text(f"SELECT municipio, COUNT(DISTINCT id_propriedade) FROM {tab} WHERE municipio IS NOT NULL GROUP BY 1")).all()
    except Exception:
        raise HTTPException(503, "Mapa indisponível")
    mun = {}
    for n, q in rows:
        k = _norm(n)
        mun[k] = mun.get(k, 0) + int(q)
    v = {"municipios": mun, "atendidos": len(mun)}
    _cache_mapa.update(t=time.time(), v=v)
    return v


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    hero = next((n for n in ("hero.jpg", "hero.jpeg", "hero.png", "hero.webp") if (BASE / "static" / n).exists()), "bovino_0.jpg")
    return _pg(request, "inicio.html", hero=hero)


@app.get("/noticias", response_class=HTMLResponse)
def noticias_pg(request: Request):
    return _pg(request, "noticias.html")


@app.get("/conheca", response_class=HTMLResponse)
def conheca(request: Request):
    return _pg(request, "conheca.html")


@app.get("/resultados", response_class=HTMLResponse)
def resultados(request: Request):
    return _pg(request, "resultados.html")


@app.get("/painel/{slug}", response_class=HTMLResponse)
def painel(request: Request, slug: str):
    p = next((x for x in PAINEIS if x["slug"] == slug), None)
    if not p or not p["url"]:
        raise HTTPException(404, "Painel não encontrado")
    return _pg(request, "painel.html", p=p, atual="/resultados")


_EM_BREVE = {
    "/conhecimento": ("Conhecimento e inovação", "Biblioteca técnica, tecnologias, projetos e casos de sucesso.", False,
                      ["Biblioteca técnica por cadeia produtiva", "Vitrine de inovação e resultados", "Conteúdo organizado por problema do produtor", "Espaço do produtor, do técnico e do estudante"]),
    "/agenda": ("Agenda e oportunidades", "Cursos, eventos, oficinas, dias de campo e capacitações.", False,
                ["Calendário institucional", "Cursos e oficinas", "Dias de campo", "Oportunidades de estágio e pesquisa"]),
    "/colaborador": ("Área do colaborador", "Documentos internos, equipes, calendário, procedimentos e pendências.", True,
                     ["Biblioteca de documentos e procedimentos", "Cadastro e organização das equipes", "Acompanhamento de pendências", "Desenvolvimento profissional"]),
    "/gestao": ("Gestão estratégica", "Painel restrito à FAEC e aos responsáveis autorizados.", True,
                ["Painel executivo de indicadores", "Cobertura territorial e metas", "Execução contratual e financeira", "Visão por cadeia produtiva e território"]),
}


def _rota_em_breve(caminho):
    titulo, sub, restrito, itens = _EM_BREVE[caminho]

    @app.get(caminho, response_class=HTMLResponse, name=caminho)
    def _f(request: Request):
        return _pg(request, "embreve.html", titulo=titulo, sub=sub, restrito=restrito, itens=itens)


for _c in _EM_BREVE:
    if _c not in ("/gestao", "/conhecimento", "/agenda", "/colaborador"):
        _rota_em_breve(_c)
