"""Casos de uso da Spec 004: orçamento, itens, desconto e decisão do Dono (UC-04, passos 1 a 4; UC-05).

O envio, a decisão do cliente e a conversão em título são da Spec 005.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento, ItemOrcamento, Orcamento, alcada_do_perfil


@dataclass(frozen=True)
class FiltroOrcamentos:
    """RF-10. O período filtra pela data de criação (OPEN-52)."""

    cliente_id: Optional[str] = None
    estado: Optional[EstadoOrcamento] = None
    criado_de: Optional[date] = None
    criado_ate: Optional[date] = None


class ServicoOrcamentos:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._relogio = relogio
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    # Orçamento

    def criar_orcamento(self, sessao: Optional[str], cliente_id: object, condicao_pagamento: object = None) -> Orcamento:
        """RF-06: para um cliente cadastrado, em Rascunho."""
        with self._execucao.operacao("criar orçamento", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            if not isinstance(cliente_id, str) or not op.uow.clientes.existe(cliente_id):
                raise OperacaoRecusada("Cliente inexistente.", {"cliente": "Escolha um cliente cadastrado."})
            orcamento = Orcamento.criar(
                _novo_id(), cliente_id, op.usuario.id, data_local(self._relogio.agora()), condicao_pagamento
            )
            op.uow.orcamentos.salvar(orcamento)
            op.registrar(_ref(orcamento), "estado", None, orcamento.estado.value)
        return orcamento

    def alterar_condicao(self, sessao: Optional[str], orcamento_id: str, condicao_pagamento: object) -> Orcamento:
        with self._execucao.operacao("alterar orçamento", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            anterior = orcamento.condicao_pagamento
            orcamento.alterar_condicao(condicao_pagamento)
            if anterior != orcamento.condicao_pagamento:
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(_ref(orcamento), "condição de pagamento", anterior, orcamento.condicao_pagamento)
        return orcamento

    def cancelar_orcamento(self, sessao: Optional[str], orcamento_id: str, motivo: object) -> Orcamento:
        """RF-13: com motivo, antes da conversão."""
        with self._execucao.operacao("cancelar orçamento", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            anterior = orcamento.estado
            orcamento.cancelar(motivo)
            op.uow.orcamentos.salvar(orcamento)
            op.registrar(
                _ref(orcamento), "estado", anterior.value, orcamento.estado.value,
                orcamento.motivo_cancelamento, operacao="mudar estado",
            )
        return orcamento

    # Itens (RF-07, RF-18)

    def incluir_item(
        self, sessao: Optional[str], orcamento_id: str, descricao: object, quantidade: object, valor_unitario: object
    ) -> Orcamento:
        with self._execucao.operacao("incluir item", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            valor_anterior = orcamento.valor_liquido
            item = orcamento.incluir_item(_novo_id(), descricao, quantidade, valor_unitario)
            op.uow.orcamentos.salvar(orcamento)
            op.registrar(_ref(orcamento, item.id), "item", None, _descrever(item))
            _registrar_valor(op, orcamento, valor_anterior)
        return orcamento

    def alterar_item(
        self,
        sessao: Optional[str],
        orcamento_id: str,
        item_id: str,
        descricao: object,
        quantidade: object,
        valor_unitario: object,
    ) -> Orcamento:
        with self._execucao.operacao("alterar item", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            valor_anterior = orcamento.valor_liquido
            antes = orcamento.item(item_id)
            depois = orcamento.alterar_item(item_id, descricao, quantidade, valor_unitario)
            if antes != depois:
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(_ref(orcamento, item_id), "item", _descrever(antes), _descrever(depois))
                _registrar_valor(op, orcamento, valor_anterior)
        return orcamento

    def remover_item(self, sessao: Optional[str], orcamento_id: str, item_id: str) -> Orcamento:
        with self._execucao.operacao("remover item", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            valor_anterior = orcamento.valor_liquido
            item = orcamento.remover_item(item_id)
            op.uow.orcamentos.salvar(orcamento)
            op.registrar(_ref(orcamento, item.id), "item", _descrever(item), None)
            _registrar_valor(op, orcamento, valor_anterior)
        return orcamento

    # Desconto (RF-15 a RF-18, RB-15)

    def informar_desconto(self, sessao: Optional[str], orcamento_id: str, percentual: object) -> Orcamento:
        """RF-15: compara com a alçada do perfil de quem informa (OPEN-50). RF-16: acima dela, Pendente de Alçada."""
        with self._execucao.operacao("informar desconto", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            anterior = orcamento.percentual_desconto
            valor_anterior = orcamento.valor_liquido
            pendente = orcamento.informar_desconto(percentual, op.usuario.id, alcada_do_perfil(op.usuario.perfil))
            if pendente:
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(_ref(orcamento), "desconto solicitado", None, str(orcamento.pendencia.percentual_solicitado))
                op.registrar(
                    _ref(orcamento), "estado", EstadoOrcamento.RASCUNHO.value, orcamento.estado.value,
                    f"Desconto acima da alçada de {_percentual(orcamento.pendencia.alcada)} (RB-15).", operacao="mudar estado",
                )
            elif anterior != orcamento.percentual_desconto:
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(_ref(orcamento), "desconto", str(anterior), str(orcamento.percentual_desconto))
                _registrar_valor(op, orcamento, valor_anterior)
        return orcamento

    def decidir_desconto(
        self, sessao: Optional[str], orcamento_id: str, aprovar: bool, percentual_aprovado: object = None
    ) -> Orcamento:
        """UC-05. Só o Dono (RB-15, permissão fixada). RF-17: responsável, decisão e data ficam registrados."""
        with self._execucao.operacao("decidir desconto", sessao, Operacao.APROVAR_DESCONTO) as op:
            orcamento = _obter(op, orcamento_id)
            anterior = orcamento.percentual_desconto
            valor_anterior = orcamento.valor_liquido
            decisao = orcamento.decidir_desconto(
                bool(aprovar), op.usuario.id, data_local(self._relogio.agora()), percentual_aprovado
            )
            op.uow.orcamentos.salvar(orcamento)
            texto = "rejeitado"
            if decisao.aprovado:
                texto = f"aprovado {decisao.percentual_aprovado}% de {decisao.percentual_solicitado}% solicitados"
            op.registrar(_ref(orcamento), "decisão do desconto", None, texto)
            if anterior != orcamento.percentual_desconto:
                op.registrar(_ref(orcamento), "desconto", str(anterior), str(orcamento.percentual_desconto))
                _registrar_valor(op, orcamento, valor_anterior)
            op.registrar(
                _ref(orcamento), "estado", EstadoOrcamento.PENDENTE_DE_ALCADA.value, orcamento.estado.value,
                operacao="mudar estado",
            )
        return orcamento

    # Consulta (RF-10)

    def consultar_orcamentos(self, sessao: Optional[str], filtro: FiltroOrcamentos = FiltroOrcamentos()) -> List[Orcamento]:
        with self._execucao.operacao("consultar orçamentos", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamentos = op.uow.orcamentos.listar()
        return sorted(
            (o for o in orcamentos if _atende(o, filtro)), key=lambda o: (o.criado_em, o.id), reverse=True
        )

    def obter_orcamento(self, sessao: Optional[str], orcamento_id: str) -> Orcamento:
        with self._execucao.operacao("consultar orçamentos", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            return _obter(op, orcamento_id)

    def pendentes_de_decisao(self, sessao: Optional[str]) -> List[Orcamento]:
        """O que o Dono tem a decidir (UC-05, gatilho)."""
        with self._execucao.operacao("consultar orçamentos", sessao, Operacao.APROVAR_DESCONTO) as op:
            orcamentos = op.uow.orcamentos.listar()
        return [o for o in orcamentos if o.estado is EstadoOrcamento.PENDENTE_DE_ALCADA]


def _obter(op: OperacaoAuditada, orcamento_id: str) -> Orcamento:
    orcamento = op.uow.orcamentos.obter(orcamento_id) if isinstance(orcamento_id, str) else None
    if orcamento is None:
        raise OperacaoRecusada("Orçamento não encontrado.")
    return orcamento


def _atende(o: Orcamento, filtro: FiltroOrcamentos) -> bool:
    return (
        (filtro.cliente_id is None or o.cliente_id == filtro.cliente_id)
        and (filtro.estado is None or o.estado is filtro.estado)
        and (filtro.criado_de is None or o.criado_em >= filtro.criado_de)
        and (filtro.criado_ate is None or o.criado_em <= filtro.criado_ate)
    )


def _registrar_valor(op: OperacaoAuditada, orcamento: Orcamento, anterior: Decimal) -> None:
    """RF-18: valor anterior e novo do orçamento, quando ele muda."""
    if anterior != orcamento.valor_liquido:
        op.registrar(_ref(orcamento), "valor", str(anterior), str(orcamento.valor_liquido))


def _percentual(valor: Decimal) -> str:
    texto = f"{valor:f}"
    return (texto.rstrip("0").rstrip(".") if "." in texto else texto) + "%"


def _descrever(item: ItemOrcamento) -> str:
    return f"{item.descricao}: {item.quantidade} × {item.valor_unitario}"


def _ref(orcamento: Orcamento, item_id: Optional[str] = None) -> str:
    if item_id is None:
        return f"orcamento {orcamento.id}"
    return f"orcamento {orcamento.id}, item {item_id}"


def _novo_id() -> str:
    return uuid.uuid4().hex
