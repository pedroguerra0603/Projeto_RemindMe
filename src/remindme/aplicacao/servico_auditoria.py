"""Caso de uso da Spec 013: consulta de auditoria (UC-12, RF-64). Não há alteração nem exclusão (RB-30)."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local, horario_local
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao

# Valor do filtro de responsável que seleciona as operações automáticas (A2).
RESPONSAVEL_SISTEMA = "sistema"


@dataclass(frozen=True)
class FiltroAuditoria:
    """RF-64. `registro` seleciona o histórico de um registro (A1): "titulo <id>" inclui os pagamentos dele."""

    usuario_id: Optional[str] = None
    inicio: Optional[date] = None
    fim: Optional[date] = None
    operacao: Optional[str] = None
    registro: Optional[str] = None


@dataclass(frozen=True)
class VisaoRegistro:
    data_hora: datetime
    responsavel: str
    usuario_id: Optional[str]
    automatica: bool
    operacao: str
    registro_afetado: str
    campo: Optional[str]
    valor_anterior: Optional[str]
    valor_novo: Optional[str]
    motivo: Optional[str]


@dataclass(frozen=True)
class OpcoesDeFiltro:
    """A3: os responsáveis (identificador e nome) e os tipos de operação presentes na auditoria."""

    responsaveis: Dict[str, str]
    operacoes: List[str]


class ServicoAuditoria:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    def consultar(self, sessao: Optional[str], filtro: FiltroAuditoria) -> List[VisaoRegistro]:
        """Ordem cronológica, que é a ordem de gravação (INV-1). E3: período invertido é recusado."""
        with self._execucao.operacao("consultar auditoria", sessao, Operacao.CONSULTAR_AUDITORIA) as op:
            if filtro.inicio and filtro.fim and filtro.inicio > filtro.fim:
                motivo = "O fim do período não pode ser anterior ao início."
                raise OperacaoRecusada(motivo, {"fim": motivo})
            registros = op.uow.auditoria.listar()
            nomes = {u.id: u.nome for u in op.uow.usuarios.listar()}
        return [_visao(r, nomes) for r in registros if _atende(r, filtro)]

    def opcoes_de_filtro(self, sessao: Optional[str]) -> OpcoesDeFiltro:
        with self._execucao.operacao("consultar auditoria", sessao, Operacao.CONSULTAR_AUDITORIA) as op:
            registros = op.uow.auditoria.listar()
            nomes = {u.id: u.nome for u in op.uow.usuarios.listar()}
        responsaveis = {r.usuario_id: nomes.get(r.usuario_id, r.usuario_id) for r in registros if r.usuario_id}
        if any(r.automatica for r in registros):
            responsaveis[RESPONSAVEL_SISTEMA] = "Sistema (operação automática)"
        return OpcoesDeFiltro(
            dict(sorted(responsaveis.items(), key=lambda par: par[1].casefold())),
            sorted({r.operacao for r in registros}),
        )


def _atende(registro: RegistroAuditoria, filtro: FiltroAuditoria) -> bool:
    if filtro.usuario_id == RESPONSAVEL_SISTEMA:
        if not registro.automatica:
            return False
    elif filtro.usuario_id and registro.usuario_id != filtro.usuario_id:
        return False
    dia = data_local(registro.data_hora)
    if filtro.inicio and dia < filtro.inicio:
        return False
    if filtro.fim and dia > filtro.fim:
        return False
    if filtro.operacao and registro.operacao != filtro.operacao:
        return False
    if filtro.registro and not (
        registro.registro_afetado == filtro.registro or registro.registro_afetado.startswith(filtro.registro + ", ")
    ):
        return False
    return True


def _visao(registro: RegistroAuditoria, nomes: Dict[str, str]) -> VisaoRegistro:
    if registro.automatica:
        responsavel = f"Sistema ({registro.rotina})"
    else:
        responsavel = nomes.get(registro.usuario_id, registro.usuario_id)
    return VisaoRegistro(
        data_hora=horario_local(registro.data_hora),
        responsavel=responsavel,
        usuario_id=registro.usuario_id,
        automatica=registro.automatica,
        operacao=registro.operacao,
        registro_afetado=registro.registro_afetado,
        campo=registro.campo,
        valor_anterior=registro.valor_anterior,
        valor_novo=registro.valor_novo,
        motivo=registro.motivo,
    )
