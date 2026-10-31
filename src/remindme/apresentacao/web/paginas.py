"""Páginas HTML da interface web (Spec 017). Só montam o que os serviços devolvem; nenhuma regra aqui (INV-1)."""

from dataclasses import dataclass
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import graficos as g
from remindme.apresentacao.web.html import Html, e, h, juntar
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario

Erros = Dict[str, str]
Valores = Dict[str, str]


@dataclass(frozen=True)
class Contexto:
    """Quem está usando a página: o usuário da sessão, as operações do perfil e a proteção dos formulários."""

    usuario: Usuario
    operacoes: FrozenSet[Operacao]
    protecao: str
    hoje: date

    def pode(self, operacao: Operacao) -> bool:
        return operacao in self.operacoes


MENU = (
    ("painel", "/painel", "Painel", "◧", None),
    ("empresa", "/empresa", "Empresa", "▣", None),
    ("titulos", "/titulos", "Títulos", "▤", Operacao.CONSULTAR_TITULOS),
    ("orcamentos", "/orcamentos", "Orçamentos", "◇", Operacao.CONDUZIR_ORCAMENTO),
    ("clientes", "/clientes", "Clientes", "◉", Operacao.CONSULTAR_CLIENTES),
    ("auditoria", "/auditoria", "Auditoria", "⌕", Operacao.CONSULTAR_AUDITORIA),
    ("usuarios", "/usuarios", "Usuários", "◎", Operacao.ADMINISTRAR_USUARIOS),
    ("permissoes", "/permissoes", "Permissões", "▦", Operacao.ADMINISTRAR_USUARIOS),
)

CLASSE_DO_ESTADO = {
    EstadoTitulo.ABERTO: "aberto",
    EstadoTitulo.VENCIDO: "vencido",
    EstadoTitulo.BAIXADO: "baixado",
    EstadoTitulo.CANCELADO: "cancelado",
}

CLASSE_DO_ESTADO_DO_ORCAMENTO = {
    EstadoOrcamento.RASCUNHO: "aberto",
    EstadoOrcamento.PENDENTE_DE_ALCADA: "proximo",
    EstadoOrcamento.ENVIADO: "aberto",
    EstadoOrcamento.APROVADO: "baixado",
    EstadoOrcamento.CONVERTIDO: "baixado",
    EstadoOrcamento.REJEITADO: "cancelado",
    EstadoOrcamento.CANCELADO: "cancelado",
}

PERFIS_DE_USUARIO = list(Perfil)


# Estrutura


DESCRICAO_PADRAO = "RemindMe: gestão de recebíveis, orçamentos e clientes de micro e pequenas empresas."


def _documento_html(titulo: str, corpo: Html, descricao: str = DESCRICAO_PADRAO) -> Html:
    return h(
        """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} | RemindMe</title>
<meta name="description" content="{descricao}">
<meta name="theme-color" content="#0f1e3d">
<link rel="icon" href="/estatico/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="/estatico/estilo.css">
<script src="/estatico/tema.js"></script>
</head>
<body>
{corpo}
</body>
</html>
""",
        titulo=titulo,
        corpo=corpo,
        descricao=descricao,
    )


def layout(titulo: str, conteudo: Html, ctx: Contexto, secao: str = "", aviso: Optional[Tuple[str, str]] = None) -> Html:
    itens = juntar(
        h(
            '<li><a href="{href}"{atual}><span class="icone" aria-hidden="true">{icone}</span>{rotulo}</a></li>',
            href=href,
            atual=Html(' aria-current="page"') if chave == secao else Html(""),
            icone=icone,
            rotulo=rotulo,
        )
        for chave, href, rotulo, icone, operacao in MENU
        if operacao is None or ctx.pode(operacao)
    )
    corpo = h(
        """<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <a class="marca" href="/painel"><img src="/estatico/icone.svg" alt="">RemindMe</a>
  <div class="quem">
    <span class="nome-completo"><strong>{nome}</strong></span>
    <span class="perfil">{perfil}</span>
    <button id="trocar-tema" class="discreto botao-tema" type="button" hidden aria-label="Trocar entre tema claro e escuro" title="Tema claro/escuro">Tema</button>
    <form method="post" action="/sair">{protecao}<button class="discreto" type="submit">Sair</button></form>
  </div>
</header>
<div class="corpo">
  <nav class="menu" aria-label="Principal"><ul>{itens}</ul></nav>
  <main id="conteudo">{aviso}{conteudo}</main>
</div>""",
        nome=ctx.usuario.nome,
        perfil=ctx.usuario.perfil.value,
        protecao=protecao(ctx),
        itens=itens,
        aviso=caixa_de_aviso(*aviso) if aviso else Html(""),
        conteudo=conteudo,
    )
    return _documento_html(titulo, corpo)


def cabecalho(titulo: str, subtitulo: str = "", acoes: Html = Html("")) -> Html:
    return h(
        '<div class="cabecalho"><div><h1>{titulo}</h1>{subtitulo}</div><div class="acoes">{acoes}</div></div>',
        titulo=titulo,
        subtitulo=h("<p>{t}</p>", t=subtitulo) if subtitulo else Html(""),
        acoes=acoes,
    )


def caixa_de_aviso(tipo: str, texto: str) -> Html:
    papel = "alert" if tipo == "erro" else "status"
    return h('<div class="aviso {tipo}" role="{papel}">{texto}</div>', tipo=tipo, papel=papel, texto=texto)


def protecao(ctx: Contexto) -> Html:
    return h('<input type="hidden" name="protecao" value="{p}">', p=ctx.protecao)


def botao_link(href: str, texto: str, classe: str = "") -> Html:
    return h('<a class="botao {classe}" href="{href}">{texto}</a>', classe=classe, href=href, texto=texto)


def selo_estado(estado: EstadoTitulo, grande: bool = False) -> Html:
    return h(
        '<span class="selo {classe}{grande}">{texto}</span>',
        classe=CLASSE_DO_ESTADO[estado],
        grande=" grande" if grande else "",
        texto=estado.value,
    )


def selo_proximo() -> Html:
    return Html('<span class="selo proximo">Próximo do vencimento</span>')


# Campos


def _erro_do_campo(nome: str, erros: Erros) -> Tuple[Html, Html]:
    if nome not in erros:
        return Html(""), Html("")
    return (
        h(' aria-invalid="true" aria-describedby="erro-{n}"', n=nome),
        h('<span class="erro" id="erro-{n}">{m}</span>', n=nome, m=erros[nome]),
    )


def campo(
    nome: str,
    rotulo: str,
    valores: Valores,
    erros: Erros,
    tipo: str = "text",
    ajuda: str = "",
    obrigatorio: bool = True,
    extra: str = "",
) -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    return h(
        """<div class="campo"><label for="{n}">{rotulo}</label>{ajuda}
<input id="{n}" name="{n}" type="{tipo}" value="{valor}"{obrigatorio}{atributos}{extra}>{mensagem}</div>""",
        n=nome,
        rotulo=rotulo,
        ajuda=h('<span class="ajuda">{a}</span>', a=ajuda) if ajuda else Html(""),
        tipo=tipo,
        valor=valores.get(nome, ""),
        obrigatorio=Html(" required") if obrigatorio else Html(""),
        atributos=atributos,
        extra=Html(" " + extra) if extra else Html(""),
        mensagem=mensagem,
    )


def selecao(
    nome: str,
    rotulo: str,
    opcoes: Iterable[Tuple[str, str]],
    valores: Valores,
    erros: Erros,
    vazio: Optional[str] = None,
    obrigatorio: bool = True,
) -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    escolhido = valores.get(nome, "")
    itens = [h('<option value="">{t}</option>', t=vazio)] if vazio is not None else []
    itens += [
        h('<option value="{v}"{s}>{t}</option>', v=valor, s=Html(" selected") if valor == escolhido else Html(""), t=texto)
        for valor, texto in opcoes
    ]
    return h(
        '<div class="campo"><label for="{n}">{rotulo}</label><select id="{n}" name="{n}"{obrigatorio}{atributos}>{itens}</select>{mensagem}</div>',
        n=nome,
        rotulo=rotulo,
        obrigatorio=Html(" required") if obrigatorio else Html(""),
        atributos=atributos,
        itens=juntar(itens),
        mensagem=mensagem,
    )


def area(nome: str, rotulo: str, valores: Valores, erros: Erros, ajuda: str = "") -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    return h(
        '<div class="campo"><label for="{n}">{rotulo}</label>{ajuda}<textarea id="{n}" name="{n}" required{atributos}>{valor}</textarea>{mensagem}</div>',
        n=nome,
        rotulo=rotulo,
        ajuda=h('<span class="ajuda">{a}</span>', a=ajuda) if ajuda else Html(""),
        atributos=atributos,
        valor=valores.get(nome, ""),
        mensagem=mensagem,
    )


def erro_geral(erros: Erros) -> Html:
    return caixa_de_aviso("erro", erros["_"]) if "_" in erros else Html("")


def tabela(cabecalhos: Sequence[Tuple[str, str]], linhas: List[Html], vazio: str) -> Html:
    if not linhas:
        return h('<p class="vazio">{v}</p>', v=vazio)
    cabeca = juntar(h('<th scope="col" class="{c}">{t}</th>', c=classe, t=texto) for texto, classe in cabecalhos)
    return h('<div class="tabela"><table><thead><tr>{c}</tr></thead><tbody>{l}</tbody></table></div>', c=cabeca, l=juntar(linhas))


# Entrada


# Telas públicas: entrar e criar conta. Painel da marca à esquerda (com a régua do caixa em miniatura,
# só ilustrativa) e o formulário à direita.

_REGUA_ILUSTRATIVA = Html(
    """<svg class="regua-ilustrativa" viewBox="-12 -6 224 50" aria-hidden="true" focusable="false">
<line class="eixo" x1="0" y1="34" x2="200" y2="34"/><line class="hoje" x1="133" y1="0" x2="133" y2="37"/>
<line class="haste" x1="58" y1="34" x2="58" y2="28"/><circle class="vermelho" cx="58" cy="28" r="3.2"/><text x="58" y="21">R$ 680</text>
<line class="haste" x1="102" y1="34" x2="102" y2="14"/><circle class="vermelho" cx="102" cy="14" r="3.2"/><text x="102" y="7">R$ 3,8 mil</text>
<line class="haste" x1="146" y1="34" x2="146" y2="28"/><circle class="laranja" cx="146" cy="28" r="3.2"/><text x="146" y="21">R$ 1,2 mil</text>
<line class="haste" x1="186" y1="34" x2="186" y2="28"/><circle class="azul" cx="186" cy="28" r="3.2"/><text x="186" y="21">R$ 720</text>
<text class="rotulo" x="133" y="44">hoje</text>
</svg>"""
)


def _tela_publica(titulo: str, descricao: str, conteudo: Html) -> Html:
    corpo = h(
        """<div class="publica">
  <aside class="publica-marca">
    <div class="marca marca-clara"><img src="/estatico/icone.svg" alt="">RemindMe</div>
    <p class="publica-frase">Cada cobrança e cada prazo no dia certo.</p>
    <p class="publica-apoio">Títulos, orçamentos e clientes da sua empresa, com o que vence hoje à vista.</p>
    {regua}
  </aside>
  <main class="publica-conteudo" id="conteudo">{conteudo}</main>
</div>""",
        regua=_REGUA_ILUSTRATIVA,
        conteudo=conteudo,
    )
    return _documento_html(titulo, corpo, descricao)


def pagina_entrar(protecao_da_entrada: str, email: str = "", erro: str = "", aviso: str = "", volta: str = "") -> Html:
    conteudo = h(
        """<h1>Entrar</h1>
{aviso}{erro}
<form class="formulario" method="post" action="/entrar">
  <input type="hidden" name="protecao" value="{protecao}">{volta}
  <div class="campo"><label for="email">E-mail</label>
    <input id="email" name="email" type="email" value="{email}" autocomplete="username" required autofocus></div>
  <div class="campo"><label for="senha">Senha</label>
    <input id="senha" name="senha" type="password" autocomplete="current-password" required></div>
  <button type="submit">Entrar</button>
</form>
<p class="publica-troca">Ainda não tem acesso? <a href="/criar-conta">Criar conta</a></p>""",
        aviso=caixa_de_aviso("info", aviso) if aviso else Html(""),
        erro=caixa_de_aviso("erro", erro) if erro else Html(""),
        protecao=protecao_da_entrada,
        volta=h('\n  <input type="hidden" name="volta" value="{v}">', v=volta) if volta else Html(""),
        email=email,
    )
    return _tela_publica(
        "Entrar", "Entre no RemindMe para acompanhar títulos a receber, orçamentos e clientes da sua empresa.", conteudo
    )


PERFIS_DA_CRIACAO_DE_CONTA = [p for p in Perfil if p is not Perfil.ADMINISTRADOR]


def pagina_criar_conta(protecao_da_entrada: str, valores: Valores, erros: Erros, criada: bool = False) -> Html:
    if criada:
        conteudo = h(
            """<h1>Conta criada</h1>
<p class="publica-texto">A conta de {email} aguarda a ativação pelo Administrador da empresa. Assim que ela for ativada, entre com o seu e-mail e a senha que você escolheu.</p>
<p><a class="botao" href="/entrar">Ir para a entrada</a></p>""",
            email=valores.get("email", ""),
        )
    else:
        conteudo = h(
            """<h1>Criar conta</h1>
<p class="publica-texto">A conta fica aguardando a ativação pelo Administrador da empresa.</p>
<form class="formulario" method="post" action="/criar-conta" novalidate>
  <input type="hidden" name="protecao" value="{protecao}">{geral}
  {nome}{email}{perfil}{senha}
  <button type="submit">Criar conta</button>
</form>
<p class="publica-troca">Já tem acesso? <a href="/entrar">Entrar</a></p>""",
            protecao=protecao_da_entrada,
            geral=erro_geral(erros),
            nome=campo("nome", "Nome", valores, erros, extra='autocomplete="name"'),
            email=campo("email", "E-mail", valores, erros, tipo="email", extra='autocomplete="email"'),
            perfil=selecao("perfil", "Perfil", [(p.name, p.value) for p in PERFIS_DA_CRIACAO_DE_CONTA], valores, erros, vazio="Escolha o perfil"),
            senha=campo("senha", "Senha", {}, erros, tipo="password", ajuda="Pelo menos 8 caracteres.", extra='autocomplete="new-password"'),
        )
    return _tela_publica("Criar conta", "Peça acesso ao RemindMe da sua empresa. A conta é ativada pelo Administrador.", conteudo)


# Painel


def pagina_painel(
    ctx: Contexto,
    visoes: Optional[list],
    nomes_clientes: Dict[str, str],
    registros: Optional[list],
    usuarios: Optional[List[Usuario]],
    aviso: Optional[Tuple[str, str]] = None,
    pendentes: Optional[list] = None,
    pagamentos: Optional[list] = None,
    orcamentos: Optional[list] = None,
) -> Html:
    partes: List[Html] = []
    acoes = []
    if ctx.pode(Operacao.CADASTRAR_TITULO):
        acoes.append(botao_link("/titulos/novo", "Novo título"))
    if ctx.pode(Operacao.CONDUZIR_ORCAMENTO):
        acoes.append(botao_link("/orcamentos/novo", "Novo orçamento", "secundario"))
    if ctx.pode(Operacao.MANTER_CLIENTES):
        acoes.append(botao_link("/clientes/novo", "Novo cliente", "secundario"))
    primeiro_nome = ctx.usuario.nome.split()[0] if ctx.usuario.nome else ""
    partes.append(cabecalho(f"Olá, {primeiro_nome}", f.data_por_extenso(ctx.hoje).capitalize(), juntar(acoes)))
    if visoes is not None:
        partes.append(_regua_do_caixa(visoes, nomes_clientes, ctx))

    if pendentes:
        partes.append(_cartao_pendentes(pendentes, nomes_clientes))
    partes.append(_graficos_do_perfil(ctx, visoes or [], registros or [], pagamentos or [], orcamentos or []))
    if visoes is not None:
        partes.append(_resumo_financeiro(visoes, nomes_clientes, ctx))
    if usuarios is not None:
        ativos = [u for u in usuarios if u.ativo]
        partes.append(
            h(
                """<div class="indicadores">
  <div class="indicador"><div class="rotulo">Usuários ativos</div><div class="numero">{ativos}</div><div class="detalhe">{inativos} inativo(s)</div></div>
  <div class="indicador"><div class="rotulo">Administração</div><div class="detalhe margem-topo"><a href="/usuarios">Usuários</a> e <a href="/permissoes">permissões por perfil</a></div></div>
</div>""",
                ativos=len(ativos),
                inativos=len(usuarios) - len(ativos),
            )
        )
    if registros is not None:
        operacoes = [r for r in registros if r.campo != "sessão"]
        itens = [_item_do_historico(r) for r in operacoes[-3:][::-1]]
        partes.append(
            h(
                '<section class="cartao sem-borda-interna"><h2>Últimas operações</h2>{lista}<p class="secundario rodape-cartao"><a href="/auditoria">Ver toda a auditoria</a></p></section>',
                lista=h('<ul class="historico">{i}</ul>', i=juntar(itens)) if itens else h('<p class="vazio">{t}</p>', t="Nenhuma operação registrada ainda."),
            )
        )
    if visoes is None and usuarios is None and registros is None:
        partes.append(caixa_de_aviso("info", "O seu perfil ainda não tem funcionalidades nesta versão."))
    return layout("Painel", juntar(partes), ctx, "painel", aviso)


# Gráficos do painel: um conjunto por perfil, com os dados que o painel já tem.

MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _regua_do_caixa(visoes: list, nomes_clientes: Dict[str, str], ctx: Contexto) -> Html:
    """O destaque do painel: vencidos à esquerda do hoje e os próximos 15 dias à direita."""
    marcos = []
    for v in visoes:
        dias = (v.vencimento - ctx.hoje).days
        if v.estado is EstadoTitulo.VENCIDO:
            cor = "vermelho"
        elif v.estado is EstadoTitulo.ABERTO and dias <= g.DIAS_DEPOIS:
            cor = "laranja" if v.proximo_do_vencimento else "azul"
        else:
            continue
        marcos.append((nomes_clientes.get(v.cliente_id, "Cliente"), dias, v.saldo, cor, f"/titulos/{v.id}"))
    vencidos = [m for m in marcos if m[3] == "vermelho"]
    a_vencer = [m for m in marcos if m[3] != "vermelho"]
    resumo = h(
        '<p class="regua-resumo"><span class="vermelho">{nv} vencido(s), {sv}</span><span class="laranja">{na} a vencer em 15 dias, {sa}</span></p>',
        nv=len(vencidos), sv=f.moeda(sum((m[2] for m in vencidos), Decimal("0.00"))),
        na=len(a_vencer), sa=f.moeda(sum((m[2] for m in a_vencer), Decimal("0.00"))),
    )
    return h(
        '<section class="regua-do-caixa" aria-labelledby="t-regua"><h2 id="t-regua">Régua do caixa</h2>{r}{g}</section>',
        r=resumo, g=g.regua(marcos, f.moeda_curta, f.data(ctx.hoje)[:5]),
    )


def _cartao_grafico(titulo: str, grafico: Html) -> Html:
    return h('<section class="cartao cartao-grafico"><h2>{t}</h2>{g}</section>', t=titulo, g=grafico)


def _graficos_do_perfil(ctx: Contexto, visoes: list, registros: list, pagamentos: list, orcamentos: list) -> Html:
    perfil = ctx.usuario.perfil
    if perfil is Perfil.DONO:
        cartoes = [
            _cartao_grafico("Recebido nos últimos 6 meses", g.colunas(_recebido_por_mes(pagamentos, ctx.hoje), f.moeda_curta, "Recebido por mês")),
            _cartao_grafico("Carteira de títulos", g.anel(_carteira(visoes), f.moeda, "Carteira de títulos por situação")),
        ]
    elif perfil is Perfil.ADMINISTRADOR:
        acoes = _acoes_dos_ultimos_30_dias(registros, ctx.hoje)
        cartoes = [
            _cartao_grafico("Ações por usuário (30 dias)", g.barras(_contar(acoes, lambda r: r.responsavel, "azul"), _vezes, "Ações por usuário")),
            _cartao_grafico("Ações mais comuns (30 dias)", g.barras(_contar(acoes, lambda r: r.operacao, "laranja")[:5], _vezes, "Ações mais comuns")),
        ]
    elif perfil is Perfil.OPERADOR_FINANCEIRO:
        cartoes = [
            _cartao_grafico("Meus orçamentos por estado", g.barras(_orcamentos_por_estado(orcamentos), _vezes, "Orçamentos por estado")),
            _cartao_grafico("A receber nos próximos 7 dias", g.colunas(_proximos_7_dias(visoes, ctx.hoje), f.moeda_curta, "A receber por dia")),
        ]
    elif perfil is Perfil.CONTADOR:
        cartoes = [_cartao_grafico("Carteira por atraso", g.barras(_faixas_de_atraso(visoes, ctx.hoje), f.moeda, "Saldo por faixa de atraso"))]
    else:
        return Html("")
    return h('<div class="grade-2">{c}</div>', c=juntar(cartoes))


def _vezes(quantidade: Decimal) -> str:
    return f"{quantidade:.0f}"


def _recebido_por_mes(pagamentos: list, hoje: date) -> list:
    """Os 6 meses até o atual, do mais antigo ao mais recente."""
    meses = []
    ano, mes = hoje.year, hoje.month
    for _ in range(6):
        meses.insert(0, (ano, mes))
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return [
        (MESES[m - 1], sum((p.valor for p in pagamentos if (p.data.year, p.data.month) == (a, m)), Decimal("0.00")), "azul")
        for a, m in meses
    ]


def _carteira(visoes: list) -> list:
    def soma(estado, campo):
        return sum((getattr(v, campo) for v in visoes if v.estado is estado), Decimal("0.00"))

    return [
        ("A receber em dia", soma(EstadoTitulo.ABERTO, "saldo"), "azul"),
        ("Vencido", soma(EstadoTitulo.VENCIDO, "saldo"), "vermelho"),
        ("Recebido (baixado)", soma(EstadoTitulo.BAIXADO, "valor"), "verde"),
    ]


def _acoes_dos_ultimos_30_dias(registros: list, hoje: date) -> list:
    """Ações de pessoas (sem entradas e saídas do sistema e sem rotinas automáticas)."""
    inicio = hoje - timedelta(days=30)
    return [r for r in registros if not r.automatica and r.campo != "sessão" and r.data_hora.date() >= inicio]


def _contar(registros: list, chave, cor: str) -> list:
    return [(nome, Decimal(total), cor) for nome, total in Counter(chave(r) for r in registros).most_common()]


def _orcamentos_por_estado(orcamentos: list) -> list:
    cores = {
        EstadoOrcamento.RASCUNHO: "azul",
        EstadoOrcamento.PENDENTE_DE_ALCADA: "laranja",
        EstadoOrcamento.CANCELADO: "cinza",
    }
    return [(estado.value, Decimal(sum(1 for o in orcamentos if o.estado is estado)), cor) for estado, cor in cores.items()]


def _proximos_7_dias(visoes: list, hoje: date) -> list:
    dias = [hoje + timedelta(days=n) for n in range(7)]
    return [
        (dia.strftime("%d/%m"), sum((v.saldo for v in visoes if v.estado is EstadoTitulo.ABERTO and v.vencimento == dia), Decimal("0.00")), "azul")
        for dia in dias
    ]


def _faixas_de_atraso(visoes: list, hoje: date) -> list:
    def soma(minimo, maximo):
        return sum(
            (v.saldo for v in visoes if v.estado is EstadoTitulo.VENCIDO and minimo <= (hoje - v.vencimento).days <= maximo),
            Decimal("0.00"),
        )

    em_dia = sum((v.saldo for v in visoes if v.estado is EstadoTitulo.ABERTO), Decimal("0.00"))
    return [
        ("Em dia", em_dia, "azul"),
        ("Até 30 dias", soma(1, 30), "laranja"),
        ("31 a 60 dias", soma(31, 60), "vermelho"),
        ("Mais de 60 dias", soma(61, 100000), "vermelho"),
    ]


def _resumo_financeiro(visoes: list, nomes_clientes: Dict[str, str], ctx: Contexto) -> Html:
    em_aberto = [v for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)]
    vencidos = [v for v in visoes if v.estado is EstadoTitulo.VENCIDO]
    proximos = [v for v in visoes if v.proximo_do_vencimento]
    baixados = [v for v in visoes if v.estado is EstadoTitulo.BAIXADO]
    soma = lambda lista: sum((v.saldo for v in lista), Decimal("0.00"))  # noqa: E731
    indicadores = h(
        """<div class="indicadores">
  <div class="indicador"><div class="rotulo">A receber</div><div class="numero">{receber}</div><div class="detalhe">{n_aberto} título(s) Aberto(s) ou Vencido(s)</div></div>
  <div class="indicador atraso"><div class="rotulo">Em atraso</div><div class="numero">{atraso}</div><div class="detalhe">{n_vencido} título(s) Vencido(s)</div></div>
  <div class="indicador proximo"><div class="rotulo">Vencem em breve</div><div class="numero">{n_proximo}</div><div class="detalhe">{proximo} nos próximos dias</div></div>
  <div class="indicador recebido"><div class="rotulo">Baixados</div><div class="numero">{n_baixado}</div><div class="detalhe">títulos pagos por completo</div></div>
</div>""",
        receber=f.moeda(soma(em_aberto)),
        n_aberto=len(em_aberto),
        atraso=f.moeda(soma(vencidos)),
        n_vencido=len(vencidos),
        n_proximo=len(proximos),
        proximo=f.moeda(soma(proximos)),
        n_baixado=len(baixados),
    )
    linhas_vencidos = [
        h(
            '<tr class="vencido"><td><a href="/titulos/{id}">{cliente}</a></td><td>{venc}</td><td class="numero">{dias}</td><td class="numero">{saldo}</td></tr>',
            id=v.id,
            cliente=nomes_clientes.get(v.cliente_id, "Cliente"),
            venc=f.data(v.vencimento),
            dias=(ctx.hoje - v.vencimento).days,
            saldo=f.moeda(v.saldo),
        )
        for v in sorted(vencidos, key=lambda v: v.vencimento)
    ]
    linhas_proximos = [
        h(
            '<tr><td><a href="/titulos/{id}">{cliente}</a></td><td>{venc}</td><td class="numero">{saldo}</td></tr>',
            id=v.id,
            cliente=nomes_clientes.get(v.cliente_id, "Cliente"),
            venc=f.data(v.vencimento),
            saldo=f.moeda(v.saldo),
        )
        for v in sorted(proximos, key=lambda v: v.vencimento)
    ]
    return h(
        """{indicadores}
<div class="grade-2">
  <section class="cartao sem-borda-interna" aria-labelledby="t-vencidos"><h2 id="t-vencidos">Títulos vencidos</h2>{vencidos}</section>
  <section class="cartao sem-borda-interna" aria-labelledby="t-proximos"><h2 id="t-proximos">Próximos do vencimento</h2>{proximos}</section>
</div>""",
        indicadores=indicadores,
        vencidos=tabela([("Cliente", ""), ("Vencimento", ""), ("Dias em atraso", "numero"), ("Saldo", "numero")], linhas_vencidos, "Nenhum título vencido."),
        proximos=tabela([("Cliente", ""), ("Vencimento", ""), ("Saldo", "numero")], linhas_proximos, "Nenhum título vence nos próximos dias."),
    )


# Clientes


def pagina_clientes(ctx: Contexto, clientes: list, termo: str, aviso=None) -> Html:
    acoes = botao_link("/clientes/novo", "Novo cliente") if ctx.pode(Operacao.MANTER_CLIENTES) else Html("")
    busca = h(
        """<form class="filtros" method="get" action="/clientes" role="search">
  <div class="campo"><label for="q">Pesquisar por nome ou documento</label><input id="q" name="q" type="search" value="{termo}"></div>
  <div><button class="secundario" type="submit">Pesquisar</button></div>
</form>""",
        termo=termo,
    )
    linhas = [
        h(
            '<tr><td><a href="/clientes/{id}">{nome}</a></td><td class="mono">{doc}</td><td>{contato}</td></tr>',
            id=c.id,
            nome=c.nome,
            doc=f.documento(c.documento),
            contato=f.contato(c.contato),
        )
        for c in clientes
    ]
    vazio = "Nenhum cliente encontrado para a pesquisa." if termo else "Nenhum cliente cadastrado ainda."
    conteudo = juntar(
        [
            cabecalho("Clientes", "Quem deve títulos à empresa.", acoes),
            h('<section class="cartao">{b}</section>', b=busca),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela([("Nome", ""), ("Documento", ""), ("Contato", "")], linhas, vazio)),
        ]
    )
    return layout("Clientes", conteudo, ctx, "clientes", aviso)


def pagina_cliente_formulario(ctx: Contexto, valores: Valores, erros: Erros, cliente_id: Optional[str] = None) -> Html:
    novo = cliente_id is None
    acao = "/clientes/novo" if novo else f"/clientes/{cliente_id}/editar"
    formulario = h(
        """<form class="formulario" method="post" action="{acao}" novalidate>
{protecao}{geral}
{nome}
<div class="linha-campos">{documento}{contato}</div>
<div class="acoes"><button type="submit">{botao}</button><a class="botao secundario" href="{voltar}">Cancelar</a></div>
</form>""",
        acao=acao,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        nome=campo("nome", "Nome ou razão social", valores, erros),
        documento=campo("documento", "CPF ou CNPJ", valores, erros, ajuda="Com ou sem pontuação."),
        contato=campo("contato", "Contato", valores, erros, ajuda="E-mail ou telefone com DDD."),
        botao="Cadastrar cliente" if novo else "Salvar alterações",
        voltar="/clientes" if novo else f"/clientes/{cliente_id}",
    )
    titulo = "Novo cliente" if novo else "Alterar cliente"
    conteudo = juntar([cabecalho(titulo), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout(titulo, conteudo, ctx, "clientes")


def pagina_cliente(ctx: Contexto, cliente, visoes: list, historico: Optional[list], aviso=None) -> Html:
    acoes = []
    if ctx.pode(Operacao.CADASTRAR_TITULO):
        acoes.append(botao_link(f"/titulos/novo?cliente={cliente.id}", "Novo título"))
    if ctx.pode(Operacao.MANTER_CLIENTES):
        acoes.append(botao_link(f"/clientes/{cliente.id}/editar", "Alterar dados", "secundario"))
    dados = h(
        '<dl class="dados"><div><dt>Documento</dt><dd class="mono">{doc}</dd></div><div><dt>Contato</dt><dd>{contato}</dd></div><div><dt>Títulos</dt><dd>{n}</dd></div><div><dt>Saldo em aberto</dt><dd>{saldo}</dd></div></dl>',
        doc=f.documento(cliente.documento),
        contato=f.contato(cliente.contato),
        n=len(visoes),
        saldo=f.moeda(sum((v.saldo for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)), Decimal("0.00"))),
    )
    partes = [
        cabecalho(cliente.nome, "Cliente", juntar(acoes)),
        h('<section class="cartao">{d}</section>', d=dados),
        h('<section class="cartao sem-borda-interna"><h2>Títulos do cliente</h2>{t}</section>', t=_tabela_de_titulos(visoes, {}, mostrar_cliente=False)),
    ]
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout(cliente.nome, juntar(partes), ctx, "clientes", aviso)


# Títulos


def _tabela_de_titulos(visoes: list, nomes_clientes: Dict[str, str], mostrar_cliente: bool = True) -> Html:
    cabecalhos = ([("Cliente", "")] if mostrar_cliente else []) + [
        ("Vencimento", ""),
        ("Valor", "numero"),
        ("Saldo", "numero"),
        ("Estado", ""),
    ]
    linhas = []
    for v in visoes:
        cliente = h('<td><a href="/titulos/{id}">{n}</a></td>', id=v.id, n=nomes_clientes.get(v.cliente_id, "Cliente")) if mostrar_cliente else Html("")
        vencimento = h('<td><a href="/titulos/{id}">{d}</a></td>', id=v.id, d=f.data(v.vencimento)) if not mostrar_cliente else h("<td>{d}</td>", d=f.data(v.vencimento))
        linhas.append(
            h(
                '<tr class="{classe}">{cliente}{vencimento}<td class="numero">{valor}</td><td class="numero">{saldo}</td><td>{estado} {proximo}</td></tr>',
                classe="vencido" if v.estado is EstadoTitulo.VENCIDO else "",
                cliente=cliente,
                vencimento=vencimento,
                valor=f.moeda(v.valor),
                saldo=f.moeda(v.saldo),
                estado=selo_estado(v.estado),
                proximo=selo_proximo() if v.proximo_do_vencimento else Html(""),
            )
        )
    return tabela(cabecalhos, linhas, "Nenhum título encontrado.")


def pagina_titulos(ctx: Contexto, visoes: list, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros, aviso=None) -> Html:
    acoes = []
    if ctx.pode(Operacao.VERIFICAR_VENCIMENTOS):
        acoes.append(
            h(
                '<form method="post" action="/titulos/verificar-vencimentos">{p}<button class="secundario" type="submit">Verificar vencimentos</button></form>',
                p=protecao(ctx),
            )
        )
    if ctx.pode(Operacao.CADASTRAR_TITULO):
        acoes.append(botao_link("/titulos/novo", "Novo título"))
    opcoes_clientes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    filtros = h(
        """<form class="filtros" method="get" action="/titulos">
{cliente}{estado}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/titulos">Limpar</a></div>
</form>""",
        cliente=selecao("cliente", "Cliente", opcoes_clientes, valores, erros, vazio="Todos", obrigatorio=False),
        estado=selecao("estado", "Estado", [(e_.name, e_.value) for e_ in EstadoTitulo], valores, erros, vazio="Todos", obrigatorio=False),
        de=campo("de", "Vencimento de", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("ate", "Vencimento até", valores, erros, tipo="date", obrigatorio=False),
    )
    total = sum((v.saldo for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)), Decimal("0.00"))
    conteudo = juntar(
        [
            cabecalho("Títulos", f"{len(visoes)} título(s), com {f.moeda(total)} em aberto", juntar(acoes)),
            h('<section class="cartao">{f}</section>', f=filtros),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=_tabela_de_titulos(visoes, nomes_clientes)),
        ]
    )
    return layout("Títulos", conteudo, ctx, "titulos", aviso)


def pagina_titulo_formulario(ctx: Contexto, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros) -> Html:
    opcoes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    if not opcoes:
        aviso = caixa_de_aviso("info", "Cadastre um cliente antes de cadastrar o título.")
        acao = botao_link("/clientes/novo", "Novo cliente") if ctx.pode(Operacao.MANTER_CLIENTES) else Html("")
        return layout("Novo título", juntar([cabecalho("Novo título"), aviso, acao]), ctx, "titulos")
    formulario = h(
        """<form class="formulario" method="post" action="/titulos/novo" novalidate>
{protecao}{geral}
{cliente}
<div class="linha-campos">{valor}{vencimento}</div>
{condicao}
<div class="acoes"><button type="submit">Cadastrar título</button><a class="botao secundario" href="/titulos">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        cliente=selecao("cliente", "Cliente", opcoes, valores, erros, vazio="Escolha o cliente"),
        valor=campo("valor", "Valor (R$)", valores, erros, ajuda="Por exemplo, 1.234,56.", extra='inputmode="decimal"'),
        vencimento=campo("vencimento", "Vencimento", valores, erros, tipo="date"),
        condicao=campo("condicao", "Condição de pagamento", valores, erros, obrigatorio=False, ajuda="Opcional. Por exemplo, à vista no Pix."),
    )
    conteudo = juntar([cabecalho("Novo título", "O título nasce Aberto, com origem manual e saldo igual ao valor."), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Novo título", conteudo, ctx, "titulos")


def pagina_titulo(
    ctx: Contexto,
    titulo,
    cliente_nome: str,
    proximo: bool,
    pedido: str,
    valores: Valores,
    erros: Erros,
    historico: Optional[list],
    aviso=None,
) -> Html:
    aceita_pagamento = titulo.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)
    acoes = []
    if aceita_pagamento and ctx.pode(Operacao.CANCELAR_TITULO):
        acoes.append(botao_link(f"/titulos/{titulo.id}/cancelamento", "Cancelar título", "secundario"))
    dados = h(
        """<dl class="dados">
<div><dt>Valor</dt><dd>{valor}</dd></div>
<div><dt>Saldo</dt><dd>{saldo}</dd></div>
<div><dt>Vencimento</dt><dd>{venc}</dd></div>
<div><dt>Condição de pagamento</dt><dd>{condicao}</dd></div>
<div><dt>Origem</dt><dd>{origem}</dd></div>
</dl>""",
        valor=f.moeda(titulo.valor),
        saldo=f.moeda(titulo.saldo),
        venc=f.data(titulo.vencimento),
        condicao=titulo.condicao_pagamento or "—",
        origem="Cadastro manual" if titulo.origem == "manual" else titulo.origem,
    )
    linhas = []
    for pagamento in titulo.pagamentos:
        if pagamento.estornado:
            situacao = h('<span class="selo cancelado">Estornado</span> <span class="secundario">{m}</span>', m=pagamento.motivo_estorno or "")
            acao = Html("")
        else:
            situacao = Html('<span class="selo baixado">Registrado</span>')
            acao = (
                h('<a class="botao pequeno secundario" href="/titulos/{t}/pagamentos/{p}/estorno">Estornar</a>', t=titulo.id, p=pagamento.id)
                if ctx.pode(Operacao.ESTORNAR_PAGAMENTO) and titulo.estado is not EstadoTitulo.CANCELADO
                else Html("")
            )
        linhas.append(
            h(
                '<tr><td>{data}</td><td class="numero">{valor}</td><td>{situacao}</td><td class="numero">{acao}</td></tr>',
                data=f.data(pagamento.data),
                valor=f.moeda(pagamento.valor),
                situacao=situacao,
                acao=acao,
            )
        )
    pagamentos = tabela([("Data", ""), ("Valor", "numero"), ("Situação", ""), ("", "numero")], linhas, "Nenhum pagamento registrado.")
    partes = [
        cabecalho(
            cliente_nome,
            "Título",
            juntar(acoes),
        ),
        h('<div class="selos-do-titulo">{estado}{proximo}</div>', estado=selo_estado(titulo.estado, grande=True), proximo=selo_proximo() if proximo else Html("")),
        h('<section class="cartao">{d}</section>', d=dados),
    ]
    if aceita_pagamento and ctx.pode(Operacao.REGISTRAR_PAGAMENTO):
        partes.append(
            h(
                """<section class="cartao" aria-labelledby="t-pagamento"><h2 id="t-pagamento">Registrar pagamento</h2>
<form class="formulario" method="post" action="/titulos/{id}/pagamentos" novalidate>
{protecao}<input type="hidden" name="pedido" value="{pedido}">{geral}
<div class="linha-campos">{valor}{data}</div>
<div class="acoes"><button type="submit">Registrar pagamento</button></div>
</form></section>""",
                id=titulo.id,
                protecao=protecao(ctx),
                pedido=pedido,
                geral=erro_geral(erros),
                valor=campo("valor", "Valor recebido (R$)", valores, erros, ajuda=f"Saldo atual: {f.moeda(titulo.saldo)}.", extra='inputmode="decimal"'),
                data=campo("data", "Data do pagamento", valores, erros, tipo="date"),
            )
        )
    partes.append(h('<section class="cartao sem-borda-interna"><h2>Pagamentos</h2>{p}</section>', p=pagamentos))
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout("Título", juntar(partes), ctx, "titulos", aviso)


def pagina_motivo(
    ctx: Contexto, titulo_pagina: str, explicacao: str, acao: str, voltar: str, botao: str, valores: Valores, erros: Erros,
    secao: str = "titulos",
) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="{acao}" novalidate>
{protecao}{geral}
{motivo}
<div class="acoes"><button class="perigo" type="submit">{botao}</button><a class="botao secundario" href="{voltar}">Voltar</a></div>
</form>""",
        acao=acao,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        motivo=area("motivo", "Motivo", valores, erros, ajuda="Obrigatório. Fica registrado na auditoria."),
        botao=botao,
        voltar=voltar,
    )
    conteudo = juntar([cabecalho(titulo_pagina, explicacao), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout(titulo_pagina, conteudo, ctx, secao)


# Orçamentos (Spec 004)


def selo_orcamento(estado: EstadoOrcamento, grande: bool = False) -> Html:
    return h(
        '<span class="selo {classe}{grande}">{texto}</span>',
        classe=CLASSE_DO_ESTADO_DO_ORCAMENTO[estado],
        grande=" grande" if grande else "",
        texto=estado.value,
    )


def _cartao_pendentes(pendentes: list, nomes_clientes: Dict[str, str]) -> Html:
    """UC-05, gatilho: os descontos que aguardam o Dono aparecem no painel, sem navegação adicional."""
    linhas = [
        h(
            '<tr><td><a href="/orcamentos/{id}">{cliente}</a></td><td class="numero">{solicitado}</td><td class="numero">{alcada}</td><td class="numero">{bruto}</td></tr>',
            id=o.id,
            cliente=nomes_clientes.get(o.cliente_id, "Cliente"),
            solicitado=f.percentual(o.pendencia.percentual_solicitado),
            alcada=f.percentual(o.pendencia.alcada),
            bruto=f.moeda(o.valor_bruto),
        )
        for o in pendentes
    ]
    return h(
        '<section class="cartao sem-borda-interna destaque-alerta" aria-labelledby="t-pendentes"><h2 id="t-pendentes">Descontos aguardando sua decisão</h2>{t}</section>',
        t=tabela([("Cliente", ""), ("Solicitado", "numero"), ("Alçada", "numero"), ("Valor bruto", "numero")], linhas, ""),
    )


def pagina_orcamentos(ctx: Contexto, orcamentos: list, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros, aviso=None) -> Html:
    opcoes_clientes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    filtros = h(
        """<form class="filtros" method="get" action="/orcamentos">
{cliente}{estado}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/orcamentos">Limpar</a></div>
</form>""",
        cliente=selecao("cliente", "Cliente", opcoes_clientes, valores, erros, vazio="Todos", obrigatorio=False),
        estado=selecao("estado", "Estado", [(e_.name, e_.value) for e_ in EstadoOrcamento], valores, erros, vazio="Todos", obrigatorio=False),
        de=campo("de", "Criado de", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("ate", "Criado até", valores, erros, tipo="date", obrigatorio=False),
    )
    linhas = [
        h(
            '<tr><td><a href="/orcamentos/{id}">{cliente}</a></td><td>{criado}</td><td class="numero">{itens}</td><td class="numero">{desconto}</td><td class="numero">{liquido}</td><td>{estado}</td></tr>',
            id=o.id,
            cliente=nomes_clientes.get(o.cliente_id, "Cliente"),
            criado=f.data(o.criado_em),
            itens=len(o.itens),
            desconto=f.percentual(o.percentual_desconto),
            liquido=f.moeda(o.valor_liquido),
            estado=selo_orcamento(o.estado),
        )
        for o in orcamentos
    ]
    tabela_ = tabela(
        [("Cliente", ""), ("Criado em", ""), ("Itens", "numero"), ("Desconto", "numero"), ("Valor líquido", "numero"), ("Estado", "")],
        linhas,
        "Nenhum orçamento encontrado.",
    )
    conteudo = juntar(
        [
            cabecalho("Orçamentos", f"{len(orcamentos)} orçamento(s)", botao_link("/orcamentos/novo", "Novo orçamento")),
            h('<section class="cartao">{f}</section>', f=filtros),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela_),
        ]
    )
    return layout("Orçamentos", conteudo, ctx, "orcamentos", aviso)


def pagina_orcamento_formulario(ctx: Contexto, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros) -> Html:
    opcoes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    if not opcoes:
        aviso = caixa_de_aviso("info", "Cadastre um cliente antes de criar o orçamento.")
        acao = botao_link("/clientes/novo", "Novo cliente") if ctx.pode(Operacao.MANTER_CLIENTES) else Html("")
        return layout("Novo orçamento", juntar([cabecalho("Novo orçamento"), aviso, acao]), ctx, "orcamentos")
    formulario = h(
        """<form class="formulario" method="post" action="/orcamentos/novo" novalidate>
{protecao}{geral}
{cliente}
{condicao}
<div class="acoes"><button type="submit">Criar orçamento</button><a class="botao secundario" href="/orcamentos">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        cliente=selecao("cliente", "Cliente", opcoes, valores, erros, vazio="Escolha o cliente"),
        condicao=campo("condicao", "Condição de pagamento", valores, erros, obrigatorio=False, ajuda="Opcional. Por exemplo, 50% na aprovação e 50% na entrega."),
    )
    conteudo = juntar(
        [
            cabecalho("Novo orçamento", "O orçamento nasce em Rascunho. Depois você inclui os itens e o desconto."),
            h('<section class="cartao">{f}</section>', f=formulario),
        ]
    )
    return layout("Novo orçamento", conteudo, ctx, "orcamentos")


def _tabela_de_itens(ctx: Contexto, orcamento, editavel: bool) -> Html:
    linhas = []
    for item in orcamento.itens:
        acoes = Html("")
        if editavel:
            acoes = h(
                """<a class="botao pequeno secundario" href="/orcamentos/{o}/itens/{i}">Alterar</a>
<form class="em-linha" method="post" action="/orcamentos/{o}/itens/{i}/remocao">{p}<button class="pequeno secundario" type="submit">Remover</button></form>""",
                o=orcamento.id,
                i=item.id,
                p=protecao(ctx),
            )
        linhas.append(
            h(
                '<tr><td>{d}</td><td class="numero">{q}</td><td class="numero">{u}</td><td class="numero">{t}</td><td class="numero">{a}</td></tr>',
                d=item.descricao,
                q=f.numero(item.quantidade),
                u=f.moeda(item.valor_unitario),
                t=f.moeda(item.total),
                a=acoes,
            )
        )
    return tabela(
        [("Descrição", ""), ("Quantidade", "numero"), ("Valor unitário", "numero"), ("Total", "numero"), ("", "numero")],
        linhas,
        "Nenhum item ainda. Um orçamento só é enviado com ao menos um item (RB-24).",
    )


def pagina_orcamento(
    ctx: Contexto,
    orcamento,
    cliente_nome: str,
    nomes_usuarios: Dict[str, str],
    formulario: str,
    valores: Valores,
    erros: Erros,
    historico: Optional[list],
    aviso=None,
) -> Html:
    rascunho = orcamento.estado is EstadoOrcamento.RASCUNHO
    pode_conduzir = ctx.pode(Operacao.CONDUZIR_ORCAMENTO)
    editavel = rascunho and pode_conduzir
    erros_de = lambda nome: erros if formulario == nome else {}  # noqa: E731
    valores_de = lambda nome: valores if formulario == nome else {}  # noqa: E731
    acoes = []
    if pode_conduzir and orcamento.estado in (EstadoOrcamento.RASCUNHO, EstadoOrcamento.PENDENTE_DE_ALCADA, EstadoOrcamento.ENVIADO):
        acoes.append(botao_link(f"/orcamentos/{orcamento.id}/cancelamento", "Cancelar orçamento", "secundario"))
    motivo_envio = orcamento.motivo_para_nao_enviar()
    if orcamento.estado is EstadoOrcamento.RASCUNHO:
        prontidao = (
            caixa_de_aviso("sucesso", "Pronto para envio: tem itens e o desconto está liberado. O envio ao cliente chega com a Spec 005.")
            if motivo_envio is None
            else caixa_de_aviso("info", motivo_envio)
        )
    else:
        prontidao = Html("")
    elaborado = nomes_usuarios.get(orcamento.elaborado_por, "—")
    dados = h(
        """<dl class="dados">
<div><dt>Valor bruto</dt><dd>{bruto}</dd></div>
<div><dt>Desconto</dt><dd>{pct} ({desc})</dd></div>
<div><dt>Valor líquido</dt><dd><strong>{liquido}</strong></dd></div>
<div><dt>Condição de pagamento</dt><dd>{condicao}</dd></div>
<div><dt>Criado em</dt><dd>{criado}</dd></div>
<div><dt>Elaborado por</dt><dd>{elaborado}</dd></div>
{motivo}
</dl>""",
        bruto=f.moeda(orcamento.valor_bruto),
        pct=f.percentual(orcamento.percentual_desconto),
        desc=f.moeda(orcamento.valor_desconto),
        liquido=f.moeda(orcamento.valor_liquido),
        condicao=orcamento.condicao_pagamento or "—",
        criado=f.data(orcamento.criado_em),
        elaborado=elaborado,
        motivo=h("<div><dt>Motivo do cancelamento</dt><dd>{m}</dd></div>", m=orcamento.motivo_cancelamento) if orcamento.motivo_cancelamento else Html(""),
    )
    partes = [
        cabecalho(cliente_nome, "Orçamento", juntar(acoes)),
        h('<div class="selos-do-titulo">{s}</div>', s=selo_orcamento(orcamento.estado, grande=True)),
        prontidao,
        h('<section class="cartao">{d}</section>', d=dados),
    ]
    if orcamento.pendencia is not None:
        partes.append(_cartao_decisao(ctx, orcamento, nomes_usuarios, valores_de("decisao"), erros_de("decisao")))
    partes.append(h('<section class="cartao sem-borda-interna"><h2>Itens</h2>{t}</section>', t=_tabela_de_itens(ctx, orcamento, editavel)))
    if editavel:
        partes.append(
            h(
                """<section class="cartao" aria-labelledby="t-item"><h2 id="t-item">Incluir item</h2>
<form class="formulario" method="post" action="/orcamentos/{id}/itens" novalidate>
{protecao}{geral}
{descricao}
<div class="linha-campos">{quantidade}{valor}</div>
<div class="acoes"><button type="submit">Incluir item</button></div>
</form></section>""",
                id=orcamento.id,
                protecao=protecao(ctx),
                geral=erro_geral(erros_de("item")),
                descricao=campo("descricao", "Descrição", valores_de("item"), erros_de("item"), ajuda="Produto ou serviço."),
                quantidade=campo("quantidade", "Quantidade", valores_de("item"), erros_de("item"), ajuda="Por exemplo, 2 ou 1,5.", extra='inputmode="decimal"'),
                valor=campo("valor_unitario", "Valor unitário (R$)", valores_de("item"), erros_de("item"), ajuda="Por exemplo, 1.234,56.", extra='inputmode="decimal"'),
            )
        )
        valores_desconto = valores_de("desconto") or {"percentual": f.numero_para_campo(orcamento.percentual_desconto)}
        valores_condicao = valores_de("condicao") or {"condicao": orcamento.condicao_pagamento or ""}
        partes.append(
            h(
                """<div class="grade-2">
<section class="cartao" aria-labelledby="t-desconto"><h2 id="t-desconto">Desconto</h2>
<form class="formulario" method="post" action="/orcamentos/{id}/desconto" novalidate>
{protecao}{geral_d}{percentual}
<div class="acoes"><button type="submit">Aplicar desconto</button></div>
</form></section>
<section class="cartao" aria-labelledby="t-condicao"><h2 id="t-condicao">Condição de pagamento</h2>
<form class="formulario" method="post" action="/orcamentos/{id}/condicao" novalidate>
{protecao}{geral_c}{condicao}
<div class="acoes"><button class="secundario" type="submit">Salvar condição</button></div>
</form></section>
</div>""",
                id=orcamento.id,
                protecao=protecao(ctx),
                geral_d=erro_geral(erros_de("desconto")),
                geral_c=erro_geral(erros_de("condicao")),
                percentual=campo(
                    "percentual", "Desconto (%)", valores_desconto, erros_de("desconto"),
                    ajuda="Acima da alçada do seu perfil, o orçamento aguarda a decisão do Dono.", extra='inputmode="decimal"',
                ),
                condicao=campo("condicao", "Condição", valores_condicao, erros_de("condicao"), obrigatorio=False),
            )
        )
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout("Orçamento", juntar(partes), ctx, "orcamentos", aviso)


def _cartao_decisao(ctx: Contexto, orcamento, nomes_usuarios: Dict[str, str], valores: Valores, erros: Erros) -> Html:
    """UC-05, passo 1: o orçamento, o desconto solicitado e a alçada de quem o pediu."""
    pendencia = orcamento.pendencia
    resumo = h(
        "<p>{quem} pediu <strong>{pct}</strong> de desconto ({valor} sobre {bruto}). A alçada do perfil é de {alcada}.</p>",
        quem=nomes_usuarios.get(pendencia.solicitado_por, "Quem elaborou"),
        pct=f.percentual(pendencia.percentual_solicitado),
        valor=f.moeda(orcamento.desconto_para(pendencia.percentual_solicitado)),
        bruto=f.moeda(orcamento.valor_bruto),
        alcada=f.percentual(pendencia.alcada),
    )
    if not ctx.pode(Operacao.APROVAR_DESCONTO):
        return h(
            '<section class="cartao destaque-alerta"><h2>Desconto aguardando o Dono</h2>{r}<p class="secundario">Enquanto isso, os itens e o desconto não mudam.</p></section>',
            r=resumo,
        )
    formulario = h(
        """<form class="formulario" method="post" action="/orcamentos/{id}/decisao" novalidate>
{protecao}{geral}{percentual}
<div class="acoes"><button type="submit" name="acao" value="aprovar">Aprovar desconto</button>
<button class="secundario" type="submit" name="acao" value="rejeitar">Rejeitar e manter {atual}</button></div>
</form>""",
        id=orcamento.id,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        percentual=campo(
            "percentual", "Percentual aprovado (%)", valores, erros, obrigatorio=False,
            ajuda=f"Opcional. Vazio aprova os {f.percentual(pendencia.percentual_solicitado)} solicitados; dá para aprovar menos.",
            extra='inputmode="decimal"',
        ),
        atual=f.percentual(orcamento.percentual_desconto),
    )
    return h(
        '<section class="cartao destaque-alerta" aria-labelledby="t-decisao"><h2 id="t-decisao">Decidir o desconto</h2>{r}{f}</section>',
        r=resumo,
        f=formulario,
    )


def pagina_item_formulario(ctx: Contexto, orcamento, item, valores: Valores, erros: Erros) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="/orcamentos/{o}/itens/{i}" novalidate>
{protecao}{geral}
{descricao}
<div class="linha-campos">{quantidade}{valor}</div>
<div class="acoes"><button type="submit">Salvar item</button><a class="botao secundario" href="/orcamentos/{o}">Voltar</a></div>
</form>""",
        o=orcamento.id,
        i=item.id,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        descricao=campo("descricao", "Descrição", valores, erros),
        quantidade=campo("quantidade", "Quantidade", valores, erros, extra='inputmode="decimal"'),
        valor=campo("valor_unitario", "Valor unitário (R$)", valores, erros, extra='inputmode="decimal"'),
    )
    conteudo = juntar([cabecalho("Alterar item", item.descricao), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Alterar item", conteudo, ctx, "orcamentos")


# Empresa (OPEN-54)


def pagina_empresa(ctx: Contexto, empresa, visoes: Optional[list], clientes: Optional[int], valores: Valores, erros: Erros, aviso=None) -> Html:
    partes = [cabecalho(empresa.nome_fantasia or empresa.razao_social if empresa else "Empresa", "Dados da sua empresa no RemindMe.")]
    if empresa:
        partes.append(
            h(
                """<section class="cartao"><dl class="dados">
<div><dt>Razão social</dt><dd>{razao}</dd></div>
<div><dt>CNPJ</dt><dd>{cnpj}</dd></div>
<div><dt>Telefone</dt><dd>{telefone}</dd></div>
<div><dt>E-mail</dt><dd>{email}</dd></div>
<div><dt>Endereço</dt><dd>{endereco}</dd></div>
</dl></section>""",
                razao=empresa.razao_social,
                cnpj=f.documento(empresa.cnpj),
                telefone=f.contato(empresa.telefone) if empresa.telefone else "Não informado",
                email=empresa.email or "Não informado",
                endereco=empresa.endereco or "Não informado",
            )
        )
    elif not ctx.pode(Operacao.MANTER_EMPRESA):
        partes.append(caixa_de_aviso("info", "Os dados da empresa ainda não foram preenchidos. Peça ao Dono para preenchê-los."))
    indicadores = []
    if clientes is not None:
        indicadores.append(h('<div class="indicador"><div class="rotulo">Clientes</div><div class="numero">{n}</div></div>', n=clientes))
    if visoes is not None:
        em_aberto = [v for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)]
        indicadores.append(h('<div class="indicador"><div class="rotulo">Títulos em aberto</div><div class="numero">{n}</div></div>', n=len(em_aberto)))
        indicadores.append(
            h(
                '<div class="indicador"><div class="rotulo">A receber</div><div class="numero">{v}</div></div>',
                v=f.moeda(sum((v.saldo for v in em_aberto), Decimal("0.00"))),
            )
        )
    if indicadores:
        partes.append(h('<div class="indicadores">{i}</div>', i=juntar(indicadores)))
    if ctx.pode(Operacao.MANTER_EMPRESA):
        formulario = h(
            """<form class="formulario" method="post" action="/empresa" novalidate>
{protecao}{geral}
{razao}{fantasia}
<div class="linha-campos">{cnpj}{telefone}</div>
{email}{endereco}
<div class="acoes"><button type="submit">Salvar dados da empresa</button></div>
</form>""",
            protecao=protecao(ctx),
            geral=erro_geral(erros),
            razao=campo("razao_social", "Razão social", valores, erros),
            fantasia=campo("nome_fantasia", "Nome fantasia", valores, erros, obrigatorio=False),
            cnpj=campo("cnpj", "CNPJ", valores, erros, extra='inputmode="numeric"'),
            telefone=campo("telefone", "Telefone", valores, erros, tipo="text", obrigatorio=False, extra='inputmode="tel"'),
            email=campo("email", "E-mail", valores, erros, tipo="email", obrigatorio=False),
            endereco=campo("endereco", "Endereço", valores, erros, obrigatorio=False),
        )
        titulo = "Alterar dados" if empresa else "Preencher dados da empresa"
        partes.append(h('<section class="cartao"><h2>{t}</h2>{f}</section>', t=titulo, f=formulario))
    return layout("Empresa", juntar(partes), ctx, "empresa", aviso)


# Auditoria


def _descrever(registro: str) -> Tuple[str, Optional[str]]:
    partes = registro.split(", ")
    tipo, _, chave = partes[0].partition(" ")
    if tipo == "titulo":
        return ("Pagamento do título " if len(partes) > 1 else "Título ") + chave[:8], f"/titulos/{chave}"
    if tipo == "cliente":
        return "Cliente " + chave[:8], f"/clientes/{chave}"
    if tipo == "empresa":
        return "Dados da empresa", "/empresa"
    if tipo == "orcamento":
        return ("Item do orçamento " if len(partes) > 1 else "Orçamento ") + chave[:8], f"/orcamentos/{chave}"
    if tipo == "usuario":
        return "Usuário " + chave[:8], f"/usuarios/{chave}"
    return registro, "/permissoes" if registro == "permissões" else None


def _valor_exibido(campo_: Optional[str], texto: Optional[str]) -> str:
    if texto is None:
        return "—"
    if campo_ == "valor":
        lido = f.ler_valor(texto)
        return f.moeda(lido) if lido is not None else texto
    if campo_ in ("desconto", "desconto solicitado"):
        lido = f.ler_valor(texto)
        return f.percentual(lido) if lido is not None else texto
    if campo_ == "documento":
        return f.documento(texto)
    if campo_ == "contato":
        return f.contato(texto)
    return texto


def _mudanca(r) -> Html:
    if not r.campo:
        return Html("")
    return h(
        "<strong>{campo}</strong>: {anterior} → {novo}{motivo}",
        campo=r.campo,
        anterior=_valor_exibido(r.campo, r.valor_anterior),
        novo=_valor_exibido(r.campo, r.valor_novo),
        motivo=h(' <span class="secundario">(motivo: {m})</span>', m=r.motivo) if r.motivo else Html(""),
    )


def _item_do_historico(r) -> Html:
    return h(
        '<li><span class="quando">{quando}</span><span><strong>{quem}</strong>: {operacao}<br><span class="mudanca">{mudanca}</span></span></li>',
        quando=f.data_hora(r.data_hora),
        quem=r.responsavel,
        operacao=r.operacao,
        mudanca=_mudanca(r),
    )


def _cartao_historico(historico: list) -> Html:
    itens = [_item_do_historico(r) for r in historico]
    lista = h('<ul class="historico">{i}</ul>', i=juntar(itens)) if itens else h('<p class="vazio">{t}</p>', t="Sem histórico.")
    return h('<section class="cartao sem-borda-interna"><h2>Histórico</h2>{l}</section>', l=lista)


def pagina_auditoria(ctx: Contexto, registros: list, opcoes, valores: Valores, erros: Erros) -> Html:
    filtros = h(
        """<form class="filtros" method="get" action="/auditoria">
{quem}{operacao}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/auditoria">Limpar</a></div>
</form>""",
        quem=selecao("usuario", "Responsável", list(opcoes.responsaveis.items()), valores, erros, vazio="Todos", obrigatorio=False),
        operacao=selecao("operacao", "Operação", [(o, o) for o in opcoes.operacoes], valores, erros, vazio="Todas", obrigatorio=False),
        de=campo("de", "De", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("fim", "Até", valores, erros, tipo="date", obrigatorio=False),
    )
    linhas = []
    for r in registros:
        descricao, link = _descrever(r.registro_afetado)
        afetado = h('<a href="{l}">{d}</a>', l=link, d=descricao) if link else e(descricao)
        linhas.append(
            h(
                "<tr><td class=\"mono\">{quando}</td><td>{quem}</td><td>{operacao}</td><td>{afetado}</td><td>{mudanca}</td></tr>",
                quando=f.data_hora(r.data_hora),
                quem=r.responsavel,
                operacao=r.operacao,
                afetado=afetado,
                mudanca=_mudanca(r),
            )
        )
    filtro_registro = valores.get("registro", "")
    subtitulo = f"{len(registros)} registro(s), em ordem cronológica. Os registros não podem ser alterados nem excluídos."
    partes = [
        cabecalho("Auditoria", subtitulo),
        erro_geral(erros),
        h('<section class="cartao">{f}</section>', f=filtros),
    ]
    if filtro_registro:
        partes.append(caixa_de_aviso("info", "Mostrando só o histórico de um registro."))
    partes.append(
        h(
            '<section class="cartao sem-borda-interna">{t}</section>',
            t=tabela([("Data e hora", ""), ("Responsável", ""), ("Operação", ""), ("Registro", ""), ("Alteração", "")], linhas, "Nenhum registro para os filtros escolhidos."),
        )
    )
    return layout("Auditoria", juntar(partes), ctx, "auditoria")


# Usuários e permissões


def _selo_situacao(usuario: Usuario) -> Html:
    return Html('<span class="selo ativo">Ativo</span>') if usuario.ativo else Html('<span class="selo inativo">Inativo</span>')


def pagina_usuarios(ctx: Contexto, usuarios: List[Usuario], aviso=None) -> Html:
    linhas = [
        h(
            '<tr><td><a href="/usuarios/{id}">{nome}</a></td><td>{email}</td><td>{perfil}</td><td>{situacao}</td></tr>',
            id=u.id,
            nome=u.nome,
            email=u.email,
            perfil=u.perfil.value,
            situacao=_selo_situacao(u),
        )
        for u in usuarios
    ]
    conteudo = juntar(
        [
            cabecalho("Usuários", "Cada usuário tem exatamente um perfil.", botao_link("/usuarios/novo", "Novo usuário")),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela([("Nome", ""), ("E-mail", ""), ("Perfil", ""), ("Situação", "")], linhas, "Nenhum usuário.")),
        ]
    )
    return layout("Usuários", conteudo, ctx, "usuarios", aviso)


def pagina_usuario_formulario(ctx: Contexto, valores: Valores, erros: Erros) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="/usuarios/novo" novalidate>
{protecao}{geral}
{nome}
<div class="linha-campos">{email}{perfil}</div>
{senha}
<div class="acoes"><button type="submit">Cadastrar usuário</button><a class="botao secundario" href="/usuarios">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        nome=campo("nome", "Nome", valores, erros),
        email=campo("email", "E-mail", valores, erros, tipo="email"),
        perfil=selecao("perfil", "Perfil", [(p.name, p.value) for p in PERFIS_DE_USUARIO], valores, erros, vazio="Escolha o perfil"),
        senha=campo("senha", "Senha provisória", valores, erros, tipo="password", ajuda="Pelo menos 8 caracteres. Informe-a ao usuário.", extra='autocomplete="new-password"'),
    )
    conteudo = juntar([cabecalho("Novo usuário"), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Novo usuário", conteudo, ctx, "usuarios")


def pagina_usuario(ctx: Contexto, usuario: Usuario, valores: Valores, erros: Erros, aviso=None) -> Html:
    dados = h(
        '<dl class="dados"><div><dt>E-mail</dt><dd>{email}</dd></div><div><dt>Perfil</dt><dd>{perfil}</dd></div><div><dt>Situação</dt><dd>{situacao}</dd></div></dl>',
        email=usuario.email,
        perfil=usuario.perfil.value,
        situacao=_selo_situacao(usuario),
    )
    partes = [cabecalho(usuario.nome, "Usuário"), erro_geral(erros), h('<section class="cartao">{d}</section>', d=dados)]
    if usuario.ativo:
        partes.append(
            h(
                """<div class="grade-2">
<section class="cartao"><h2>Alterar perfil</h2>
<form class="formulario" method="post" action="/usuarios/{id}/perfil" novalidate>{protecao}{perfil}
<div class="acoes"><button type="submit">Alterar perfil</button></div></form></section>
<section class="cartao"><h2>Inativar usuário</h2><p class="secundario">O usuário perde o acesso na hora. O histórico dele é preservado.</p>
<form method="post" action="/usuarios/{id}/inativacao">{protecao}<button class="perigo" type="submit">Inativar usuário</button></form></section>
</div>""",
                id=usuario.id,
                protecao=protecao(ctx),
                perfil=selecao("perfil", "Novo perfil", [(p.name, p.value) for p in PERFIS_DE_USUARIO], valores or {"perfil": usuario.perfil.name}, erros),
            )
        )
    else:
        partes.append(
            h(
                """<section class="cartao"><h2>Ativar usuário</h2><p class="secundario">Libera a entrada com o e-mail e a senha que a pessoa escolheu ao criar a conta.</p>
<form method="post" action="/usuarios/{id}/ativacao">{protecao}<button type="submit">Ativar usuário</button></form></section>""",
                id=usuario.id,
                protecao=protecao(ctx),
            )
        )
    partes.append(h('<p><a href="/auditoria?registro=usuario+{id}">Histórico deste usuário</a></p>', id=usuario.id))
    return layout(usuario.nome, juntar(partes), ctx, "usuarios", aviso)


def pagina_permissoes(ctx: Contexto, linhas_da_matriz: list, aviso=None) -> Html:
    cabecalhos = h("<th scope=\"col\">Operação</th>{p}", p=juntar(h('<th scope="col">{p}</th>', p=perfil.value) for perfil in Perfil))
    linhas = []
    for linha in linhas_da_matriz:
        celulas = []
        for perfil in Perfil:
            celula = linha.celulas[perfil]
            texto = "Permitido" if celula.permitido else "Negado"
            classe = "sim" if celula.permitido else "nao"
            if celula.fixada is not None:
                celulas.append(
                    h('<td><span class="celula {c} fixa" title="{m}">🔒 {t}</span></td>', c=classe, m=celula.fixada.motivo, t=texto)
                )
            else:
                celulas.append(
                    h(
                        """<td><form method="post" action="/permissoes">{protecao}<input type="hidden" name="perfil" value="{perfil}"><input type="hidden" name="operacao" value="{operacao}"><input type="hidden" name="acao" value="{acao}"><button class="{c}" type="submit" title="{dica}">{t}</button></form></td>""",
                        protecao=protecao(ctx),
                        perfil=perfil.name,
                        operacao=linha.operacao.name,
                        acao="retirar" if celula.permitido else "conceder",
                        c=classe,
                        dica=("Retirar" if celula.permitido else "Conceder") + f" a permissão de {perfil.value}",
                        t=texto,
                    )
                )
        linhas.append(h("<tr><th scope=\"row\">{o}</th>{c}</tr>", o=linha.operacao.value, c=juntar(celulas)))
    conteudo = juntar(
        [
            cabecalho("Permissões por perfil", "Clique em uma célula para conceder ou retirar. 🔒 indica permissão fixada por regra de negócio, que não muda por configuração."),
            h('<section class="cartao sem-borda-interna"><div class="tabela"><table class="matriz"><thead><tr>{c}</tr></thead><tbody>{l}</tbody></table></div></section>', c=cabecalhos, l=juntar(linhas)),
        ]
    )
    return layout("Permissões", conteudo, ctx, "permissoes", aviso)


# Erros


def pagina_erro(codigo: int, titulo: str, mensagem: str, correlacao: Optional[str] = None, com_volta: bool = True) -> Html:
    corpo = h(
        """<main class="erro-pagina" id="conteudo">
<div class="codigo">{codigo}</div>
<h1>{titulo}</h1>
<p>{mensagem}</p>
{correlacao}
{volta}
</main>""",
        codigo=codigo,
        titulo=titulo,
        mensagem=mensagem,
        correlacao=h('<p class="secundario">Identificador para o suporte: <span class="mono">{c}</span></p>', c=correlacao) if correlacao else Html(""),
        volta=Html('<p><a class="botao secundario" href="/painel">Voltar ao painel</a></p>') if com_volta else Html(""),
    )
    return _documento_html(titulo, corpo)
