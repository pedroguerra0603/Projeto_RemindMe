"""Casos de uso da Spec 006: cadastro manual, pagamento, vencimento, estorno, cancelamento e consulta."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.portas import ConsultaClientes, Relogio, UnidadeDeTrabalho
from remindme.dominio import regras
from remindme.dominio.auditoria import RegistroAuditoria
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
    def __init__(self, uow: UnidadeDeTrabalho, clientes: ConsultaClientes, relogio: Relogio):
        self._uow = uow
        self._clientes = clientes
        self._relogio = relogio

    def cadastrar_titulo(
        self,
        usuario: Usuario,
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> Titulo:
        if not self._clientes.existe(cliente_id):
            raise OperacaoRecusada("Cliente inexistente.")
        titulo = Titulo.cadastrar_manual(
            _novo_id(), cliente_id, valor, vencimento, condicao_pagamento
        )
        with self._uow as uow:
            uow.titulos.salvar(titulo)
            self._auditar(usuario, "cadastrar título", titulo, None, titulo.estado.value)
        return titulo

    def registrar_pagamento(
        self, usuario: Usuario, titulo_id: str, valor: Decimal, data: date
    ) -> Titulo:
        with self._uow as uow:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            pagamento = titulo.registrar_pagamento(_novo_id(), valor, data)
            uow.titulos.salvar(titulo)
            self._auditar(
                usuario, "registrar pagamento", titulo, None, f"pagamento {pagamento.id}: {valor}"
            )
            self._auditar_estado(usuario, titulo, estado_anterior)
        return titulo

    def verificar_vencimentos(self, usuario: Usuario, data_referencia: date) -> List[str]:
        """A3. O disparo periódico é da Spec 008."""
        vencidos = []
        with self._uow as uow:
            for titulo in uow.titulos.listar():
                if titulo.marcar_vencido(data_referencia):
                    uow.titulos.salvar(titulo)
                    self._auditar_estado(usuario, titulo, EstadoTitulo.ABERTO)
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
        with self._uow as uow:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.estornar_pagamento(pagamento_id, motivo, data_referencia)
            uow.titulos.salvar(titulo)
            self._auditar(
                usuario, "estornar pagamento", titulo, f"pagamento {pagamento_id}", "estornado", motivo
            )
            self._auditar_estado(usuario, titulo, estado_anterior, motivo)
        return titulo

    def cancelar_titulo(self, usuario: Usuario, titulo_id: str, motivo: Optional[str]) -> Titulo:
        regras.exigir_permissao_de_cancelamento(usuario)
        with self._uow as uow:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.cancelar(motivo)
            uow.titulos.salvar(titulo)
            self._auditar_estado(usuario, titulo, estado_anterior, motivo)
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

    def _auditar_estado(
        self, usuario: Usuario, titulo: Titulo, anterior: EstadoTitulo, motivo: Optional[str] = None
    ) -> None:
        if titulo.estado is not anterior:
            self._auditar(
                usuario, "mudar estado", titulo, anterior.value, titulo.estado.value, motivo
            )

    def _auditar(
        self,
        usuario: Usuario,
        operacao: str,
        titulo: Titulo,
        valor_anterior: Optional[str],
        valor_novo: Optional[str],
        motivo: Optional[str] = None,
    ) -> None:
        self._uow.auditoria.registrar(
            RegistroAuditoria(
                usuario_id=usuario.id,
                data_hora=self._relogio.agora(),
                operacao=operacao,
                registro_afetado=f"titulo {titulo.id}",
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                motivo=motivo,
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
