"""Caixa de saída (Spec 005): o que o canal de notificação simulado registrou para cada cliente."""

from typing import Dict

from remindme.aplicacao.modelos_de_mensagem import numero_do_orcamento
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import Contexto, cabecalho, layout, tabela


def _origem(origem: str) -> Html:
    tipo, _, registro = origem.partition(" ")
    if tipo == "orcamento" and registro:
        return h('<a href="/orcamentos/{o}">Orçamento nº {n}</a>', o=registro, n=numero_do_orcamento(registro))
    return h("{o}", o=origem)


def pagina_mensagens(ctx: Contexto, mensagens: list, nomes_clientes: Dict[str, str]) -> Html:
    linhas = [
        h(
            """<tr><td>{quando}</td><td>{cliente}</td><td>{contato}</td><td>{origem}</td>
<td><span class="selo {classe}">{resultado}</span></td>
<td><details><summary>{assunto}</summary><pre class="mensagem">{texto}</pre></details></td></tr>""",
            quando=f.data_hora(m.enviada_em),
            cliente=nomes_clientes.get(m.cliente_id, "Cliente"),
            contato=f.contato(m.contato),
            origem=_origem(m.origem),
            classe="baixado" if m.resultado == "enviada" else "vencido",
            resultado="Enviada" if m.resultado == "enviada" else "Falhou",
            assunto=m.assunto,
            texto=m.texto,
        )
        for m in mensagens
    ]
    conteudo = juntar(
        [
            cabecalho(
                "Mensagens enviadas",
                "O canal de notificação é simulado: as mensagens ficam registradas aqui em vez de chegar ao cliente.",
            ),
            h(
                '<section class="cartao sem-borda-interna">{t}</section>',
                t=tabela(
                    [("Data e hora", ""), ("Cliente", ""), ("Contato", ""), ("Origem", ""), ("Resultado", ""), ("Mensagem", "")],
                    linhas,
                    "Nenhuma mensagem enviada ainda.",
                ),
            ),
        ]
    )
    return layout("Mensagens enviadas", conteudo, ctx, "mensagens")
