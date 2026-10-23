"""Casos de uso da Spec 006: cadastro manual, pagamento, vencimento, estorno, cancelamento e consulta."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.auditoria import Auditoria, OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.portas import ConsultaClientes, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio import regras
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo, Titulo
from remindme.dominio.usuario import Usuario


@dataclass(frozen=True)
class FiltroTitulos:
    """RF-22. O período filtra pelo vencimento (OPEN-19)."""

    cliente_id: Optional[str] = None
    estado: Optional[EstadoTitulo] = None
    vencimento_de: Optional[date] = None
    vencimento_ate: Optional[date] = None


@dataclass(frozen=True)
class VisaoTitulo:
    """A6: o que a consulta apresenta de cada título."""

    id: str
    cliente_id: str
    valor: Decimal
    saldo: Decimal
    vencimento: date
    estado: EstadoTitulo
    proximo_do_vencimento: bool


class ServicoTitulos:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        clientes: ConsultaClientes,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
    ):
        self._uow = uow
        self._clientes = clientes
        self._auditoria = Auditoria(uow, relogio, erros or RegistroErrosNoLog())

    def cadastrar_titulo(
        self,
        usuario: Usuario,
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> Titulo:
        with self._auditoria.operacao("cadastrar título", usuario) as op:
            if not self._clientes.existe(cliente_id):
                raise OperacaoRecusada("Cliente inexistente.")
            titulo = Titulo.cadastrar_manual(
                _novo_id(), cliente_id, valor, vencimento, condicao_pagamento
            )
            op.registrar(_ref(titulo), "estado", None, titulo.estado.value)
            op.uow.titulos.salvar(titulo)
        return titulo

    def registrar_pagamento(
        self, usuario: Usuario, titulo_id: str, valor: Decimal, data: date
    ) -> Titulo:
        with self._auditoria.operacao("registrar pagamento", usuario) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            pagamento = titulo.registrar_pagamento(_novo_id(), valor, data)
            op.registrar(_ref(titulo, pagamento.id), "valor", None, str(valor))
            _auditar_estado(op, titulo, estado_anterior)
            op.uow.titulos.salvar(titulo)
        return titulo

    def verificar_vencimentos(self, usuario: Optional[Usuario], data_referencia: date) -> List[str]:
        """A3. Sem usuário, é a rotina automática (Spec 001, A4). O disparo periódico é da Spec 008."""
        vencidos = []
        with self._auditoria.operacao(
            "verificar vencimentos", usuario, rotina="verificação de vencimento"
        ) as op:
            for titulo in op.uow.titulos.listar():
                if titulo.marcar_vencido(data_referencia):
                    _auditar_estado(op, titulo, EstadoTitulo.ABERTO)
                    op.uow.titulos.salvar(titulo)
                    vencidos.append(titulo.id)
        return vencidos

    def estornar_pagamento(
        self,
        usuario: Usuario,
        titulo_id: str,
        pagamento_id: str,
        motivo: Optional[str],
        data_referencia: date,
    ) -> Titulo:
        regras.exigir_permissao_de_estorno(usuario)
        with self._auditoria.operacao("estornar pagamento", usuario) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.estornar_pagamento(pagamento_id, motivo, data_referencia)
            op.registrar(_ref(titulo, pagamento_id), "estornado", "não", "sim", motivo)
            _auditar_estado(op, titulo, estado_anterior, motivo)
            op.uow.titulos.salvar(titulo)
        return titulo

    def cancelar_titulo(self, usuario: Usuario, titulo_id: str, motivo: Optional[str]) -> Titulo:
        regras.exigir_permissao_de_cancelamento(usuario)
        with self._auditoria.operacao("cancelar título", usuario) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.cancelar(motivo)
            _auditar_estado(op, titulo, estado_anterior, motivo)
            op.uow.titulos.salvar(titulo)
        return titulo

    def consultar_titulos(
        self, filtro: FiltroTitulos, data_referencia: date, antecedencia_dias: int
    ) -> List[VisaoTitulo]:
        """A6. A antecedência vem da configuração (Spec 014)."""
        with self._uow as uow:
            titulos = uow.titulos.listar()
        return [
            VisaoTitulo(
                id=t.id,
                cliente_id=t.cliente_id,
                valor=t.valor,
                saldo=t.saldo,
                vencimento=t.vencimento,
                estado=t.estado,
                proximo_do_vencimento=t.proximo_do_vencimento(data_referencia, antecedencia_dias),
            )
            for t in titulos
            if _atende(t, filtro)
        ]

    def _obter(self, titulo_id: str) -> Titulo:
        titulo = self._uow.titulos.obter(titulo_id)
        if titulo is None:
            raise OperacaoRecusada("Título não encontrado.")
        return titulo


def _atende(titulo: Titulo, filtro: FiltroTitulos) -> bool:
    return (
        (filtro.cliente_id is None or titulo.cliente_id == filtro.cliente_id)
        and (filtro.estado is None or titulo.estado is filtro.estado)
        and (filtro.vencimento_de is None or titulo.vencimento >= filtro.vencimento_de)
        and (filtro.vencimento_ate is None or titulo.vencimento <= filtro.vencimento_ate)
    )


def _auditar_estado(
    op: OperacaoAuditada, titulo: Titulo, anterior: EstadoTitulo, motivo: Optional[str] = None
) -> None:
    if titulo.estado is not anterior:
        op.registrar(
            _ref(titulo), "estado", anterior.value, titulo.estado.value, motivo, operacao="mudar estado"
        )


def _ref(titulo: Titulo, pagamento_id: Optional[str] = None) -> str:
    """O pagamento existe dentro do título, e a referência nomeia os dois (Spec 006, CA-22)."""
    if pagamento_id is None:
        return f"titulo {titulo.id}"
    return f"titulo {titulo.id}, pagamento {pagamento_id}"


def _novo_id() -> str:
    return uuid.uuid4().hex
