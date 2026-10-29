"""Escape de HTML (ADR-006, INV-4): todo valor exibido passa por `e`; só o texto de `Html` é confiável."""

import html


class Html(str):
    """Trecho de HTML já seguro. Concatenar com texto comum exige passar o texto por `e`."""


def e(conteudo: object) -> Html:
    if isinstance(conteudo, Html):
        return conteudo
    return Html(html.escape("" if conteudo is None else str(conteudo), quote=True))


def h(modelo: str, **valores: object) -> Html:
    """Preenche o modelo, que é confiável, com valores escapados."""
    return Html(modelo.format(**{nome: e(valor) for nome, valor in valores.items()}))


def juntar(partes) -> Html:
    return Html("".join(e(parte) for parte in partes))
