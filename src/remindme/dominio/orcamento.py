"""Orçamento, itens e desconto (Spec 004). Regras RB-15 e RB-24; transições em `docs/uml/estados.md`.

Valores: OPEN-20 e OPEN-24 (duas casas, até 15 dígitos inteiros). Quantidade, percentual e arredondamento:
OPEN-51. Alçada padrão: OPEN-49.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Dict, List, Optional

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")
CEM = Decimal(100)
LIMITE_VALOR = Decimal(10) ** 15
TAMANHO_MAXIMO_TEXTO = 200

# OPEN-49 (provisória até a Spec 014, que torna a alçada configurável, RF-14): percentual máximo de desconto
# sem aprovação. Perfil fora da tabela não concede desconto. O Dono não tem limite (RB-15).
ALCADA_PADRAO: Dict[Perfil, Decimal] = {Perfil.OPERADOR_FINANCEIRO: Decimal("10.00")}


def alcada_do_perfil(perfil: Perfil) -> Optional[Decimal]:
    """RB-15: o percentual máximo do perfil; None quer dizer sem limite (Dono)."""
    if perfil is Perfil.DONO:
        return None
    return ALCADA_PADRAO.get(perfil, ZERO)


class EstadoOrcamento(Enum):
    RASCUNHO = "Rascunho"
    PENDENTE_DE_ALCADA = "Pendente de Alçada"
    ENVIADO = "Enviado"
    APROVADO = "Aprovado"
    REJEITADO = "Rejeitado"
    CONVERTIDO = "Convertido"
    CANCELADO = "Cancelado"


ESTADOS_QUE_ACEITAM_CANCELAMENTO = (
    EstadoOrcamento.RASCUNHO,
    EstadoOrcamento.PENDENTE_DE_ALCADA,
    EstadoOrcamento.ENVIADO,
)


@dataclass(frozen=True)
class ItemOrcamento:
    id: str
    descricao: str
    quantidade: Decimal
    valor_unitario: Decimal

    @property
    def total(self) -> Decimal:
        """Quantidade × valor unitário, arredondado ao centavo, metade para cima (OPEN-51)."""
        return _ao_centavo(self.quantidade * self.valor_unitario)


@dataclass(frozen=True)
class PendenciaDesconto:
    """RF-16: o desconto pedido acima da alçada, à espera da decisão do Dono."""

    percentual_solicitado: Decimal
    solicitado_por: str
    alcada: Decimal


@dataclass(frozen=True)
class AprovacaoDesconto:
    """RF-17: responsável, decisão e data. A2: o solicitado e o aprovado (RF-18)."""

    aprovado: bool
    percentual_solicitado: Decimal
    percentual_aprovado: Optional[Decimal]
    decidido_por: str
    data: date


@dataclass
class Orcamento:
    id: str
    cliente_id: str
    elaborado_por: str
    criado_em: date
    estado: EstadoOrcamento
    condicao_pagamento: Optional[str] = None
    percentual_desconto: Decimal = ZERO
    itens: List[ItemOrcamento] = field(default_factory=list)
    pendencia: Optional[PendenciaDesconto] = None
    decisoes: List[AprovacaoDesconto] = field(default_factory=list)
    motivo_cancelamento: Optional[str] = None

    @classmethod
    def criar(
        cls, id: str, cliente_id: str, elaborado_por: str, criado_em: date, condicao_pagamento: object = None
    ) -> "Orcamento":
        """RF-06: nasce em Rascunho, sem itens e sem desconto."""
        return cls(
            id=id,
            cliente_id=cliente_id,
            elaborado_por=elaborado_por,
            criado_em=criado_em,
            estado=EstadoOrcamento.RASCUNHO,
            condicao_pagamento=_condicao(condicao_pagamento),
        )

    # Valores (RF-07)

    @property
    def valor_bruto(self) -> Decimal:
        return sum((item.total for item in self.itens), ZERO)

    @property
    def valor_desconto(self) -> Decimal:
        return self.desconto_para(self.percentual_desconto)

    def desconto_para(self, percentual: Decimal) -> Decimal:
        """Valor bruto × percentual ÷ 100, ao centavo (OPEN-51). Também mostra quanto vale um pedido pendente."""
        return _ao_centavo((self.valor_bruto * percentual).scaleb(-2))

    @property
    def valor_liquido(self) -> Decimal:
        return self.valor_bruto - self.valor_desconto

    # Itens (RF-07)

    def incluir_item(self, item_id: str, descricao: object, quantidade: object, valor_unitario: object) -> ItemOrcamento:
        self._exigir_rascunho("incluir item")
        item = _item(item_id, descricao, quantidade, valor_unitario)
        self._aplicar_itens(self.itens + [item])
        return item

    def alterar_item(self, item_id: str, descricao: object, quantidade: object, valor_unitario: object) -> ItemOrcamento:
        self._exigir_rascunho("alterar item")
        posicao = self._posicao(item_id)
        item = _item(item_id, descricao, quantidade, valor_unitario)
        self._aplicar_itens(self.itens[:posicao] + [item] + self.itens[posicao + 1 :])
        return item

    def remover_item(self, item_id: str) -> ItemOrcamento:
        self._exigir_rascunho("remover item")
        return self.itens.pop(self._posicao(item_id))

    def item(self, item_id: str) -> ItemOrcamento:
        return self.itens[self._posicao(item_id)]

    def alterar_condicao(self, condicao_pagamento: object) -> None:
        self._exigir_rascunho("alterar a condição de pagamento")
        self.condicao_pagamento = _condicao(condicao_pagamento)

    # Desconto e alçada (RB-15)

    def informar_desconto(self, percentual: object, usuario_id: str, alcada: Optional[Decimal]) -> bool:
        """RF-15, RF-16. Devolve True quando o desconto fica Pendente de Alçada.

        `alcada` é a do perfil de quem informa (OPEN-50); None quer dizer sem limite. Um percentual igual ao
        vigente, já aprovado, não gera nova pendência.
        """
        self._exigir_rascunho("alterar o desconto")
        novo = _percentual(percentual)
        if novo == self.percentual_desconto:
            return False
        if alcada is None or novo <= alcada:
            self.percentual_desconto = novo
            return False
        self.pendencia = PendenciaDesconto(novo, usuario_id, alcada)
        self.estado = EstadoOrcamento.PENDENTE_DE_ALCADA
        return True

    def decidir_desconto(
        self, aprovar: bool, decidido_por: str, data: date, percentual_aprovado: object = None
    ) -> AprovacaoDesconto:
        """RF-17, UC-05. A2: o Dono pode aprovar um percentual menor que o solicitado. A1: rejeitar mantém o
        desconto anterior. Nos dois casos, o orçamento volta a Rascunho."""
        if self.estado is not EstadoOrcamento.PENDENTE_DE_ALCADA or self.pendencia is None:
            raise OperacaoRecusada(
                f"Este orçamento não tem desconto pendente de decisão: ele está {self.estado.value} (UC-05, E2)."
            )
        solicitado = self.pendencia.percentual_solicitado
        aprovado: Optional[Decimal] = None
        if aprovar:
            aprovado = solicitado if percentual_aprovado in (None, "") else _percentual(percentual_aprovado)
            if aprovado > solicitado:
                _recusar("percentual", "O desconto aprovado não pode ser maior que o solicitado.")
            self.percentual_desconto = aprovado
        decisao = AprovacaoDesconto(aprovar, solicitado, aprovado, decidido_por, data)
        self.decisoes.append(decisao)
        self.pendencia = None
        self.estado = EstadoOrcamento.RASCUNHO
        return decisao

    # Envio (verificado aqui; o envio em si é da Spec 005)

    def motivo_para_nao_enviar(self) -> Optional[str]:
        """RB-24 e RB-15: só sai de Rascunho com ao menos um item e sem desconto pendente."""
        if self.estado is EstadoOrcamento.PENDENTE_DE_ALCADA:
            return "O desconto aguarda a decisão do Dono (RB-15)."
        if self.estado is not EstadoOrcamento.RASCUNHO:
            return f"Orçamento {self.estado.value} não é enviado."
        if not self.itens:
            return "Inclua ao menos um item antes de enviar o orçamento (RB-24)."
        return None

    def exigir_envio(self) -> None:
        motivo = self.motivo_para_nao_enviar()
        if motivo:
            raise OperacaoRecusada(motivo)

    # Cancelamento (RF-13)

    def cancelar(self, motivo: object) -> None:
        texto = motivo.strip() if isinstance(motivo, str) else ""
        if not texto:
            _recusar("motivo", "O motivo do cancelamento é obrigatório (RF-13).")
        if self.estado not in ESTADOS_QUE_ACEITAM_CANCELAMENTO:
            raise OperacaoRecusada(f"Orçamento {self.estado.value} não pode ser cancelado.")
        self.estado = EstadoOrcamento.CANCELADO
        self.pendencia = None
        self.motivo_cancelamento = texto

    # Apoio

    def _exigir_rascunho(self, acao: str) -> None:
        """RF-07: itens, condição e desconto só mudam em Rascunho."""
        if self.estado is not EstadoOrcamento.RASCUNHO:
            explicacao = " Aguarde a decisão do Dono sobre o desconto." if self.estado is EstadoOrcamento.PENDENTE_DE_ALCADA else ""
            raise OperacaoRecusada(f"Não é possível {acao}: o orçamento está {self.estado.value}.{explicacao}")

    def _posicao(self, item_id: str) -> int:
        for posicao, item in enumerate(self.itens):
            if item.id == item_id:
                return posicao
        raise OperacaoRecusada("Item não encontrado neste orçamento.")

    def _aplicar_itens(self, itens: List[ItemOrcamento]) -> None:
        """OPEN-24: o valor bruto também fica abaixo de 15 dígitos inteiros. Recusa sem alterar nada."""
        if sum((item.total for item in itens), ZERO) >= LIMITE_VALOR:
            _recusar("valor_unitario", "O valor do orçamento deve ter no máximo 15 dígitos inteiros.")
        self.itens = itens


def _item(item_id: str, descricao: object, quantidade: object, valor_unitario: object) -> ItemOrcamento:
    """Todos os campos inválidos de uma vez (RNF-14)."""
    campos: Dict[str, str] = {}
    texto = " ".join(descricao.split()) if isinstance(descricao, str) else ""
    if not texto:
        campos["descricao"] = "Descreva o produto ou serviço."
    elif len(texto) > TAMANHO_MAXIMO_TEXTO:
        campos["descricao"] = f"A descrição tem no máximo {TAMANHO_MAXIMO_TEXTO} caracteres."
    if not _decimal(quantidade):
        campos["quantidade"] = "Informe a quantidade."
    elif quantidade <= 0:
        campos["quantidade"] = "A quantidade deve ser maior que zero."
    elif quantidade != quantidade.quantize(CENTAVO) or quantidade >= LIMITE_VALOR:
        campos["quantidade"] = "A quantidade tem no máximo duas casas decimais."
    if not _decimal(valor_unitario):
        campos["valor_unitario"] = "Informe o valor unitário."
    elif valor_unitario <= 0:
        campos["valor_unitario"] = "O valor unitário deve ser maior que zero."
    elif valor_unitario != valor_unitario.quantize(CENTAVO):
        campos["valor_unitario"] = "O valor unitário tem no máximo duas casas decimais."
    elif valor_unitario >= LIMITE_VALOR:
        campos["valor_unitario"] = "O valor unitário deve ter no máximo 15 dígitos inteiros."
    if campos:
        raise OperacaoRecusada(" ".join(campos.values()), campos)
    return ItemOrcamento(item_id, texto, quantidade, valor_unitario)


def _percentual(percentual: object) -> Decimal:
    """OPEN-51: de 0 a 100, com até duas casas decimais."""
    if not _decimal(percentual):
        _recusar("percentual", "Informe o desconto em percentual, por exemplo 5 ou 7,5.")
    if percentual < 0 or percentual > CEM:
        _recusar("percentual", "O desconto deve estar entre 0% e 100%.")
    if percentual != percentual.quantize(CENTAVO):
        _recusar("percentual", "O desconto tem no máximo duas casas decimais.")
    return percentual.quantize(CENTAVO)


def _condicao(condicao: object) -> Optional[str]:
    texto = " ".join(condicao.split()) if isinstance(condicao, str) else ""
    if len(texto) > TAMANHO_MAXIMO_TEXTO:
        _recusar("condicao", f"A condição de pagamento tem no máximo {TAMANHO_MAXIMO_TEXTO} caracteres.")
    return texto or None


def _decimal(numero: object) -> bool:
    """NaN, infinito, float e texto não são número (como nos defeitos D-01 a D-04 do título)."""
    return isinstance(numero, Decimal) and numero.is_finite()


def _ao_centavo(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _recusar(campo: str, mensagem: str) -> None:
    raise OperacaoRecusada(mensagem, {campo: mensagem})
