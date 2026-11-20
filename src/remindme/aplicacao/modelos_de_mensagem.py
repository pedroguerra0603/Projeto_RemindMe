"""Textos que o canal de notificação entrega: ao cliente (Spec 005) e os alertas de obrigação aos usuários (Spec 010).

É o único ponto que monta texto enviado (RB-27, INV-4; Spec 010, INV-6): nada de texto livre além dos dados do
orçamento, da obrigação, do destinatário e da empresa. Os valores são formatados aqui, porque a aplicação não usa a apresentação.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from remindme.dominio.cliente import Cliente
from remindme.dominio.empresa import Empresa
from remindme.dominio.obrigacao import Obrigacao
from remindme.dominio.orcamento import Orcamento
from remindme.dominio.usuario import Usuario

SEM_EMPRESA = "Nossa empresa"


def numero_do_orcamento(orcamento_id: str) -> str:
    """O número que o cliente e as telas usam para o orçamento."""
    return orcamento_id[:8].upper()


def mensagem_de_orcamento(empresa: Optional[Empresa], cliente: Cliente, orcamento: Orcamento) -> Tuple[str, str]:
    """Assunto e texto do orçamento enviado ao cliente (RF-08)."""
    nome = _nome_da_empresa(empresa)
    numero = numero_do_orcamento(orcamento.id)
    linhas = [f"Olá, {cliente.nome}.", "", f"{nome} envia o orçamento nº {numero}:", ""]
    for item in orcamento.itens:
        linhas.append(
            f"- {item.descricao}: {_numero(item.quantidade)} × {_reais(item.valor_unitario)} = {_reais(item.total)}"
        )
    linhas += ["", f"Valor bruto: {_reais(orcamento.valor_bruto)}"]
    if orcamento.percentual_desconto > 0:
        linhas.append(f"Desconto: {_numero(orcamento.percentual_desconto)}% ({_reais(orcamento.valor_desconto)})")
    linhas.append(f"Valor líquido: {_reais(orcamento.valor_liquido)}")
    linhas.append(f"Prazo para pagamento: {_prazo(orcamento.prazo_pagamento_dias)}")
    if orcamento.condicao_pagamento:
        linhas.append(f"Condição de pagamento: {orcamento.condicao_pagamento}")
    linhas += ["", "Para aprovar ou recusar, responda a esta mensagem."]
    return f"Orçamento nº {numero} — {nome}", "\n".join(linhas)


def mensagem_de_aviso_de_obrigacao(
    empresa: Optional[Empresa], usuario: Usuario, obrigacao: Obrigacao, hoje: date
) -> Tuple[str, str]:
    """Aviso ao responsável antes do prazo (RF-44, RB-07)."""
    prazo = _data(obrigacao.prazo)
    dias = (obrigacao.prazo - hoje).days
    quando = "hoje" if dias == 0 else "amanhã" if dias == 1 else f"daqui a {dias} dias"
    linhas = [f"Olá, {usuario.nome}.", "", f"A obrigação {obrigacao.nome} ({obrigacao.tipo.value}) vence em {prazo}, {quando}."]
    if obrigacao.exige_evidencia:
        linhas.append("Ao registrar o cumprimento, anexe a evidência.")
    linhas += ["", f"{_nome_da_empresa(empresa)} · RemindMe"]
    return f"Obrigação a vencer: {obrigacao.nome} em {prazo}", "\n".join(linhas)


def mensagem_de_escalonamento(
    empresa: Optional[Empresa], usuario: Usuario, obrigacao: Obrigacao, responsavel: Optional[Usuario], hoje: date
) -> Tuple[str, str]:
    """Alerta escalonado ao Dono (RF-49, RB-16)."""
    dias = (hoje - obrigacao.prazo).days
    linhas = [
        f"Olá, {usuario.nome}.",
        "",
        f"A obrigação {obrigacao.nome} ({obrigacao.tipo.value}) venceu em {_data(obrigacao.prazo)} "
        f"e está Atrasada há {dias} {'dia' if dias == 1 else 'dias'}.",
        f"Responsável: {responsavel.nome if responsavel else 'não definido'}.",
        "",
        f"{_nome_da_empresa(empresa)} · RemindMe",
    ]
    return f"Obrigação atrasada: {obrigacao.nome}", "\n".join(linhas)


def _data(data: date) -> str:
    return data.strftime("%d/%m/%Y")


def _nome_da_empresa(empresa: Optional[Empresa]) -> str:
    if empresa is None:
        return SEM_EMPRESA
    return empresa.nome_fantasia or empresa.razao_social or SEM_EMPRESA


def _prazo(dias: Optional[int]) -> str:
    if not dias:
        return "à vista, na aprovação"
    return f"{dias} {'dia' if dias == 1 else 'dias'} a partir da aprovação"


def _numero(valor: Decimal) -> str:
    """Sem zeros à direita e com vírgula: 1,5 e 2."""
    texto = f"{valor:f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _reais(valor: Decimal) -> str:
    """R$ 1.234,56."""
    texto = f"{valor.quantize(Decimal('0.01')):,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")
