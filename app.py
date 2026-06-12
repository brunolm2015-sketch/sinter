import os
import fitz
from flask import Flask, render_template, request, redirect, session, send_file, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

UPLOAD_FOLDER = os.path.join("static", "uploads")
PDF_FOLDER = os.path.join("static", "formularios")
PDF_GERADOS = os.path.join("static", "pdfs_gerados")
PDF_PAGES = os.path.join("static", "pdf_pages")
ENDO_ANEXOS = os.path.join("static", "endocrinos_anexos")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(PDF_GERADOS, exist_ok=True)
os.makedirs(PDF_PAGES, exist_ok=True)
os.makedirs(ENDO_ANEXOS, exist_ok=True)


def usuario_logado():
    return "usuario_id" in session


def buscar_usuario_logado():
    # Cache por requisição: evita várias consultas ao Supabase na mesma página.
    # Antes, cada chamada de tem_permissao() consultava o usuário de novo,
    # deixando o menu lateral e as páginas muito lentas.
    if hasattr(g, "usuario_logado_cache"):
        return g.usuario_logado_cache

    if not usuario_logado():
        g.usuario_logado_cache = None
        return None

    resultado = (
        supabase.table("usuarios")
        .select("*, cargos(*)")
        .eq("id", session.get("usuario_id"))
        .limit(1)
        .execute()
    )

    if not resultado.data:
        g.usuario_logado_cache = None
        return None

    g.usuario_logado_cache = resultado.data[0]
    return g.usuario_logado_cache


def normalizar_texto(valor):
    valor = str(valor or "").strip().lower()
    trocas = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }

    for antigo, novo in trocas.items():
        valor = valor.replace(antigo, novo)

    return valor


def buscar_cargo_do_usuario(usuario):
    # Cache por requisição do cargo do usuário.
    if hasattr(g, "cargo_usuario_cache"):
        return g.cargo_usuario_cache

    if not usuario:
        g.cargo_usuario_cache = None
        return None

    cargo_relacionado = usuario.get("cargos")

    if isinstance(cargo_relacionado, dict) and cargo_relacionado:
        g.cargo_usuario_cache = cargo_relacionado
        return g.cargo_usuario_cache

    cargo_id = usuario.get("cargo_id")

    if cargo_id:
        resultado = (
            supabase.table("cargos")
            .select("*")
            .eq("id", cargo_id)
            .limit(1)
            .execute()
        )

        if resultado.data:
            g.cargo_usuario_cache = resultado.data[0]
            return g.cargo_usuario_cache

    nome_cargo_usuario = normalizar_texto(usuario.get("cargo"))

    if nome_cargo_usuario:
        cargos = supabase.table("cargos").select("*").execute()

        for cargo in cargos.data or []:
            if normalizar_texto(cargo.get("nome")) == nome_cargo_usuario:
                g.cargo_usuario_cache = cargo
                return g.cargo_usuario_cache

    g.cargo_usuario_cache = None
    return None


def permissoes_usuario():
    # Cache por requisição das permissões.
    if hasattr(g, "permissoes_usuario_cache"):
        return g.permissoes_usuario_cache

    usuario = buscar_usuario_logado()

    if not usuario:
        g.permissoes_usuario_cache = {}
        return g.permissoes_usuario_cache

    cargo = buscar_cargo_do_usuario(usuario)

    if cargo and isinstance(cargo.get("permissoes"), dict):
        g.permissoes_usuario_cache = cargo.get("permissoes") or {}
        return g.permissoes_usuario_cache

    g.permissoes_usuario_cache = {}
    return g.permissoes_usuario_cache


def usuario_master(usuario=None):
    if usuario is None:
        usuario = buscar_usuario_logado()

    if not usuario:
        return False

    if normalizar_texto(usuario.get("cargo")) == "master":
        return True

    cargo = buscar_cargo_do_usuario(usuario)

    if cargo and normalizar_texto(cargo.get("nome")) == "master":
        return True

    return False


PERMISSOES_ALIAS = {
    "ver_convenios": [
        "ver_convenios", "ver_convenio", "menu_convenios", "menu_convenio",
        "convenios", "convenio", "ver_cards", "convenios_ver_cards",
        "convenio_ver_cards", "cards_convenios", "cards_convenio"
    ],
    "criar_convenios": [
        "criar_convenios", "criar_convenio", "novo_convenio", "novo_convenios",
        "ver_botao_novo", "botao_novo", "convenios_novo", "convenio_novo"
    ],
    "editar_convenios": [
        "editar_convenios", "editar_convenio", "convenios_editar", "convenio_editar"
    ],
    "excluir_convenios": [
        "excluir_convenios", "excluir_convenio", "convenios_excluir", "convenio_excluir"
    ],

    "ver_reqs": [
        "ver_reqs", "ver_req", "menu_reqs", "reqs", "req", "reqs_ver", "req_ver",
        "ver_reqs_formularios", "menu_reqs_formularios"
    ],
    "criar_reqs": ["criar_reqs", "criar_req", "reqs_criar", "req_criar", "nova_req", "novo_req"],
    "editar_reqs": ["editar_reqs", "editar_req", "reqs_editar", "req_editar"],
    "excluir_reqs": ["excluir_reqs", "excluir_req", "reqs_excluir", "req_excluir"],

    "ver_formularios": [
        "ver_formularios", "ver_formulario", "formularios", "formulario",
        "formularios_ver", "formulario_ver", "ver_reqs_formularios", "menu_reqs_formularios"
    ],
    "criar_formularios": ["criar_formularios", "criar_formulario", "formularios_criar", "formulario_criar"],
    "configurar_formularios": ["configurar_formularios", "configurar_formulario", "formularios_configurar", "formulario_configurar"],
    "preencher_formularios": ["preencher_formularios", "preencher_formulario", "formularios_preencher", "formulario_preencher"],
    "excluir_formularios": ["excluir_formularios", "excluir_formulario", "formularios_excluir", "formulario_excluir"],

    "ver_endocrinos": ["ver_endocrinos", "ver_endocrino", "menu_endocrinos", "endocrinos", "endocrino"],
    "ver_agendamentos": ["ver_agendamentos", "ver_agendamento", "endocrinos_ver_agendamentos", "agendamentos_ver"],
    "criar_agendamentos": ["novo_agendamento", "criar_agendamento", "criar_agendamentos", "endocrinos_novo_agendamento"],
    "editar_agendamentos": ["editar_agendamento", "editar_agendamentos", "endocrinos_editar_agendamento"],
    "excluir_agendamentos": ["excluir_agendamento", "excluir_agendamentos", "endocrinos_excluir_agendamento"],
    "gerenciar_exames": ["gerenciar_exames", "endocrinos_gerenciar_exames"],
    "gerenciar_status": ["gerenciar_status", "endocrinos_gerenciar_status"],

    "ver_usuarios_cargos": [
        "ver_usuarios_cargos", "menu_usuarios_cargos", "usuarios_cargos",
        "usuarios_e_cargos", "ver_usuarios_e_cargos"
    ],
    "ver_usuarios": ["ver_usuarios", "usuarios_ver", "usuarios"],
    "aprovar_usuarios": ["aprovar_usuarios", "usuarios_aprovar", "aprovar_usuario"],
    "editar_usuarios": ["editar_usuarios", "usuarios_editar", "editar_usuario"],
    "excluir_usuarios": ["excluir_usuarios", "usuarios_excluir", "excluir_usuario"],
    "ver_cargos": ["ver_cargos", "cargos_ver", "cargos"],
    "criar_cargos": ["criar_cargos", "cargos_criar", "criar_cargo"],
    "editar_cargos": ["editar_cargos", "cargos_editar", "editar_cargo"],
    "excluir_cargos": ["excluir_cargos", "cargos_excluir", "excluir_cargo"],
}


def permissao_ativa(permissoes, chave):
    if not isinstance(permissoes, dict):
        return False

    aliases = set(PERMISSOES_ALIAS.get(chave, []))
    aliases.add(chave)

    aliases_normalizados = {normalizar_texto(a).replace(" ", "_").replace("-", "_") for a in aliases}

    for nome, valor in permissoes.items():
        if valor in (False, None, "", "false", "False", "0", 0):
            continue

        nome_normalizado = normalizar_texto(nome).replace(" ", "_").replace("-", "_")

        if nome_normalizado in aliases_normalizados:
            return True

    return False


def tem_permissao(*chaves):
    usuario = buscar_usuario_logado()

    if not usuario:
        return False

    if usuario_master(usuario):
        return True

    permissoes = permissoes_usuario()

    for chave in chaves:
        if permissao_ativa(permissoes, chave):
            return True

    return False


def primeira_pagina_permitida():
    opcoes = [
        ("/convenios", ("ver_convenios",)),
        ("/reqs", ("ver_reqs",)),
        ("/formularios", ("ver_formularios",)),
        ("/endocrinos", ("ver_endocrinos", "ver_agendamentos")),
        ("/usuarios-cargos", ("ver_usuarios_cargos", "ver_usuarios", "ver_cargos")),
    ]

    for url, permissoes in opcoes:
        if tem_permissao(*permissoes):
            return url

    return "/sem-permissao"


def bloquear_sem_permissao(*chaves):
    if not usuario_logado():
        return redirect("/login")

    if not tem_permissao(*chaves):
        return redirect(primeira_pagina_permitida())

    return None


@app.before_request
def proteger_rotas_por_permissao():
    rota = request.path

    rotas_livres = (
        "/static",
        "/login",
        "/cadastro",
        "/logout",
        "/sem-permissao",
    )

    if rota == "/":
        return None

    if rota.startswith(rotas_livres):
        return None

    if not usuario_logado():
        return redirect("/login")

    regras = [
        ("/convenios/novo", ("criar_convenios", "criar_convenio")),
        ("/convenios/editar", ("editar_convenios", "editar_convenio")),
        ("/convenios/excluir", ("excluir_convenios", "excluir_convenio")),
        ("/convenios", ("ver_convenios",)),

        ("/reqs/nova", ("criar_reqs", "criar_req")),
        ("/reqs/editar", ("editar_reqs", "editar_req")),
        ("/reqs/excluir", ("excluir_reqs", "excluir_req")),
        ("/reqs", ("ver_reqs",)),

        ("/formularios/novo", ("criar_formularios", "criar_formulario")),
        ("/formularios/configurar", ("configurar_formularios", "configurar_formulario")),
        ("/formularios/perguntas", ("configurar_formularios", "configurar_formulario")),
        ("/formularios/preencher", ("preencher_formularios", "preencher_formulario")),
        ("/formularios/gerar-pdf", ("preencher_formularios", "preencher_formulario")),
        ("/formularios/excluir", ("excluir_formularios", "excluir_formulario")),
        ("/formularios", ("ver_formularios",)),


        ("/endocrinos/exame", ("gerenciar_exames",)),
        ("/endocrinos/status", ("gerenciar_status",)),
        ("/endocrinos/agendamento/novo", ("criar_agendamentos", "novo_agendamento", "criar_agendamento")),
        ("/endocrinos/agendamento/editar", ("editar_agendamentos", "editar_agendamento")),
        ("/endocrinos/agendamento/excluir", ("excluir_agendamentos", "excluir_agendamento")),
        ("/endocrinos", ("ver_endocrinos", "ver_agendamentos")),

        ("/usuarios/aprovar", ("aprovar_usuarios",)),
        ("/usuarios/negar", ("aprovar_usuarios",)),
        ("/usuarios/editar", ("editar_usuarios",)),
        ("/usuarios/excluir", ("excluir_usuarios",)),
        ("/usuarios", ("ver_usuarios", "ver_usuarios_cargos")),

        ("/cargos/novo", ("criar_cargos",)),
        ("/cargos/editar", ("editar_cargos",)),
        ("/cargos/excluir", ("excluir_cargos",)),
        ("/cargos", ("ver_cargos", "ver_usuarios_cargos")),

        ("/usuarios-cargos", ("ver_usuarios_cargos", "ver_usuarios", "ver_cargos")),
    ]

    for caminho, permissoes in regras:
        if rota.startswith(caminho):
            if not tem_permissao(*permissoes):
                return redirect(primeira_pagina_permitida())
            return None

    return None


@app.context_processor
def inserir_permissoes_nos_templates():
    return {
        "tem_permissao": tem_permissao,
        "permissoes": permissoes_usuario(),
        "usuario_master": usuario_master(),
    }


def salvar_imagem(imagem):
    if imagem and imagem.filename:
        filename = secure_filename(imagem.filename)
        caminho = os.path.join(UPLOAD_FOLDER, filename)
        imagem.save(caminho)
        return "/" + caminho.replace("\\", "/")
    return None


def salvar_pdf(arquivo):
    if arquivo and arquivo.filename:
        filename = secure_filename(arquivo.filename)
        caminho = os.path.join(PDF_FOLDER, filename)
        arquivo.save(caminho)
        return "/" + caminho.replace("\\", "/")
    return None


def salvar_anexos_endocrino(arquivos, nomes_anexos, agendamento_id):
    for index, arquivo in enumerate(arquivos):
        if arquivo and arquivo.filename:
            filename = secure_filename(arquivo.filename)
            caminho = os.path.join(ENDO_ANEXOS, f"{agendamento_id}_{filename}")
            arquivo.save(caminho)

            nome_personalizado = ""

            if index < len(nomes_anexos):
                nome_personalizado = nomes_anexos[index].strip()

            supabase.table("endocrino_anexos").insert({
                "agendamento_id": agendamento_id,
                "arquivo": "/" + caminho.replace("\\", "/"),
                "nome_arquivo": nome_personalizado if nome_personalizado else filename
            }).execute()


def caminho_local(caminho_web):
    return caminho_web.replace("/", "", 1)


def dados_pdf(formulario_id, arquivo_pdf, pagina_numero=0):
    caminho_pdf = caminho_local(arquivo_pdf)
    doc = fitz.open(caminho_pdf)

    total_paginas = len(doc)

    if pagina_numero < 0:
        pagina_numero = 0

    if pagina_numero >= total_paginas:
        pagina_numero = total_paginas - 1

    caminho_imagem = os.path.join(PDF_PAGES, f"{formulario_id}_pagina_{pagina_numero}.png")

    pagina = doc[pagina_numero]
    zoom = 2
    matriz = fitz.Matrix(zoom, zoom)
    pix = pagina.get_pixmap(matrix=matriz)
    pix.save(caminho_imagem)

    doc.close()

    return {
        "imagem": "/" + caminho_imagem.replace("\\", "/"),
        "zoom": zoom,
        "pagina_atual": pagina_numero,
        "total_paginas": total_paginas
    }


def detectar_campos_pdf(arquivo_pdf, pagina_numero=0):
    """Detecta automaticamente áreas preenchíveis no PDF.

    Regras:
    - Linhas de sublinhado/pontilhado feitas com vários "_" viram campos de texto.
    - Marcações "( )" viram campos de caixa de seleção.

    As coordenadas retornadas já estão no sistema de coordenadas do PDF,
    o mesmo usado pelo PyMuPDF para escrever o PDF final.
    """
    campos = []

    try:
        caminho_pdf = caminho_local(arquivo_pdf)
        doc = fitz.open(caminho_pdf)

        if pagina_numero < 0:
            pagina_numero = 0

        if pagina_numero >= len(doc):
            pagina_numero = len(doc) - 1

        pagina = doc[pagina_numero]

        def adiciona_campo(tipo, x, y, largura, altura, label, fonte=9):
            if largura <= 0 or altura <= 0:
                return

            # Evita campos repetidos muito próximos.
            for c in campos:
                if (
                    abs(c["pos_x"] - x) < 3
                    and abs(c["pos_y"] - y) < 3
                    and abs(c["largura"] - largura) < 6
                ):
                    return

            campos.append({
                "id": f"campo_{len(campos) + 1}",
                "tipo": tipo,
                "tipo_sugerido": "caixa_selecao" if tipo == "checkbox" else "texto",
                "pos_x": round(float(x), 2),
                "pos_y": round(float(y), 2),
                "largura": round(float(largura), 2),
                "altura": round(float(altura), 2),
                "fonte": fonte,
                "label": label,
            })

        # 1) Detecta linhas feitas com underscores.
        underscores = list(pagina.search_for("_"))
        linhas = []

        for r in underscores:
            centro_y = (r.y0 + r.y1) / 2
            grupo = None

            for linha in linhas:
                if abs(linha["centro_y"] - centro_y) <= 3:
                    grupo = linha
                    break

            if grupo is None:
                grupo = {"centro_y": centro_y, "rects": []}
                linhas.append(grupo)

            grupo["rects"].append(r)

        for linha in linhas:
            rects = sorted(linha["rects"], key=lambda rr: rr.x0)
            if not rects:
                continue

            segmentos = []
            atual = fitz.Rect(rects[0])

            for r in rects[1:]:
                # Se os underscores estão próximos, fazem parte da mesma linha.
                if r.x0 - atual.x1 <= 12:
                    atual |= r
                else:
                    segmentos.append(atual)
                    atual = fitz.Rect(r)

            segmentos.append(atual)

            for seg in segmentos:
                largura = seg.width

                # Ignora riscos muito pequenos; normalmente são artefatos.
                if largura < 25:
                    continue

                # O texto deve ficar um pouco acima do risco.
                x = seg.x0
                y = max(0, seg.y0 - 9)
                altura = max(14, seg.height + 8)

                adiciona_campo(
                    "texto",
                    x,
                    y,
                    largura,
                    altura,
                    f"Linha detectada {len(campos) + 1}",
                    9,
                )

        # 2) Detecta caixas de seleção escritas como ( ).
        for r in pagina.search_for("( )"):
            adiciona_campo(
                "checkbox",
                r.x0 + 1,
                r.y0,
                max(10, r.width - 2),
                max(10, r.height),
                f"Caixa de seleção {len(campos) + 1}",
                10,
            )

        doc.close()

    except Exception:
        # Se a detecção falhar, a tela continua funcionando com seleção manual.
        return []

    campos.sort(key=lambda c: (c["pos_y"], c["pos_x"]))
    return campos


@app.route("/")
def index():
    return redirect(primeira_pagina_permitida() if usuario_logado() else "/login")


@app.route("/painel")
def painel():
    if not usuario_logado():
        return redirect("/login")

    return redirect(primeira_pagina_permitida())


@app.route("/sem-permissao")
def sem_permissao():
    return "Você não tem permissão para acessar nenhuma página do sistema. Peça para um administrador liberar seu cargo."


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome_completo = request.form.get("nome_completo")
        cpf = request.form.get("cpf")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        if senha != confirmar_senha:
            return redirect("/cadastro")

        usuario_existente = supabase.table("usuarios").select("id").eq("cpf", cpf).execute()

        if usuario_existente.data:
            return redirect("/cadastro")

        senha_hash = generate_password_hash(senha)

        supabase.table("usuarios").insert({
            "nome_completo": nome_completo,
            "cpf": cpf,
            "senha": senha_hash,
            "cargo": "usuario",
            "aprovado": False,
            "status_cadastro": "pendente"
        }).execute()

        return redirect("/login")

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf = request.form.get("cpf")
        senha = request.form.get("senha")

        resultado = supabase.table("usuarios").select("*").eq("cpf", cpf).execute()

        if not resultado.data:
            return redirect("/login")

        usuario = resultado.data[0]

        if not check_password_hash(usuario["senha"], senha):
            return redirect("/login")

        if not usuario.get("aprovado"):
            return "Seu cadastro está aguardando aprovação."

        session["usuario_id"] = usuario["id"]
        session["usuario_nome"] = usuario["nome_completo"]
        session["usuario_cpf"] = usuario["cpf"]
        session["usuario_cargo"] = usuario["cargo"]

        return redirect(primeira_pagina_permitida())

    return render_template("login.html")


@app.route("/convenios")
def convenios():
    if not usuario_logado():
        return redirect("/login")

    resultado = supabase.table("convenios").select("*").order("criado_em", desc=True).execute()

    return render_template(
        "convenios.html",
        convenios=resultado.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/convenios/novo", methods=["POST"])
def novo_convenio():
    if not usuario_logado():
        return redirect("/login")

    imagem_path = salvar_imagem(request.files.get("imagem"))

    dados = {
        "nome": request.form.get("nome"),
        "nome_ativo": "nome_ativo" in request.form,
        "login": request.form.get("login"),
        "login_ativo": "login_ativo" in request.form,
        "cpf": request.form.get("cpf"),
        "cpf_ativo": "cpf_ativo" in request.form,
        "cnpj": request.form.get("cnpj"),
        "cnpj_ativo": "cnpj_ativo" in request.form,
        "codigo": request.form.get("codigo"),
        "codigo_ativo": "codigo_ativo" in request.form,
        "senha": request.form.get("senha"),
        "senha_ativo": "senha_ativo" in request.form,
        "imagem": imagem_path,
        "imagem_ativo": "imagem_ativo" in request.form,
        "link_site": request.form.get("link_site"),
        "criado_por": session.get("usuario_id")
    }

    supabase.table("convenios").insert(dados).execute()
    return redirect("/convenios")


@app.route("/convenios/editar/<convenio_id>", methods=["POST"])
def editar_convenio(convenio_id):
    if not usuario_logado():
        return redirect("/login")

    imagem_atual = request.form.get("imagem_atual")
    nova_imagem = salvar_imagem(request.files.get("imagem"))
    imagem_path = nova_imagem if nova_imagem else imagem_atual

    dados = {
        "nome": request.form.get("nome"),
        "nome_ativo": "nome_ativo" in request.form,
        "login": request.form.get("login"),
        "login_ativo": "login_ativo" in request.form,
        "cpf": request.form.get("cpf"),
        "cpf_ativo": "cpf_ativo" in request.form,
        "cnpj": request.form.get("cnpj"),
        "cnpj_ativo": "cnpj_ativo" in request.form,
        "codigo": request.form.get("codigo"),
        "codigo_ativo": "codigo_ativo" in request.form,
        "senha": request.form.get("senha"),
        "senha_ativo": "senha_ativo" in request.form,
        "imagem": imagem_path,
        "imagem_ativo": "imagem_ativo" in request.form,
        "link_site": request.form.get("link_site")
    }

    supabase.table("convenios").update(dados).eq("id", convenio_id).execute()
    return redirect("/convenios")


@app.route("/convenios/excluir/<convenio_id>", methods=["POST"])
def excluir_convenio(convenio_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("convenios").delete().eq("id", convenio_id).execute()
    return redirect("/convenios")


@app.route("/reqs-formularios")
def reqs_formularios():
    if not usuario_logado():
        return redirect("/login")

    reqs = supabase.table("reqs").select("*").order("criado_em", desc=True).execute()
    formularios = supabase.table("formularios").select("*").order("criado_em", desc=True).execute()

    return render_template(
        "reqs_formularios.html",
        reqs=reqs.data,
        formularios=formularios.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/reqs")
def reqs():
    if not usuario_logado():
        return redirect("/login")

    resultado = (
        supabase.table("reqs")
        .select("*")
        .order("criado_em", desc=True)
        .execute()
    )

    return render_template(
        "reqs.html",
        reqs=resultado.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/formularios")
def formularios():
    if not usuario_logado():
        return redirect("/login")

    resultado = (
        supabase.table("formularios")
        .select("*")
        .order("criado_em", desc=True)
        .execute()
    )

    return render_template(
        "formularios.html",
        formularios=resultado.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/reqs/nova", methods=["POST"])
def nova_req():
    if not usuario_logado():
        return redirect("/login")

    supabase.table("reqs").insert({
        "nome": request.form.get("nome"),
        "link": request.form.get("link"),
        "criado_por": session.get("usuario_id")
    }).execute()

    return redirect("/reqs")


@app.route("/reqs/editar/<req_id>", methods=["POST"])
def editar_req(req_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("reqs").update({
        "nome": request.form.get("nome"),
        "link": request.form.get("link")
    }).eq("id", req_id).execute()

    return redirect("/reqs")


@app.route("/reqs/excluir/<req_id>", methods=["POST"])
def excluir_req(req_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("reqs").delete().eq("id", req_id).execute()
    return redirect("/reqs")


@app.route("/formularios/novo", methods=["POST"])
def novo_formulario():
    if not usuario_logado():
        return redirect("/login")

    nome = request.form.get("nome")
    arquivo_pdf = request.files.get("arquivo_pdf")

    if not nome or not arquivo_pdf:
        return redirect("/formularios")

    pdf_path = salvar_pdf(arquivo_pdf)

    resultado = supabase.table("formularios").insert({
        "nome": nome,
        "arquivo_pdf": pdf_path,
        "perguntas": {
            "status": "manual",
            "modo": "mapeamento_visual"
        }
    }).execute()

    formulario_id = resultado.data[0]["id"]

    return redirect(f"/formularios/configurar/{formulario_id}?pagina=0")


@app.route("/formularios/configurar/<formulario_id>")
def configurar_formulario(formulario_id):
    if not usuario_logado():
        return redirect("/login")

    pagina = int(request.args.get("pagina", 0))

    formulario_result = supabase.table("formularios").select("*").eq("id", formulario_id).execute()

    if not formulario_result.data:
        return redirect("/formularios")

    formulario = formulario_result.data[0]
    pdf = dados_pdf(formulario_id, formulario["arquivo_pdf"], pagina)
    campos_detectados = detectar_campos_pdf(formulario["arquivo_pdf"], pdf["pagina_atual"])

    perguntas_result = (
        supabase.table("formulario_perguntas")
        .select("*")
        .eq("formulario_id", formulario_id)
        .order("pagina")
        .order("ordem")
        .execute()
    )

    return render_template(
        "configurar_formulario.html",
        formulario=formulario,
        perguntas=perguntas_result.data,
        imagem_pdf=pdf["imagem"],
        zoom_pdf=pdf["zoom"],
        pagina_atual=pdf["pagina_atual"],
        total_paginas=pdf["total_paginas"],
        campos_detectados=campos_detectados,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/formularios/perguntas/nova/<formulario_id>", methods=["POST"])
def nova_pergunta_formulario(formulario_id):
    if not usuario_logado():
        return redirect("/login")

    pagina = request.form.get("pagina") or 0

    dados = {
        "formulario_id": formulario_id,
        "pergunta": request.form.get("pergunta"),
        "tipo": request.form.get("tipo") or "texto",
        "placeholder": "",
        "obrigatoria": False,
        "ordem": request.form.get("ordem") or 1,
        "pos_x": request.form.get("pos_x") or None,
        "pos_y": request.form.get("pos_y") or None,
        "largura": request.form.get("largura") or 160,
        "altura": request.form.get("altura") or 18,
        "fonte": request.form.get("fonte") or 9,
        "pagina": pagina,
        "acao_padrao": "proxima",
        "pergunta_destino_id": None,
        "acao_se_sim": "proxima",
        "pergunta_se_sim_id": None,
        "acao_se_nao": "proxima",
        "pergunta_se_nao_id": None,
        "acao_se_marcado": "proxima",
        "pergunta_se_marcado_id": None,
        "copiar_resposta": "copiar_resposta" in request.form,
        "copiar_de_pergunta_id": request.form.get("copiar_de_pergunta_id") or None
    }

    supabase.table("formulario_perguntas").insert(dados).execute()

    return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")


@app.route("/formularios/perguntas/editar/<pergunta_id>/<formulario_id>", methods=["POST"])
def editar_pergunta_formulario(pergunta_id, formulario_id):
    if not usuario_logado():
        return redirect("/login")

    pagina = request.form.get("pagina") or 0

    dados = {
        "pergunta": request.form.get("pergunta"),
        "tipo": request.form.get("tipo") or "texto",
        "ordem": request.form.get("ordem") or 1,
        "pos_x": request.form.get("pos_x") or None,
        "pos_y": request.form.get("pos_y") or None,
        "largura": request.form.get("largura") or 160,
        "altura": request.form.get("altura") or 18,
        "fonte": request.form.get("fonte") or 9,
        "pagina": pagina,
        "copiar_resposta": "copiar_resposta" in request.form,
        "copiar_de_pergunta_id": request.form.get("copiar_de_pergunta_id") or None
    }

    supabase.table("formulario_perguntas").update(dados).eq("id", pergunta_id).execute()

    return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")


@app.route("/formularios/perguntas/mover/<pergunta_id>/<formulario_id>/<direcao>", methods=["POST"])
def mover_pergunta_formulario(pergunta_id, formulario_id, direcao):
    if not usuario_logado():
        return redirect("/login")

    pagina = request.form.get("pagina") or 0

    atual_result = (
        supabase.table("formulario_perguntas")
        .select("*")
        .eq("id", pergunta_id)
        .limit(1)
        .execute()
    )

    if not atual_result.data:
        return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")

    atual = atual_result.data[0]
    ordem_atual = int(atual.get("ordem") or 1)

    if direcao == "cima":
        vizinho_result = (
            supabase.table("formulario_perguntas")
            .select("*")
            .eq("formulario_id", formulario_id)
            .lt("ordem", ordem_atual)
            .order("ordem", desc=True)
            .limit(1)
            .execute()
        )
    elif direcao == "baixo":
        vizinho_result = (
            supabase.table("formulario_perguntas")
            .select("*")
            .eq("formulario_id", formulario_id)
            .gt("ordem", ordem_atual)
            .order("ordem")
            .limit(1)
            .execute()
        )
    else:
        return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")

    if vizinho_result.data:
        vizinho = vizinho_result.data[0]
        ordem_vizinho = int(vizinho.get("ordem") or 1)

        supabase.table("formulario_perguntas").update({"ordem": ordem_vizinho}).eq("id", pergunta_id).execute()
        supabase.table("formulario_perguntas").update({"ordem": ordem_atual}).eq("id", vizinho["id"]).execute()

    return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")


@app.route("/formularios/perguntas/excluir/<pergunta_id>/<formulario_id>", methods=["POST"])
def excluir_pergunta_formulario(pergunta_id, formulario_id):
    if not usuario_logado():
        return redirect("/login")

    pagina = request.form.get("pagina") or 0

    supabase.table("formulario_perguntas").delete().eq("id", pergunta_id).execute()

    return redirect(f"/formularios/configurar/{formulario_id}?pagina={pagina}")


@app.route("/formularios/preencher/<formulario_id>")
def preencher_formulario(formulario_id):
    if not usuario_logado():
        return redirect("/login")

    formulario_result = supabase.table("formularios").select("*").eq("id", formulario_id).execute()

    if not formulario_result.data:
        return redirect("/formularios")

    perguntas_result = (
        supabase.table("formulario_perguntas")
        .select("*")
        .eq("formulario_id", formulario_id)
        .order("pagina")
        .order("ordem")
        .execute()
    )

    return render_template(
        "preencher_formulario.html",
        formulario=formulario_result.data[0],
        perguntas=perguntas_result.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/formularios/gerar-pdf/<formulario_id>", methods=["POST"])
def gerar_pdf_preenchido(formulario_id):
    if not usuario_logado():
        return redirect("/login")

    formulario_result = supabase.table("formularios").select("*").eq("id", formulario_id).execute()

    if not formulario_result.data:
        return redirect("/formularios")

    formulario = formulario_result.data[0]

    perguntas_result = (
        supabase.table("formulario_perguntas")
        .select("*")
        .eq("formulario_id", formulario_id)
        .order("pagina")
        .order("ordem")
        .execute()
    )

    perguntas = perguntas_result.data or []
    respostas = {}

    # Primeiro coleta tudo que foi digitado manualmente no formulário.
    for pergunta in perguntas:
        respostas[pergunta["id"]] = request.form.get(pergunta["id"], "")

    # Depois aplica cópia automática somente quando o usuário escolher
    # realmente usar a resposta automática.
    # No HTML, cada pergunta automática envia:
    # modo_resposta_<id> = automatico ou manual
    for pergunta in perguntas:
        pergunta_id = pergunta["id"]
        origem_id = pergunta.get("copiar_de_pergunta_id")
        usa_copia = pergunta.get("copiar_resposta") and origem_id

        if usa_copia:
            modo_resposta = request.form.get(f"modo_resposta_{pergunta_id}", "automatico")

            if modo_resposta == "automatico":
                respostas[pergunta_id] = respostas.get(origem_id, "")
            else:
                respostas[pergunta_id] = request.form.get(pergunta_id, "")

    caminho_pdf = caminho_local(formulario["arquivo_pdf"])
    doc = fitz.open(caminho_pdf)

    def numero(valor, padrao):
        try:
            if valor in (None, ""):
                return float(padrao)
            return float(valor)
        except Exception:
            return float(padrao)

    tipos_checkbox = {"checkbox", "caixa_selecao", "caixa de seleção", "caixa_de_selecao"}

    for pergunta in perguntas:
        resposta = respostas.get(pergunta["id"], "")

        if not resposta:
            continue

        pagina_index = int(pergunta.get("pagina") or 0)

        if pagina_index < 0 or pagina_index >= len(doc):
            continue

        pagina = doc[pagina_index]

        x = numero(pergunta.get("pos_x"), 50)
        y = numero(pergunta.get("pos_y"), 50)
        largura = numero(pergunta.get("largura"), 160)
        altura = numero(pergunta.get("altura"), 18)
        fonte = numero(pergunta.get("fonte"), 9)

        if largura < 8:
            largura = 8

        if altura < 8:
            altura = 8

        tipo = str(pergunta.get("tipo") or "texto").strip().lower()

        if tipo in tipos_checkbox:
            # Para caixa de seleção, o X fica centralizado dentro da área selecionada.
            x_marca = x + (largura / 2) - (fonte / 3)
            y_marca = y + (altura / 2) + (fonte / 3)
            pagina.insert_text(
                (x_marca, y_marca),
                "X",
                fontsize=fonte,
                fontname="helv",
                color=(0, 0, 0)
            )
        else:
            texto = str(resposta or "")
            caixa = fitz.Rect(x, y, x + largura, y + altura)
            pagina.insert_textbox(
                caixa,
                texto,
                fontsize=fonte,
                fontname="helv",
                color=(0, 0, 0),
                align=0
            )

    nome_saida = f"formulario_preenchido_{formulario_id}.pdf"
    caminho_saida = os.path.join(PDF_GERADOS, nome_saida)

    doc.save(caminho_saida)
    doc.close()

    return send_file(caminho_saida, as_attachment=True)


@app.route("/formularios/excluir/<formulario_id>", methods=["POST"])
def excluir_formulario(formulario_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("formularios").delete().eq("id", formulario_id).execute()
    return redirect("/formularios")


@app.route("/endocrinos")
def endocrinos():
    if not usuario_logado():
        return redirect("/login")

    exames = supabase.table("endocrino_exames").select("*").order("exame").execute()
    status = supabase.table("endocrino_status").select("*").order("nome").execute()

    agendamentos = (
        supabase.table("endocrino_agendamentos")
        .select("*, endocrino_exames(*), endocrino_status(*)")
        .order("data_agendamento")
        .order("horario")
        .execute()
    )

    anexos = supabase.table("endocrino_anexos").select("*").execute()

    anexos_por_agendamento = {}

    for anexo in anexos.data:
        agendamento_id = anexo.get("agendamento_id")

        if agendamento_id not in anexos_por_agendamento:
            anexos_por_agendamento[agendamento_id] = []

        anexos_por_agendamento[agendamento_id].append(anexo)

    return render_template(
        "endocrinos.html",
        exames=exames.data,
        status=status.data,
        agendamentos=agendamentos.data,
        anexos_por_agendamento=anexos_por_agendamento,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/endocrinos/exame/novo", methods=["POST"])
def endocrino_exame_novo():
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_exames").insert({
        "exame": request.form.get("exame"),
        "sigla": request.form.get("sigla"),
        "tempo_medio": request.form.get("tempo_medio"),
        "observacao": request.form.get("observacao")
    }).execute()

    return redirect("/endocrinos")


@app.route("/endocrinos/exame/editar/<exame_id>", methods=["POST"])
def endocrino_exame_editar(exame_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_exames").update({
        "exame": request.form.get("exame"),
        "sigla": request.form.get("sigla"),
        "tempo_medio": request.form.get("tempo_medio"),
        "observacao": request.form.get("observacao")
    }).eq("id", exame_id).execute()

    return redirect("/endocrinos")


@app.route("/endocrinos/exame/excluir/<exame_id>", methods=["POST"])
def endocrino_exame_excluir(exame_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_exames").delete().eq("id", exame_id).execute()
    return redirect("/endocrinos")


@app.route("/endocrinos/status/novo", methods=["POST"])
def endocrino_status_novo():
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_status").insert({
        "nome": request.form.get("nome"),
        "cor": request.form.get("cor"),
        "descricao_padrao": request.form.get("descricao_padrao")
    }).execute()

    return redirect("/endocrinos")


@app.route("/endocrinos/status/editar/<status_id>", methods=["POST"])
def endocrino_status_editar(status_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_status").update({
        "nome": request.form.get("nome"),
        "cor": request.form.get("cor"),
        "descricao_padrao": request.form.get("descricao_padrao")
    }).eq("id", status_id).execute()

    return redirect("/endocrinos")


@app.route("/endocrinos/status/excluir/<status_id>", methods=["POST"])
def endocrino_status_excluir(status_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_status").delete().eq("id", status_id).execute()
    return redirect("/endocrinos")


@app.route("/endocrinos/agendamento/novo", methods=["POST"])
def endocrino_agendamento_novo():
    if not usuario_logado():
        return redirect("/login")

    status_novo = supabase.table("endocrino_status").select("*").ilike("nome", "Novo").limit(1).execute()

    status_id = request.form.get("status_id")
    status_descricao = request.form.get("status_descricao")

    if not status_id and status_novo.data:
        status_id = status_novo.data[0]["id"]
        status_descricao = status_novo.data[0].get("descricao_padrao") or "Novo agendamento"

    resultado = supabase.table("endocrino_agendamentos").insert({
        "cip": request.form.get("cip"),
        "nome": request.form.get("nome"),
        "cpf": request.form.get("cpf"),
        "data_nascimento": request.form.get("data_nascimento") or None,
        "exame_id": request.form.get("exame_id") or None,
        "data_agendamento": request.form.get("data_agendamento") or None,
        "horario": request.form.get("horario"),
        "status_id": status_id or None,
        "status_descricao": status_descricao,
        "criado_por": session.get("usuario_id")
    }).execute()

    agendamento_id = resultado.data[0]["id"]

    salvar_anexos_endocrino(
        request.files.getlist("anexos"),
        request.form.getlist("nomes_anexos"),
        agendamento_id
    )

    return redirect("/endocrinos")


@app.route("/endocrinos/agendamento/editar/<agendamento_id>", methods=["POST"])
def endocrino_agendamento_editar(agendamento_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_agendamentos").update({
        "cip": request.form.get("cip"),
        "nome": request.form.get("nome"),
        "cpf": request.form.get("cpf"),
        "data_nascimento": request.form.get("data_nascimento") or None,
        "exame_id": request.form.get("exame_id") or None,
        "data_agendamento": request.form.get("data_agendamento") or None,
        "horario": request.form.get("horario"),
        "status_id": request.form.get("status_id") or None,
        "status_descricao": request.form.get("status_descricao")
    }).eq("id", agendamento_id).execute()

    salvar_anexos_endocrino(
        request.files.getlist("anexos"),
        request.form.getlist("nomes_anexos"),
        agendamento_id
    )

    return redirect("/endocrinos")


@app.route("/endocrinos/agendamento/excluir/<agendamento_id>", methods=["POST"])
def endocrino_agendamento_excluir(agendamento_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("endocrino_agendamentos").delete().eq("id", agendamento_id).execute()

    return redirect("/endocrinos")


@app.route("/usuarios-cargos")
def usuarios_cargos():
    if not usuario_logado():
        return redirect("/login")

    usuarios = (
        supabase.table("usuarios")
        .select("*, cargos(*)")
        .order("nome_completo")
        .execute()
    )

    cargos = (
        supabase.table("cargos")
        .select("*")
        .order("nome")
        .execute()
    )

    return render_template(
        "usuarios_cargos.html",
        usuarios=usuarios.data,
        cargos=cargos.data,
        nome=session.get("usuario_nome"),
        cargo=session.get("usuario_cargo"),
        permissoes=permissoes_usuario()
    )


@app.route("/cargos/novo", methods=["POST"])
def cargos_novo():
    if not usuario_logado():
        return redirect("/login")

    permissoes = request.form.getlist("permissoes")

    permissoes_json = {}

    for permissao in permissoes:
        permissoes_json[permissao] = True

    supabase.table("cargos").insert({
        "nome": request.form.get("nome"),
        "permissoes": permissoes_json
    }).execute()

    return redirect("/usuarios-cargos")


@app.route("/cargos/editar/<cargo_id>", methods=["POST"])
def cargos_editar(cargo_id):
    if not usuario_logado():
        return redirect("/login")

    permissoes = request.form.getlist("permissoes")

    permissoes_json = {}

    for permissao in permissoes:
        permissoes_json[permissao] = True

    supabase.table("cargos").update({
        "nome": request.form.get("nome"),
        "permissoes": permissoes_json
    }).eq("id", cargo_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/cargos/excluir/<cargo_id>", methods=["POST"])
def cargos_excluir(cargo_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("cargos").delete().eq("id", cargo_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/usuarios/aprovar/<usuario_id>", methods=["POST"])
def usuarios_aprovar(usuario_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("usuarios").update({
        "aprovado": True,
        "status_cadastro": "aprovado",
        "cargo_id": request.form.get("cargo_id"),
        "cargo": request.form.get("cargo_nome")
    }).eq("id", usuario_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/usuarios/negar/<usuario_id>", methods=["POST"])
def usuarios_negar(usuario_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("usuarios").update({
        "aprovado": False,
        "status_cadastro": "negado"
    }).eq("id", usuario_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/usuarios/editar/<usuario_id>", methods=["POST"])
def usuarios_editar(usuario_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("usuarios").update({
        "nome_completo": request.form.get("nome_completo"),
        "cpf": request.form.get("cpf"),
        "cargo_id": request.form.get("cargo_id"),
        "cargo": request.form.get("cargo_nome"),
        "aprovado": "aprovado" in request.form,
        "status_cadastro": "aprovado" if "aprovado" in request.form else "pendente"
    }).eq("id", usuario_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/usuarios/excluir/<usuario_id>", methods=["POST"])
def usuarios_excluir(usuario_id):
    if not usuario_logado():
        return redirect("/login")

    supabase.table("usuarios").delete().eq("id", usuario_id).execute()

    return redirect("/usuarios-cargos")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)