"""Casos de uso das Specs 004 e 005: orçamento, itens, desconto e decisão do Dono (UC-04, passos 1 a 4; UC-05);
prazo, envio ao cliente, decisão do cliente e conversão em título (UC-04, passos 5 a 9)."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.modelos_de_mensagem import mensagem_de_orcamento
from remindme.aplicacao.portas import CanalNotificacao, Mensagem, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento, ItemOrcamento, Orcamento, alcada_do_perfil
from remindme.dominio.titulo import Titulo


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
        canal: Optional[CanalNotificacao] = None,
    ):
        self._relogio = relogio
        self._canal = canal  # injetado pela montagem (ADR-001, ADR-002)
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

    # Prazo, envio e decisão do cliente (Spec 005)

    def alterar_prazo(self, sessao: Optional[str], orcamento_id: str, dias: object) -> Orcamento:
        """OPEN-61: prazo para pagamento em dias, só em Rascunho."""
        with self._execucao.operacao("alterar orçamento", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            anterior = orcamento.prazo_pagamento_dias
            orcamento.alterar_prazo(dias)
            if anterior != orcamento.prazo_pagamento_dias:
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(
                    _ref(orcamento), "prazo para pagamento", _texto(anterior), _texto(orcamento.prazo_pagamento_dias)
                )
        return orcamento

    def enviar_orcamento(self, sessao: Optional[str], orcamento_id: str) -> Orcamento:
        """RF-08: o texto do modelo (RB-27) vai ao contato do cliente pelo canal. Toda tentativa fica na caixa de
        saída (ADR-002); se o canal falhar, o orçamento continua em Rascunho (E2)."""
        if self._canal is None:
            raise RuntimeError("Canal de notificação não configurado: a montagem do sistema deve fornecê-lo.")
        with self._execucao.operacao("enviar orçamento", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            orcamento = _obter(op, orcamento_id)
            orcamento.exigir_envio()
            cliente = op.uow.clientes.obter(orcamento.cliente_id)
            assunto, texto = mensagem_de_orcamento(op.uow.empresa.obter(), cliente, orcamento)
            try:
                entregue = bool(self._canal.entregar(cliente.contato, assunto, texto))
            except Exception:
                entregue = False
            op.uow.mensagens.registrar(
                Mensagem(
                    _novo_id(), cliente.id, cliente.contato, assunto, texto, self._relogio.agora(),
                    "enviada" if entregue else "falhou", _ref(orcamento),
                )
            )
            if entregue:
                orcamento.marcar_enviado(data_local(self._relogio.agora()))
                op.uow.orcamentos.salvar(orcamento)
                op.registrar(
                    _ref(orcamento), "estado", EstadoOrcamento.RASCUNHO.value, orcamento.estado.value,
                    operacao="mudar estado",
                )
        if not entregue:
            # Fora da transação: a tentativa que falhou já está gravada na caixa de saída.
            raise OperacaoRecusada(
                "O canal de notificação não entregou o orçamento. Ele continua em Rascunho; tente enviar de novo."
            )
        return orcamento

    def registrar_decisao_do_cliente(
        self, sessao: Optional[str], orcamento_id: str, aprovado: bool, data: object, motivo: object = None
    ) -> Orcamento:
        """RF-09 (OPEN-57): um usuário registra o que o cliente decidiu. Na aprovação, gera o título e converte o
        orçamento na mesma transação (RF-11, RF-19, RB-05, RNF-09)."""
        with self._execucao.operacao("registrar decisão do cliente", sessao, Operacao.CONDUZIR_ORCAMENTO) as op:
            hoje = data_local(self._relogio.agora())
            orcamento = _obter(op, orcamento_id)
            orcamento.registrar_decisao(bool(aprovado), data, hoje, motivo)
            op.registrar(
                _ref(orcamento), "estado", EstadoOrcamento.ENVIADO.value, orcamento.estado.value,
                orcamento.motivo_rejeicao, operacao="mudar estado",
            )
            if orcamento.estado is EstadoOrcamento.APROVADO:
                titulo = Titulo.gerar_de_orcamento(_novo_id(), orcamento)
                ref_titulo = f"titulo {titulo.id}"
                op.registrar(ref_titulo, "estado", None, titulo.estado.value, operacao="mudar estado")
                if titulo.marcar_vencido(hoje):  # RF-24: aprovação registrada com atraso (A2).
                    op.registrar(ref_titulo, "estado", "Aberto", titulo.estado.value, operacao="mudar estado")
                orcamento.converter(titulo.id)
                op.uow.titulos.salvar(titulo)
                op.registrar(
                    _ref(orcamento), "estado", EstadoOrcamento.APROVADO.value, orcamento.estado.value,
                    operacao="mudar estado",
                )
            op.uow.orcamentos.salvar(orcamento)
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


def _texto(dias: Optional[int]) -> Optional[str]:
    return None if dias is None else str(dias)


def _novo_id() -> str:
    return uuid.uuid4().hex
