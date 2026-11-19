"""Consulta de auditoria e histórico de cada registro (Specs 013 e 017). Só monta o que os serviços devolvem (INV-1)."""

from typing import Optional, Tuple

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, e, h, juntar
from remindme.apresentacao.web.paginas import (
    Contexto,
    Erros,
    Valores,
    cabecalho,
    caixa_de_aviso,
    campo,
    erro_geral,
    layout,
    selecao,
    tabela,
)


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
    if tipo == "fornecedor":
        return "Fornecedor " + chave[:8], f"/fornecedores/{chave}"
    if tipo == "conta_pagar":
        return ("Pagamento da conta " if len(partes) > 1 else "Conta a pagar ") + chave[:8], f"/contas-a-pagar/{chave}"
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
