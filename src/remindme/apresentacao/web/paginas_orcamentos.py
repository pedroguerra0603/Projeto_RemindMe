"""Páginas de orçamentos: itens, desconto, decisão, envio e resposta do cliente (Specs 004 e 005). Só montam o que os serviços devolvem (INV-1)."""

from typing import Dict, Optional

from remindme.aplicacao.modelos_de_mensagem import numero_do_orcamento
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import h, Html, juntar
from remindme.apresentacao.web.paginas import (
    botao_link,
    cabecalho,
    caixa_de_aviso,
    campo,
    _cartao_historico,
    Contexto,
    erro_geral,
    Erros,
    layout,
    protecao,
    selecao,
    tabela,
    Valores,
)
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento


CLASSE_DO_ESTADO_DO_ORCAMENTO = {
    EstadoOrcamento.RASCUNHO: "aberto",
    EstadoOrcamento.PENDENTE_DE_ALCADA: "proximo",
    EstadoOrcamento.ENVIADO: "aberto",
    EstadoOrcamento.APROVADO: "baixado",
    EstadoOrcamento.CONVERTIDO: "baixado",
    EstadoOrcamento.REJEITADO: "cancelado",
    EstadoOrcamento.CANCELADO: "cancelado",
}


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
    mensagens: Optional[list] = None,
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
            _cartao_envio(ctx, orcamento, erros_de("envio"))
            if motivo_envio is None and pode_conduzir
            else caixa_de_aviso("sucesso", "Pronto para envio ao cliente.")
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
<div><dt>Prazo para pagamento</dt><dd>{prazo}</dd></div>
<div><dt>Criado em</dt><dd>{criado}</dd></div>
<div><dt>Elaborado por</dt><dd>{elaborado}</dd></div>
{andamento}
{motivo}
</dl>""",
        bruto=f.moeda(orcamento.valor_bruto),
        pct=f.percentual(orcamento.percentual_desconto),
        desc=f.moeda(orcamento.valor_desconto),
        liquido=f.moeda(orcamento.valor_liquido),
        condicao=orcamento.condicao_pagamento or "—",
        prazo=_prazo(orcamento.prazo_pagamento_dias),
        criado=f.data(orcamento.criado_em),
        elaborado=elaborado,
        andamento=_andamento_do_orcamento(orcamento),
        motivo=h("<div><dt>Motivo do cancelamento</dt><dd>{m}</dd></div>", m=orcamento.motivo_cancelamento) if orcamento.motivo_cancelamento else Html(""),
    )
    partes = [
        cabecalho(cliente_nome, f"Orçamento nº {numero_do_orcamento(orcamento.id)}", juntar(acoes)),
        h('<div class="selos-do-titulo">{s}</div>', s=selo_orcamento(orcamento.estado, grande=True)),
        prontidao,
        h('<section class="cartao">{d}</section>', d=dados),
    ]
    if orcamento.estado is EstadoOrcamento.ENVIADO and pode_conduzir:
        valores_resposta = valores_de("resposta") or {"data": ctx.hoje.isoformat()}
        partes.append(_cartao_resposta_do_cliente(ctx, orcamento, valores_resposta, erros_de("resposta")))
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
        valores_condicao = valores_de("condicao") or {
            "condicao": orcamento.condicao_pagamento or "",
            "prazo": "" if orcamento.prazo_pagamento_dias is None else str(orcamento.prazo_pagamento_dias),
        }
        partes.append(
            h(
                """<div class="grade-2">
<section class="cartao" aria-labelledby="t-desconto"><h2 id="t-desconto">Desconto</h2>
<form class="formulario" method="post" action="/orcamentos/{id}/desconto" novalidate>
{protecao}{geral_d}{percentual}
<div class="acoes"><button type="submit">Aplicar desconto</button></div>
</form></section>
<section class="cartao" aria-labelledby="t-condicao"><h2 id="t-condicao">Pagamento</h2>
<form class="formulario" method="post" action="/orcamentos/{id}/condicao" novalidate>
{protecao}{geral_c}{prazo}{condicao}
<div class="acoes"><button class="secundario" type="submit">Salvar pagamento</button></div>
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
                prazo=campo(
                    "prazo", "Prazo para pagamento (dias)", valores_condicao, erros_de("condicao"),
                    ajuda="Contado da aprovação do cliente; 0 é à vista. Obrigatório para enviar.", extra='inputmode="numeric"',
                ),
                condicao=campo("condicao", "Condição", valores_condicao, erros_de("condicao"), obrigatorio=False),
            )
        )
    if mensagens:
        partes.append(_cartao_envios(mensagens))
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout("Orçamento", juntar(partes), ctx, "orcamentos", aviso)


def _prazo(dias: Optional[int]) -> str:
    if dias is None:
        return "—"
    if dias == 0:
        return "À vista, na aprovação"
    return f"{dias} {'dia' if dias == 1 else 'dias'} após a aprovação"


def _andamento_do_orcamento(orcamento) -> Html:
    """Spec 005: envio, decisão do cliente e o título gerado."""
    partes = []
    if orcamento.enviado_em:
        partes.append(h("<div><dt>Enviado ao cliente em</dt><dd>{d}</dd></div>", d=f.data(orcamento.enviado_em)))
    if orcamento.decidido_em:
        partes.append(h("<div><dt>Decisão do cliente em</dt><dd>{d}</dd></div>", d=f.data(orcamento.decidido_em)))
    if orcamento.motivo_rejeicao:
        partes.append(h("<div><dt>Motivo da rejeição</dt><dd>{m}</dd></div>", m=orcamento.motivo_rejeicao))
    if orcamento.titulo_id:
        partes.append(
            h('<div><dt>Título gerado</dt><dd><a href="/titulos/{t}">Ver o título</a></dd></div>', t=orcamento.titulo_id)
        )
    return juntar(partes)


def _cartao_envio(ctx: Contexto, orcamento, erros: Erros) -> Html:
    """RF-08: pronto para sair de Rascunho."""
    return h(
        """<section class="cartao destaque-sucesso" aria-labelledby="t-envio"><h2 id="t-envio">Pronto para envio</h2>
<p>O cliente recebe os itens, o valor líquido e o prazo para pagamento pelo canal de notificação.</p>
<form class="formulario" method="post" action="/orcamentos/{id}/envio">{protecao}{geral}
<div class="acoes"><button type="submit">Enviar ao cliente</button></div></form></section>""",
        id=orcamento.id,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
    )


def _cartao_resposta_do_cliente(ctx: Contexto, orcamento, valores: Valores, erros: Erros) -> Html:
    """RF-09 (OPEN-57): quem fala com o cliente registra a resposta dele."""
    return h(
        """<section class="cartao destaque-alerta" aria-labelledby="t-resposta"><h2 id="t-resposta">Registrar decisão do cliente</h2>
<p>Na aprovação, o título é gerado com vencimento na data da decisão mais o prazo ({prazo}).</p>
<form class="formulario" method="post" action="/orcamentos/{id}/resposta-do-cliente" novalidate>
{protecao}{geral}
<div class="linha-campos">{data}{motivo}</div>
<div class="acoes"><button type="submit" name="decisao" value="aprovar">Registrar aprovação</button>
<button class="secundario" type="submit" name="decisao" value="rejeitar">Registrar rejeição</button></div>
</form></section>""",
        id=orcamento.id,
        prazo=_prazo(orcamento.prazo_pagamento_dias).lower(),
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        data=campo("data", "Data da decisão", valores, erros, tipo="date", ajuda="O dia em que o cliente respondeu."),
        motivo=campo("motivo", "Motivo", valores, erros, obrigatorio=False, ajuda="Opcional, na rejeição."),
    )


def _cartao_envios(mensagens: list) -> Html:
    """O que o canal de notificação registrou para este orçamento (ADR-002)."""
    itens = juntar(
        h(
            '<details><summary>{quando} · {contato} · <span class="selo {classe}">{resultado}</span></summary>'
            '<pre class="mensagem">{texto}</pre></details>',
            quando=f.data_hora(m.enviada_em),
            contato=m.contato,
            classe="baixado" if m.resultado == "enviada" else "vencido",
            resultado="Enviada" if m.resultado == "enviada" else "Falhou",
            texto=m.texto,
        )
        for m in mensagens
    )
    return h('<section class="cartao" aria-labelledby="t-envios"><h2 id="t-envios">Envio ao cliente</h2>{i}</section>', i=itens)


def _origem_do_titulo(ctx: Contexto, titulo) -> Html:
    """O link para o orçamento só aparece para quem pode abri-lo (o Contador vê títulos, mas não orçamentos)."""
    if titulo.orcamento_id:
        numero = numero_do_orcamento(titulo.orcamento_id)
        if ctx.pode(Operacao.CONDUZIR_ORCAMENTO):
            return h('<a href="/orcamentos/{o}">Gerado do orçamento nº {n}</a>', o=titulo.orcamento_id, n=numero)
        return h("Gerado do orçamento nº {n}", n=numero)
    return h("{o}", o="Cadastro manual" if titulo.origem == "manual" else titulo.origem)


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
