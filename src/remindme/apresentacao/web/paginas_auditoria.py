"""Consulta de auditoria e histórico de cada registro (Specs 013 e 017). Só monta o que os serviços devolvem (INV-1)."""

import re
from decimal import Decimal, InvalidOperation
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
from remindme.dominio.operacoes import Operacao

# Textos compostos que a auditoria guarda no formato canônico (servico_orcamentos): exibidos no formato brasileiro.
_ITEM = re.compile(r"(.*): (\S+) × (\S+)")
_DECISAO = re.compile(r"aprovado (\S+)% de (\S+)% solicitados")


def _descrever(registro: str, administra: bool = False) -> Tuple[str, Optional[str]]:
    """Descrição e link do registro afetado. Usuários e permissões só ganham link para quem pode abrir essas páginas (RF-65)."""
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
        return "Usuário " + chave[:8], f"/usuarios/{chave}" if administra else None
    if tipo == "obrigacao":
        return ("Evidência da obrigação " if len(partes) > 1 else "Obrigação ") + chave[:8], f"/obrigacoes/{chave}"
    return registro, "/permissoes" if registro == "permissões" and administra else None


def _canonico(texto: str) -> Optional[Decimal]:
    """Lê o número como a auditoria o guarda (`str` de `Decimal`: "1800.00", "1.250"), e não como o usuário digita."""
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None
    return numero if numero.is_finite() else None


def _valor_exibido(campo_: Optional[str], texto: Optional[str]) -> str:
    if texto is None:
        return "—"
    if campo_ == "valor":
        lido = _canonico(texto)
        return f.moeda(lido) if lido is not None else texto
    if campo_ in ("desconto", "desconto solicitado"):
        lido = _canonico(texto)
        return f.percentual(lido) if lido is not None else texto
    if campo_ == "item":
        item = _ITEM.fullmatch(texto)
        quantidade, unitario = (_canonico(item.group(2)), _canonico(item.group(3))) if item else (None, None)
        if quantidade is not None and unitario is not None:
            return f"{item.group(1)}: {f.numero(quantidade)} × {f.moeda(unitario)}"
        return texto
    if campo_ == "decisão do desconto":
        decisao = _DECISAO.fullmatch(texto)
        aprovado, solicitado = (_canonico(decisao.group(1)), _canonico(decisao.group(2))) if decisao else (None, None)
        if aprovado is not None and solicitado is not None:
            return f"aprovado {f.percentual(aprovado)} de {f.percentual(solicitado)} solicitados"
        return texto
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
    administra = ctx.pode(Operacao.ADMINISTRAR_USUARIOS)
    for r in registros:
        descricao, link = _descrever(r.registro_afetado, administra)
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
