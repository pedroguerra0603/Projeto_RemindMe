"""Base das páginas HTML da interface web (Spec 017): contexto, estrutura, campos e páginas comuns.

As páginas de cada módulo ficam em `paginas_<módulo>.py` e usam os componentes daqui. Só montam o que os serviços
devolvem; nenhuma regra aqui (INV-1).
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from remindme.apresentacao.web.html import Html, h, juntar
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Usuario

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
    ("mensagens", "/mensagens", "Mensagens enviadas", "✉", Operacao.CONSULTAR_MENSAGENS),
    ("clientes", "/clientes", "Clientes", "◉", Operacao.CONSULTAR_CLIENTES),
    ("contas", "/contas-a-pagar", "Contas a pagar", "▥", Operacao.CONSULTAR_CONTAS_PAGAR),
    ("obrigacoes", "/obrigacoes", "Obrigações", "◷", Operacao.GERENCIAR_OBRIGACOES),
    ("fornecedores", "/fornecedores", "Fornecedores", "◍", Operacao.CONSULTAR_FORNECEDORES),
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
    <a class="botao discreto" href="/trocar-senha">Trocar senha</a>
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


# Páginas comuns: motivo de uma operação e erro


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
