"""Casos de uso da Spec 006: cadastro manual, pagamento, vencimento, estorno, cancelamento e consulta.

Cada operação que altera dados passa por `OperacaoAuditada` (Spec 001).
"""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.auditoria import Alteracao, Auditar, OperacaoAuditada
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


ROTINA_VERIFICACAO_DE_VENCIMENTO = "verificação de vencimento"


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
        self._operacao = OperacaoAuditada(uow, relogio, erros)

    def cadastrar_titulo(
        self,
        usuario: Usuario,
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> Titulo:
        def acao(uow: UnidadeDeTrabalho, auditar: Auditar) -> Titulo:
            if not self._clientes.existe(cliente_id):
                raise OperacaoRecusada("Cliente inexistente.")
            titulo = Titulo.cadastrar_manual(
                _novo_id(), cliente_id, valor, vencimento, condicao_pagamento
            )
            uow.titulos.salvar(titulo)
            auditar(Alteracao(_registro(titulo), "estado", None, titulo.estado.value))
            return titulo

        return self._operacao.executar(usuario, "cadastrar título", acao)

    def registrar_pagamento(
        self, usuario: Usuario, titulo_id: str, valor: Decimal, data: date
    ) -> Titulo:
        def acao(uow: UnidadeDeTrabalho, auditar: Auditar) -> Titulo:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            pagamento = titulo.registrar_pagamento(_novo_id(), valor, data)
            uow.titulos.salvar(titulo)
            # Spec 006, CA-22: o registro do pagamento tem o título como registro afetado.
            auditar(
                Alteracao(_registro(titulo), "pagamento", None, f"pagamento {pagamento.id}: {valor}")
            )
            _auditar_estado(auditar, titulo, estado_anterior)
            return titulo

        return self._operacao.executar(usuario, "registrar pagamento", acao)

    def verificar_vencimentos(self, usuario: Optional[Usuario], data_referencia: date) -> List[str]:
        """A3 da Spec 006. Sem usuário, é operação automática (Spec 001, A4). O disparo periódico é da Spec 008."""

        def acao(uow: UnidadeDeTrabalho, auditar: Auditar) -> List[str]:
            vencidos = []
            for titulo in uow.titulos.listar():
                if titulo.marcar_vencido(data_referencia):
                    uow.titulos.salvar(titulo)
                    _auditar_estado(auditar, titulo, EstadoTitulo.ABERTO)
                    vencidos.append(titulo.id)
            return vencidos

        return self._operacao.executar(
            usuario, "verificar vencimentos", acao, rotina=ROTINA_VERIFICACAO_DE_VENCIMENTO
        )

    def estornar_pagamento(
        self,
        usuario: Usuario,
        titulo_id: str,
        pagamento_id: str,
        motivo: Optional[str],
        data_referencia: date,
    ) -> Titulo:
        def acao(uow: UnidadeDeTrabalho, auditar: Auditar) -> Titulo:
            regras.exigir_permissao_de_estorno(usuario)
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            pagamento = titulo.estornar_pagamento(pagamento_id, motivo, data_referencia)
            uow.titulos.salvar(titulo)
            # Spec 001, A5 e CA-03: o pagamento é o registro afetado do estorno.
            auditar(Alteracao(f"pagamento {pagamento.id}", "estornado", "não", "sim", motivo))
            _auditar_estado(auditar, titulo, estado_anterior, motivo)
            return titulo

        return self._operacao.executar(usuario, "estornar pagamento", acao)

    def cancelar_titulo(self, usuario: Usuario, titulo_id: str, motivo: Optional[str]) -> Titulo:
        def acao(uow: UnidadeDeTrabalho, auditar: Auditar) -> Titulo:
            regras.exigir_permissao_de_cancelamento(usuario)
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.cancelar(motivo)
            uow.titulos.salvar(titulo)
            _auditar_estado(auditar, titulo, estado_anterior, motivo)
            return titulo

        return self._operacao.executar(usuario, "cancelar título", acao)

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


def _registro(titulo: Titulo) -> str:
    return f"titulo {titulo.id}"


def _auditar_estado(
    auditar: Auditar, titulo: Titulo, anterior: EstadoTitulo, motivo: Optional[str] = None
) -> None:
    """A2: a mudança de estado é auditada com o campo estado."""
    if titulo.estado is not anterior:
        auditar(
            Alteracao(
                _registro(titulo), "estado", anterior.value, titulo.estado.value, motivo,
                operacao="mudar estado",
            )
        )


def _atende(titulo: Titulo, filtro: FiltroTitulos) -> bool:
    return (
        (filtro.cliente_id is None or titulo.cliente_id == filtro.cliente_id)
        and (filtro.estado is None or titulo.estado is filtro.estado)
        and (filtro.vencimento_de is None or titulo.vencimento >= filtro.vencimento_de)
        and (filtro.vencimento_ate is None or titulo.vencimento <= filtro.vencimento_ate)
    )


def _novo_id() -> str:
    return uuid.uuid4().hex
