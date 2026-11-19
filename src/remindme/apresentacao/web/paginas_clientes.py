"""Páginas de clientes (Specs 003 e 017). Só montam o que os serviços devolvem (INV-1)."""

from decimal import Decimal
from typing import Optional

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import h, Html, juntar
from remindme.apresentacao.web.paginas import (
    botao_link,
    cabecalho,
    campo,
    _cartao_historico,
    Contexto,
    erro_geral,
    Erros,
    layout,
    protecao,
    tabela,
    Valores,
)
from remindme.apresentacao.web.paginas_titulos import _tabela_de_titulos
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo


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
